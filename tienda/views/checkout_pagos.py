import json
import re
import threading
import mercadopago
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db import transaction

from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_api_keys import IntegrationApiKeys

from ..models import Producto, Pedido, ItemPedido, Cupon, LogProducto, LogPedido
from ..carrito import Carrito
from ..deseos import Deseos
from ..comunas_chile import (
    calcular_costo_envio,
    obtener_region_de_comuna,
    obtener_puntos_blue_por_comuna,
    REGIONES_Y_COMUNAS,
    UMBRAL_ENVIO_GRATIS,
    determinar_talla_peso
)
from ..utils import normalizar_telefono_chile


def enviar_correo_asincrono(asunto, mensaje, destinatario):
    """
    Envía correos electrónicos en un hilo secundario para evitar que 
    fallas o latencias en el servidor SMTP bloqueen al worker de Gunicorn.
    """
    if not getattr(settings, 'EMAIL_HOST_USER', None):
        return
    try:
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [destinatario],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Error asíncrono al enviar correo a {destinatario}: {e}")



def get_webpay_transaction():
    """
    Retorna una instancia de Transaction configurada para Producción o Integración (pruebas)
    según las credenciales en settings.
    """
    commerce_code = getattr(settings, 'TRANSBANK_COMMERCE_CODE', '') or ''
    api_key = getattr(settings, 'TRANSBANK_API_KEY', '') or ''
    env = getattr(settings, 'TRANSBANK_ENVIRONMENT', 'INTEGRATION').upper()

    if env == 'PRODUCTION' and commerce_code and api_key:
        return Transaction.build_for_production(commerce_code, api_key)
    else:
        code = commerce_code or IntegrationCommerceCodes.WEBPAY_PLUS
        key = api_key or IntegrationApiKeys.WEBPAY
        return Transaction.build_for_integration(code, key)


def descifrar_tipo_pago_webpay(codigo_tipo):
    """
    Convierte el código de tipo de pago de Transbank Webpay Plus a texto legible.
    """
    tipos = {
        'VD': 'Redcompra (Débito)',
        'VN': 'Tarjeta de Crédito (1 pago)',
        'VC': 'Crédito en Cuotas',
        'SI': '3 Cuotas sin Interés',
        'S2': '2 Cuotas sin Interés',
        'NC': 'Cuotas sin Interés',
        'VP': 'Tarjeta Prepago',
    }
    return tipos.get(codigo_tipo, codigo_tipo or 'Webpay Plus')



def toggle_deseos(request, producto_id):
    deseos = Deseos(request)
    producto = get_object_or_404(Producto, id=producto_id)
    agregado = deseos.toggle(producto)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        return JsonResponse({
            'success': True,
            'agregado': agregado,
            'total_deseos': len(deseos),
            'producto_id': producto_id,
            'nombre': producto.nombre,
        })
    
    if agregado:
        messages.success(request, f'¡{producto.nombre} agregado a tu Lista de Deseos!')
    else:
        messages.info(request, f'{producto.nombre} eliminado de tu Lista de Deseos.')

    url_anterior = request.META.get('HTTP_REFERER', '/')
    return redirect(url_anterior)


def ver_deseos(request):
    deseos = Deseos(request)
    return render(request, 'deseos.html', {'deseos': deseos})


def mover_deseos_a_carrito(request, producto_id):
    deseos = Deseos(request)
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'

    if producto.hay_stock():
        carrito.agregar(producto, 1)
        deseos.eliminar(producto)
        msg = f'¡{producto.nombre} movido al carrito de compras!'
        success = True
    else:
        msg = f'Lo sentimos, {producto.nombre} está agotado por ahora.'
        success = False

    if is_ajax:
        cart_html = render_to_string('includes/cart_drawer_content.html', {'carrito': carrito}, request=request)
        total_raw = carrito.get_total()
        return JsonResponse({
            'success': success,
            'message': msg,
            'message_type': 'success' if success else 'error',
            'total_items': len(carrito),
            'total_deseos': len(deseos),
            'total_precio': f"{total_raw:,}".replace(',', '.'),
            'total_raw': total_raw,
            'cart_html': cart_html,
        })

    if success:
        messages.success(request, msg)
    else:
        messages.error(request, msg)

    return _cart_redirect(request, '/deseos/')



def validar_rut_chileno(rut):
    rut_limpio = rut.replace(".", "").replace("-", "").replace(" ", "").upper()
    if not re.match(r'^\d{7,8}[0-9K]$', rut_limpio):
        return False
        
    cuerpo = rut_limpio[:-1]
    dv_ingresado = rut_limpio[-1]
    
    suma = 0
    multiplo = 2
    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo += 1
        if multiplo == 8:
            multiplo = 2
            
    resto = suma % 11
    dv_esperado = 11 - resto
    
    if dv_esperado == 11:
        dv_esperado = "0"
    elif dv_esperado == 10:
        dv_esperado = "K"
    else:
        dv_esperado = str(dv_esperado)
        
    return dv_ingresado == dv_esperado


def obtener_descuento_cupon(request, total_carrito):
    codigo = request.session.get('cupon_codigo')
    if not codigo:
        return None, 0
    try:
        cupon = Cupon.objects.get(codigo__iexact=codigo)
        valido, _ = cupon.es_valido()
        if valido:
            descuento = cupon.calcular_descuento(total_carrito)
            return cupon, descuento
    except Cupon.DoesNotExist:
        pass
    return None, 0


def aplicar_cupon(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().upper()
        if not codigo:
            messages.error(request, "Por favor ingresa un código de cupón.")
            return redirect('procesar_pedido')
        
        try:
            cupon = Cupon.objects.get(codigo__iexact=codigo)
            valido, msg = cupon.es_valido()
            if not valido:
                messages.error(request, msg)
            else:
                request.session['cupon_codigo'] = cupon.codigo
                messages.success(request, f"¡Cupón '{cupon.codigo}' aplicado exitosamente!")
        except Cupon.DoesNotExist:
            messages.error(request, "El código de cupón ingresado no existe.")
            
    return redirect('procesar_pedido')


def quitar_cupon(request):
    if 'cupon_codigo' in request.session:
        del request.session['cupon_codigo']
        messages.info(request, "Cupón removido.")
    return redirect('procesar_pedido')


def _cart_json_response(request, carrito, success=True, message=None, message_type='info'):
    cart_html = render_to_string('includes/cart_drawer_content.html', {'carrito': carrito}, request=request)
    total_raw = carrito.get_total()
    return JsonResponse({
        'success': success,
        'message': message,
        'message_type': message_type,
        'total_items': len(carrito),
        'total_precio': f"{total_raw:,}".replace(',', '.'),
        'total_raw': total_raw,
        'cart_html': cart_html,
    })


def _cart_redirect(request, default_url='/'):
    url_anterior = request.POST.get('next') or request.GET.get('next') or request.META.get('HTTP_REFERER') or default_url
    if 'cart=open' not in url_anterior:
        sep = '&' if '?' in url_anterior else '?'
        return redirect(url_anterior + sep + 'cart=open')
    return redirect(url_anterior)


def agregar_al_carrito(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'

    try:
        val = request.POST.get('cantidad') if request.method == 'POST' else request.GET.get('cantidad')
        cantidad = int(val) if val is not None else 1
        if cantidad <= 0:
            if is_ajax:
                return _cart_json_response(request, carrito, success=False, message="La cantidad debe ser un número positivo.", message_type='error')
            messages.error(request, "La cantidad debe ser un número positivo.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
    except ValueError:
        if is_ajax:
            return _cart_json_response(request, carrito, success=False, message="Cantidad no válida.", message_type='error')
        messages.error(request, "Cantidad no válida.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    if producto.hay_stock():
        agregado_exitosamente = carrito.agregar(producto, cantidad)
        if agregado_exitosamente:
            msg = f'¡{producto.nombre} agregado a tu carrito!'
            msg_type = 'success'
        else:
            msg = f'¡Límite alcanzado! Solo nos quedan {producto.stock} unidades de {producto.nombre} y ya están en tu carrito.'
            msg_type = 'warning'
    else:
        agregado_exitosamente = False
        msg = f'Lo sentimos, {producto.nombre} está agotado por ahora.'
        msg_type = 'error'

    if is_ajax:
        return _cart_json_response(request, carrito, success=agregado_exitosamente, message=msg, message_type=msg_type)

    if msg_type == 'success':
        messages.success(request, msg)
    elif msg_type == 'warning':
        messages.warning(request, msg)
    else:
        messages.error(request, msg)

    return _cart_redirect(request)


def ver_carrito(request):
    return _cart_redirect(request)


def restar_del_carrito(request, producto_id):
    carrito = Carrito(request)
    producto = Producto.objects.filter(id=producto_id).first()
    if producto:
        carrito.restar(producto)
    else:
        carrito.eliminar(producto_id)

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'
    if is_ajax:
        return _cart_json_response(request, carrito, success=True)

    return _cart_redirect(request)


def quitar_del_carrito(request, producto_id):
    carrito = Carrito(request)
    producto = Producto.objects.filter(id=producto_id).first()
    if producto:
        carrito.eliminar(producto)
    else:
        carrito.eliminar(producto_id)

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'
    if is_ajax:
        return _cart_json_response(request, carrito, success=True)

    return _cart_redirect(request)


def limpiar_carrito(request):
    carrito = Carrito(request)
    carrito.limpiar()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        return _cart_json_response(request, carrito, success=True)
    return _cart_redirect(request)


def procesar_pedido(request):
    carrito = Carrito(request)
    
    if len(carrito.carrito) == 0:
        messages.warning(request, "Tu carrito está vacío. ¡Agrega productos desde el catálogo!")
        return redirect('index')
    
    for item_data in carrito:
        producto = item_data.get('producto_real')
        cantidad_pedida = item_data['cantidad']
        
        if not producto:
            messages.error(request, "Un producto de tu carrito ya no está disponible.")
            return redirect('ver_carrito')
            
        if cantidad_pedida <= 0:
            messages.error(request, "Se detectó una cantidad inválida en tu carrito. Por favor, revisa tus productos.")
            return redirect('ver_carrito')
            
        if cantidad_pedida > producto.stock:
            messages.warning(request, f"¡Atención! Mientras pensabas, el stock de '{producto.nombre}' bajó a {producto.stock} unidades. Por favor ajusta tu carrito.")
            return redirect('ver_carrito')

def obtener_peso_total_carrito(carrito):
    """
    Calcula el peso total acumulado de los productos en el carrito.
    Si un producto no tiene peso definido, asume 0.40 kg (talla XS).
    """
    peso = 0.0
    for item in carrito:
        prod = item.get('producto_real')
        if prod and getattr(prod, 'peso', None):
            try:
                peso += float(prod.peso) * item.get('cantidad', 1)
            except (ValueError, TypeError):
                peso += 0.40 * item.get('cantidad', 1)
        else:
            peso += 0.40 * item.get('cantidad', 1)
    return max(0.40, peso)


def procesar_pedido(request):
    carrito = Carrito(request)
    
    if len(carrito) == 0:
        messages.info(request, "Tu carrito de compras está vacío. Agrega productos para continuar.")
        return redirect('ver_carrito')

    for item in carrito:
        producto = item['producto_real']
        cantidad_pedida = item['cantidad']
        if cantidad_pedida <= 0:
            messages.error(request, "Se detectó una cantidad inválida en tu carrito. Por favor, revisa tus productos.")
            return redirect('ver_carrito')
            
        if cantidad_pedida > producto.stock:
            messages.warning(request, f"¡Atención! Mientras pensabas, el stock de '{producto.nombre}' bajó a {producto.stock} unidades. Por favor ajusta tu carrito.")
            return redirect('ver_carrito')

    total_bruto = carrito.get_total()
    cupon_obj, descuento_aplicado = obtener_descuento_cupon(request, total_bruto)
    subtotal_descuento = max(0, total_bruto - descuento_aplicado)
    
    peso_carrito = obtener_peso_total_carrito(carrito)
    talla_carrito = determinar_talla_peso(peso_carrito)
    
    datos_previos = request.POST if request.method == 'POST' else {}
    comuna_previa = datos_previos.get('comuna') or datos_previos.get('ciudad') or 'Santiago'
    region_previa = datos_previos.get('region') or 'Región Metropolitana de Santiago'
    
    permite_gratis_rm_inicial = (region_previa == "Región Metropolitana de Santiago" and subtotal_descuento >= UMBRAL_ENVIO_GRATIS)
    tipo_entrega_default = datos_previos.get('tipo_entrega') or ('GRATIS_RM' if permite_gratis_rm_inicial else 'ENVIO')
    costo_envio_default = calcular_costo_envio(comuna_previa, subtotal_descuento, peso_carrito, tipo_entrega=tipo_entrega_default)
    total_final_default = subtotal_descuento + costo_envio_default

    def _build_checkout_context(extra_dict=None):
        ctx = {
            'carrito': carrito,
            'cupon': cupon_obj,
            'descuento': descuento_aplicado,
            'subtotal': total_bruto,
            'total_final': total_final_default,
            'costo_envio': costo_envio_default,
            'talla_envio': talla_carrito,
            'peso_total': round(peso_carrito, 2),
            'regiones_comunas': REGIONES_Y_COMUNAS,
            'regiones_comunas_json': json.dumps(REGIONES_Y_COMUNAS),
            'umbral_envio_gratis': UMBRAL_ENVIO_GRATIS,
            'permite_gratis_rm': permite_gratis_rm_inicial,
            'tipo_entrega_default': tipo_entrega_default,
            'datos_previos': datos_previos,
            'comuna_previa': comuna_previa,
            'region_previa': region_previa,
        }
        if extra_dict:
            ctx.update(extra_dict)
        return ctx

    if request.method == 'POST':
        rut_ingresado = request.POST.get('rut', '')
        terminos_aceptados = request.POST.get('terminos_aceptados')

        tipo_entrega = request.POST.get('tipo_entrega', 'ENVIO')
        direccion = request.POST.get('direccion', '').strip()
        region = request.POST.get('region', '').strip() or 'Región Metropolitana de Santiago'
        comuna = request.POST.get('comuna', '').strip() or request.POST.get('ciudad', '').strip() or 'Santiago'
        punto_entrega_id = request.POST.get('punto_entrega_id', '').strip()
        punto_entrega_nombre = request.POST.get('punto_entrega_nombre', '').strip()

        if tipo_entrega == 'RETIRO':
            costo_envio = 0
            if not direccion:
                direccion = "Retiro en Local - San Diego 174 local 8"
            comuna = "Santiago"
            region = "Región Metropolitana de Santiago"
        elif tipo_entrega == 'GRATIS_RM':
            if not direccion:
                direccion = "Dirección no especificada"
            costo_envio = calcular_costo_envio(comuna, subtotal_descuento, peso_carrito, tipo_entrega='GRATIS_RM')
        elif tipo_entrega == 'PUNTO_BLUE':
            costo_envio = calcular_costo_envio(comuna, subtotal_descuento, peso_carrito, tipo_entrega='PUNTO_BLUE')
            if not direccion and punto_entrega_nombre:
                direccion = f"Punto Blue Express: {punto_entrega_nombre}"
        else:
            if not direccion:
                direccion = "Dirección no especificada"
            costo_envio = calcular_costo_envio(comuna, subtotal_descuento, peso_carrito, tipo_entrega='ENVIO')

        total_final = max(0, subtotal_descuento + costo_envio)

        if not terminos_aceptados:
            return render(request, 'checkout.html', _build_checkout_context({
                'error_terminos': "Debes aceptar los Términos y Condiciones y Políticas de Devolución para realizar tu pedido.",
                'datos_previos': request.POST,
                'total_final': total_final,
                'costo_envio': costo_envio
            }))

        if not validar_rut_chileno(rut_ingresado):
            return render(request, 'checkout.html', _build_checkout_context({
                'error_rut': "El RUT ingresado no es válido. Por favor, revísalo y escríbelo correctamente.",
                'datos_previos': request.POST,
                'total_final': total_final,
                'costo_envio': costo_envio
            }))

        requiere_factura = bool(request.POST.get('requiere_factura'))
        razon_social = request.POST.get('razon_social', '').strip()
        rut_empresa = request.POST.get('rut_empresa', '').strip()
        giro_comercial = request.POST.get('giro_comercial', '').strip()

        if requiere_factura and rut_empresa:
            if not validar_rut_chileno(rut_empresa):
                return render(request, 'checkout.html', _build_checkout_context({
                    'error_rut': "El RUT de la Empresa ingresado para la factura no es válido.",
                    'datos_previos': request.POST,
                    'total_final': total_final,
                    'costo_envio': costo_envio
                }))

        pedido = Pedido.objects.create(
            nombre_completo=request.POST.get('nombre_completo'),
            rut=rut_ingresado,
            email=request.POST.get('email'),
            telefono=normalizar_telefono_chile(request.POST.get('telefono')),
            tipo_entrega=tipo_entrega,
            punto_entrega_id=punto_entrega_id,
            punto_entrega_nombre=punto_entrega_nombre,
            direccion=direccion,
            ciudad=comuna,
            region=region,
            comuna=comuna,
            costo_envio=costo_envio,
            empresa_transporte='Blue Express' if tipo_entrega in ('ENVIO', 'PUNTO_BLUE', 'GRATIS_RM') else '',
            cupon=cupon_obj,
            descuento_aplicado=descuento_aplicado,
            requiere_factura=requiere_factura,
            razon_social=razon_social,
            rut_empresa=rut_empresa,
            giro_comercial=giro_comercial,
            metodo_pago='WEBPAY'
        )
        
        if cupon_obj:
            cupon_obj.usos_actuales += 1
            cupon_obj.save()
            if 'cupon_codigo' in request.session:
                del request.session['cupon_codigo']

        request.session['pedido_autorizado'] = str(pedido.id)
        
        for item in carrito:
            ItemPedido.objects.create(
                pedido=pedido,
                producto=item['producto_real'],
                precio=item['precio'],
                cantidad=item['cantidad']
            )
            LogProducto.objects.create(
                producto_id=item['producto_real'].id,
                nombre_producto=item['producto_real'].nombre,
                accion='VENTA',
                detalles=f"Vendido {item['cantidad']} unidad(es) en Pedido #{pedido.codigo_orden} | Cliente: {pedido.nombre_completo} ({pedido.email})"
            )

        items_summary = ", ".join([f"{item['producto_real'].nombre} (x{item['cantidad']})" for item in carrito])
        detalles_creacion = f"Pedido iniciado por total ${total_final} (Subtotal: ${total_bruto}, Descuento: -${descuento_aplicado}, Envío Blue Express: ${costo_envio}) | Ítems: {items_summary} | Destino: {pedido.direccion}, {pedido.comuna}, {pedido.region} | RUT: {pedido.rut} | Teléfono: {pedido.telefono_display}"
        if cupon_obj:
            detalles_creacion += f" | Cupón: {cupon_obj.codigo} (-${descuento_aplicado})"

        LogPedido.objects.create(
            pedido_id=pedido.id,
            codigo_orden=pedido.codigo_orden,
            cliente_nombre=pedido.nombre_completo,
            cliente_email=pedido.email,
            accion='CREACION',
            detalles=detalles_creacion
        )

        if getattr(settings, 'EMAIL_HOST_USER', None):
            asunto_admin = f"NUEVO PEDIDO RAPIDASSURE #{pedido.codigo_orden} - {pedido.nombre_completo}"
            mensaje_admin = f"""¡Atención! Acaba de entrar un nuevo pedido.

Cliente: {pedido.nombre_completo}
Comuna/Región: {pedido.comuna}, {pedido.region}
Total: ${total_final} (Envío Blue Express: ${costo_envio})
Teléfono: {pedido.telefono_display}

Revisa el panel de administración para ver el detalle completo.
https://rapidassure.cl/panel/
"""
            threading.Thread(
                target=enviar_correo_asincrono,
                args=(asunto_admin, mensaje_admin, settings.EMAIL_HOST_USER),
                daemon=True
            ).start()

        # Iniciar transacción con Transbank Webpay Plus
        try:
            tx = get_webpay_transaction()
            buy_order = f"ORD-{pedido.codigo_orden}"
            session_id = f"PEDIDO-{pedido.id}"
            monto_transbank = max(1, int(total_final))

            return_url = request.build_absolute_uri('/webpay/retorno/')
            if not settings.DEBUG and return_url.startswith('http://'):
                return_url = return_url.replace('http://', 'https://', 1)

            tbk_response = tx.create(
                buy_order=buy_order,
                session_id=session_id,
                amount=monto_transbank,
                return_url=return_url
            )

            token_ws = tbk_response.get('token')
            url_tbk = tbk_response.get('url')

            if not token_ws or not url_tbk:
                raise ValueError(f"Respuesta sin token o url de Transbank: {tbk_response}")

            # Guardamos el token provisionalmente en el pedido
            pedido.id_transaccion = token_ws
            pedido.save(update_fields=['id_transaccion'])

            return render(request, 'webpay_redirect.html', {
                'url': url_tbk,
                'token': token_ws,
                'pedido': pedido
            })

        except Exception as e:
            LogPedido.objects.create(
                pedido_id=pedido.id,
                codigo_orden=pedido.codigo_orden,
                cliente_nombre=pedido.nombre_completo,
                cliente_email=pedido.email,
                accion='ERROR',
                detalles=f"Excepción al conectar con Webpay Plus: {e}"
            )
            print(f"Error al conectar con Webpay Plus: {e}")
            messages.error(request, f"Hubo un inconveniente al conectar con Transbank Webpay Plus: {e}. Por favor intenta nuevamente.")
            return redirect('ver_carrito')

    return render(request, 'checkout.html', _build_checkout_context())


def api_cotizar_envio(request):
    """
    Endpoint AJAX para cotizar el despacho Blue Express según comuna y tipo de entrega (ENVIO, PUNTO_BLUE, RETIRO).
    """
    carrito = Carrito(request)
    comuna = request.GET.get('comuna') or request.POST.get('comuna') or 'Santiago'
    comuna = comuna.strip()
    tipo_entrega = request.GET.get('tipo_entrega') or request.POST.get('tipo_entrega') or 'ENVIO'
    tipo_entrega = tipo_entrega.strip()

    total_bruto = carrito.get_total()
    cupon_obj, descuento_aplicado = obtener_descuento_cupon(request, total_bruto)
    subtotal_descuento = max(0, total_bruto - descuento_aplicado)

    peso_carrito = obtener_peso_total_carrito(carrito)
    talla_carrito = determinar_talla_peso(peso_carrito)
    region_comuna = obtener_region_de_comuna(comuna)
    permite_gratis_rm = (region_comuna == "Región Metropolitana de Santiago" and subtotal_descuento >= UMBRAL_ENVIO_GRATIS)

    costo_envio = calcular_costo_envio(comuna, subtotal_descuento, peso_carrito, tipo_entrega=tipo_entrega)
    total_final = subtotal_descuento + costo_envio

    return JsonResponse({
        'success': True,
        'comuna': comuna,
        'tipo_entrega': tipo_entrega,
        'region': region_comuna,
        'costo_envio': costo_envio,
        'costo_envio_formateado': f"${costo_envio:,}".replace(',', '.') if costo_envio > 0 else "GRATIS",
        'es_gratis': (costo_envio == 0),
        'permite_gratis_rm': permite_gratis_rm,
        'talla': talla_carrito,
        'peso_total': round(peso_carrito, 2),
        'subtotal': total_bruto,
        'descuento': descuento_aplicado,
        'total_final': total_final,
        'total_final_formateado': f"${total_final:,}".replace(',', '.'),
        'umbral_envio_gratis': UMBRAL_ENVIO_GRATIS
    })


def api_puntos_blue_express(request):
    """
    Endpoint AJAX para obtener los Puntos Blue Express habilitados para retiro en una comuna.
    """
    comuna = request.GET.get('comuna') or request.POST.get('comuna') or ''
    puntos = obtener_puntos_blue_por_comuna(comuna.strip())
    return JsonResponse({
        'success': True,
        'comuna': comuna.strip(),
        'total': len(puntos),
        'puntos': puntos
    })



@csrf_exempt
def webpay_retorno(request):
    """
    Vista receptora del retorno de Transbank Webpay Plus (POST o GET).
    Maneja aprobación, rechazo y anulación por el usuario (TBK_TOKEN).
    """
    token_ws = request.POST.get('token_ws') or request.GET.get('token_ws')
    tbk_token = request.POST.get('TBK_TOKEN') or request.GET.get('TBK_TOKEN')
    tbk_orden = request.POST.get('TBK_ORDEN_COMPRA') or request.GET.get('TBK_ORDEN_COMPRA')

    # Caso 1: El cliente anuló la compra en la pantalla de Transbank Webpay Plus
    if tbk_token and not token_ws:
        pedido = None
        if tbk_orden:
            try:
                cod_str = tbk_orden.replace('ORD-', '')
                pedido_id = int(cod_str) - 1100
                pedido = Pedido.objects.filter(id=pedido_id).first()
            except (ValueError, TypeError):
                pass

        if not pedido and tbk_token:
            pedido = Pedido.objects.filter(id_transaccion=tbk_token).first()

        if pedido:
            LogPedido.objects.create(
                pedido_id=pedido.id,
                codigo_orden=pedido.codigo_orden,
                cliente_nombre=pedido.nombre_completo,
                cliente_email=pedido.email,
                accion='CANCELADO',
                detalles="El cliente anuló voluntariamente el pago en el portal de Webpay Plus."
            )
        messages.info(request, "Has cancelado el proceso de pago en Webpay Plus. Tus productos continúan en tu carrito de compras.")
        return redirect('/?cart=open')

    # Caso 2: Falta de token
    if not token_ws:
        messages.error(request, "No se recibió el comprobante de transacción de Webpay Plus.")
        return redirect('/?cart=open')

    # Caso 3: Verificar si el pedido ya fue pagado previamente para no duplicar commit
    pedido = Pedido.objects.filter(id_transaccion=token_ws).first()
    if pedido and pedido.pagado:
        request.session['pedido_autorizado'] = str(pedido.id)
        carrito = Carrito(request)
        carrito.limpiar()
        return redirect(f"{reverse('pedido_confirmado', kwargs={'pedido_id': pedido.id})}?token={token_ws}")

    # Caso 4: Confirmación con commit(token_ws)
    tx = get_webpay_transaction()

    try:
        commit_res = tx.commit(token=token_ws)
    except Exception as e:
        print(f"Error al ejecutar commit en Webpay: {e}")
        if pedido:
            LogPedido.objects.create(
                pedido_id=pedido.id,
                codigo_orden=pedido.codigo_orden,
                cliente_nombre=pedido.nombre_completo,
                cliente_email=pedido.email,
                accion='ERROR',
                detalles=f"Error en commit Webpay Plus: {e}"
            )
        messages.error(request, f"Ocurrió un error al procesar la confirmación con Transbank: {e}")
        return redirect('/?cart=open')

    response_code = commit_res.get('response_code')
    status = commit_res.get('status')
    buy_order = commit_res.get('buy_order', '')
    session_id = commit_res.get('session_id', '')

    # Encontramos el pedido correspondiente si no se encontró antes por token
    if not pedido:
        if buy_order and buy_order.startswith('ORD-'):
            try:
                cod_str = buy_order.replace('ORD-', '')
                pedido_id = int(cod_str) - 1100
                pedido = Pedido.objects.filter(id=pedido_id).first()
            except (ValueError, TypeError):
                pass
        if not pedido and session_id and session_id.startswith('PEDIDO-'):
            try:
                p_id = int(session_id.replace('PEDIDO-', ''))
                pedido = Pedido.objects.filter(id=p_id).first()
            except (ValueError, TypeError):
                pass

    if not pedido:
        messages.error(request, "No se encontró el pedido asociado a la transacción de Webpay.")
        return redirect('index')

    card_detail = commit_res.get('card_detail', {})
    tarjeta_ultimos = card_detail.get('card_number', '') if isinstance(card_detail, dict) else ''
    tipo_pago = descifrar_tipo_pago_webpay(commit_res.get('payment_type_code'))
    auth_code = str(commit_res.get('authorization_code', ''))
    cuotas = int(commit_res.get('installments_number') or 0)

    # Verificamos si fue aprobada (response_code == 0 y status == 'AUTHORIZED')
    if response_code == 0 and status == 'AUTHORIZED':
        pago_procesado = False
        with transaction.atomic():
            pedido_lock = Pedido.objects.select_for_update().filter(id=pedido.id).first()
            if pedido_lock and not pedido_lock.pagado:
                pedido_lock.confirmar_pago()
                pedido_lock.metodo_pago = 'WEBPAY'
                pedido_lock.id_transaccion = token_ws
                pedido_lock.codigo_autorizacion = auth_code
                pedido_lock.tipo_pago = tipo_pago
                pedido_lock.tarjeta_ultimos_digitos = tarjeta_ultimos
                pedido_lock.cuotas = cuotas
                pedido_lock.save()
                pedido = pedido_lock
                pago_procesado = True

        if pago_procesado:
            LogPedido.objects.create(
                pedido_id=pedido.id,
                codigo_orden=pedido.codigo_orden,
                cliente_nombre=pedido.nombre_completo,
                cliente_email=pedido.email,
                accion='PAGO_OK',
                detalles=(
                    f"Pago APROBADO por Webpay Plus | "
                    f"Cód. Aut.: {auth_code} | "
                    f"Monto: ${int(commit_res.get('amount', 0))} | "
                    f"Tipo: {tipo_pago} | "
                    f"Tarjeta: **** **** **** {tarjeta_ultimos} | "
                    f"Cuotas: {cuotas}"
                )
            )

            # Limpiamos el carrito del usuario
            carrito = Carrito(request)
            carrito.limpiar()

            # Autorizamos la vista de pedido confirmado
            request.session['pedido_autorizado'] = str(pedido.id)

            # Enviamos el correo de confirmación de pago al cliente y alerta a contacto@rapidassure.cl
            from ..emails import enviar_alerta_compra_confirmada
            enviar_alerta_compra_confirmada(pedido, async_send=True)

            return redirect(f"{reverse('pedido_confirmado', kwargs={'pedido_id': pedido.id})}?token={token_ws}")
        else:
            request.session['pedido_autorizado'] = str(pedido.id)
            carrito = Carrito(request)
            carrito.limpiar()
            return redirect(f"{reverse('pedido_confirmado', kwargs={'pedido_id': pedido.id})}?token={token_ws}")

    else:
        # Transacción rechazada por el banco emisor o Webpay
        LogPedido.objects.create(
            pedido_id=pedido.id,
            codigo_orden=pedido.codigo_orden,
            cliente_nombre=pedido.nombre_completo,
            cliente_email=pedido.email,
            accion='RECHAZADO',
            detalles=f"Transacción rechazada por Webpay Plus | Response Code: {response_code} | Status: {status}"
        )
        messages.error(
            request, 
            "Tu pago fue rechazado por el banco emisor o Webpay. Por favor verifica tus fondos o intenta con otra tarjeta."
        )
        return redirect('/?cart=open')


    return render(request, 'checkout.html', {
        'carrito': carrito,
        'cupon': cupon_obj,
        'descuento': descuento_aplicado,
        'total_final': total_final
    })


def pedido_confirmado(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    token_url = request.GET.get('token')
    pedido_autorizado = request.session.get('pedido_autorizado')

    es_autorizado = False
    if str(pedido_autorizado) == str(pedido.id):
        es_autorizado = True
    elif token_url and pedido.id_transaccion == token_url and pedido.pagado:
        es_autorizado = True
        request.session['pedido_autorizado'] = str(pedido.id)

    if not es_autorizado:
        return redirect('index')

    carrito = Carrito(request)
    carrito.limpiar()
    if 'cupon_codigo' in request.session:
        try:
            del request.session['cupon_codigo']
        except KeyError:
            pass
    request.session.modified = True

    return render(request, 'pedido_confirmado.html', {'pedido': pedido, 'carrito': carrito})


@csrf_exempt
def webhook_mercadopago(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if data.get("type") == "payment" or data.get("action") == "payment.created":
                payment_id = data.get("data", {}).get("id")
                
                if payment_id:
                    sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
                    payment_info = sdk.payment().get(payment_id)
                    payment = payment_info.get("response")
                    
                    if payment and payment.get("status") == "approved":
                        pedido_id = payment.get("external_reference")
                        
                        if pedido_id:
                            pago_procesado = False
                            pedido = None
                            with transaction.atomic():
                                pedido = Pedido.objects.select_for_update().filter(id=pedido_id).first()
                                if pedido and not pedido.pagado:
                                    pedido.confirmar_pago()
                                    pedido.id_transaccion = str(payment_id)
                                    pedido.save()
                                    pago_procesado = True
                            
                            if pago_procesado and pedido:
                                LogPedido.objects.create(
                                    pedido_id=pedido.id,
                                    codigo_orden=pedido.codigo_orden,
                                    cliente_nombre=pedido.nombre_completo,
                                    cliente_email=pedido.email,
                                    accion='PAGO_OK',
                                    detalles=f"Pago confirmado exitosamente por Webhook MercadoPago | ID Transacción MP: {payment_id}"
                                )
                                print(f"✅ ¡ÉXITO! Pedido #{pedido.id} pagado y stock descontado.")

                                # Enviamos el correo de confirmación de pago al cliente y alerta a contacto@rapidassure.cl
                                from ..emails import enviar_alerta_compra_confirmada
                                enviar_alerta_compra_confirmada(pedido, async_send=True)
                            elif pedido and pedido.pagado:
                                print(f"ℹ️ Webhook duplicado ignorado para pedido #{pedido.id}.")
                    elif payment and payment.get("status") != "approved":
                        pedido_id = payment.get("external_reference")
                        if pedido_id:
                            pedido_obj = Pedido.objects.filter(id=pedido_id).first()
                            if pedido_obj:
                                mp_status = payment.get("status")
                                accion_log = 'CANCELADO' if mp_status in ['cancelled', 'refunded'] else 'ERROR'
                                LogPedido.objects.create(
                                    pedido_id=pedido_obj.id,
                                    codigo_orden=pedido_obj.codigo_orden,
                                    cliente_nombre=pedido_obj.nombre_completo,
                                    cliente_email=pedido_obj.email,
                                    accion=accion_log,
                                    detalles=f"Notificación de Webhook MercadoPago | Estado MP: '{mp_status}' | Detalle MP: '{payment.get('status_detail', 'Sin detalle')}' | ID Transacción MP: {payment_id}"
                                )

            return JsonResponse({"status": "ok"}, status=200)

        except Exception as e:
            print(f"❌ Error en Webhook: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "method not allowed"}, status=405)
