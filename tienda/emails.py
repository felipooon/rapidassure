import os
import json
import logging
import threading
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.db import transaction
from .models import LogPedido

logger = logging.getLogger(__name__)

# Destinatario y remitente oficial de Rapidassure Retail
EMAIL_CONTACTO_OFICIAL = 'contacto@rapidassure.cl'
FROM_EMAIL_CONTACTO = f"Rapidassure Retail <{EMAIL_CONTACTO_OFICIAL}>"


def _construir_destinatarios_admin():
    """
    Retorna la lista de correos que deben recibir la alerta de nuevo pedido.
    Siempre incluye contacto@rapidassure.cl, sin variantes erróneas.
    """
    destinatarios = [EMAIL_CONTACTO_OFICIAL]
    contact_email = getattr(settings, 'CONTACT_EMAIL', '')
    if contact_email:
        clean_contact = contact_email.strip().lower()
        if 'rapidasure.cl' not in clean_contact and clean_contact not in [d.lower() for d in destinatarios]:
            destinatarios.append(clean_contact)
    return destinatarios


def _despachar_email(asunto, texto, html, destinatarios, from_email=None, reply_to=None):
    """
    Envía un correo con HTML y texto plano.
    1. Si se define RESEND_API_KEY o BREVO_API_KEY, usa API HTTPS (ideal para Render sin SMTP abierto).
    2. En su defecto o ante fallback, usa EmailMultiAlternatives estándar de Django (SMTP, console o locmem para tests).
    """
    from_email = from_email or FROM_EMAIL_CONTACTO
    reply_to_list = reply_to or [EMAIL_CONTACTO_OFICIAL]

    resend_key = os.environ.get('RESEND_API_KEY', '').strip()
    brevo_key = os.environ.get('BREVO_API_KEY', '').strip()

    if resend_key:
        try:
            import urllib.request
            resend_from = os.environ.get('RESEND_FROM_EMAIL', from_email).strip()
            payload = {
                "from": resend_from,
                "to": destinatarios,
                "subject": asunto,
                "text": texto,
                "html": html,
                "reply_to": reply_to_list,
            }
            req = urllib.request.Request(
                "https://api.resend.com/emails",
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    "Authorization": f"Bearer {resend_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "RapidassureApp/1.0"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                logger.info(f"[Emails] Enviado vía Resend API a {destinatarios}")
                return True
        except Exception as e_resend:
            logger.error(f"[Emails] Error enviando vía Resend API: {e_resend}, intentando backend Django...")

    if brevo_key:
        try:
            import urllib.request
            sender_email = os.environ.get('BREVO_SENDER_EMAIL', EMAIL_CONTACTO_OFICIAL).strip()
            payload = {
                "sender": {"name": "Rapidassure Retail", "email": sender_email},
                "to": [{"email": d} for d in destinatarios],
                "subject": asunto,
                "textContent": texto,
                "htmlContent": html,
                "replyTo": {"email": reply_to_list[0]} if reply_to_list else None,
            }
            req = urllib.request.Request(
                "https://api.brevo.com/v3/smtp/email",
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    "api-key": brevo_key,
                    "Content-Type": "application/json",
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                logger.info(f"[Emails] Enviado vía Brevo API a {destinatarios}")
                return True
        except Exception as e_brevo:
            logger.error(f"[Emails] Error enviando vía Brevo API: {e_brevo}, intentando backend Django...")

    # Backend estándar Django
    msg = EmailMultiAlternatives(
        subject=asunto,
        body=texto,
        from_email=from_email,
        to=destinatarios,
        reply_to=reply_to_list,
    )
    if html:
        msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)
    return True


def _obtener_url_rastreo(empresa, seguimiento):
    """Genera el enlace de consulta directa según la empresa de envíos."""
    if not seguimiento:
        return ""
    cod = str(seguimiento).strip()
    emp = str(empresa or '').strip().lower()

    if 'blue' in emp:
        return f"https://seguimiento.bluex.cl/tracking?os={cod}"
    elif 'chilexpress' in emp:
        return f"https://www.chilexpress.cl/seguimiento-envio?numero={cod}"
    elif 'starken' in emp:
        return f"https://www.starken.cl/seguimiento?codigo={cod}"
    elif 'correos' in emp:
        return f"https://www.correos.cl/seguimiento-en-linea?envio={cod}"
    return "https://www.bluex.cl/"


def _generar_texto_plano_cliente(pedido, items, total_final, subtotal):
    """Genera la versión en texto plano para el correo del cliente."""
    lineas_items = []
    for item in items:
        lineas_items.append(f"- {item.cantidad}x {item.producto.nombre} | ${item.get_costo():,}")
    items_str = "\n".join(lineas_items)

    info_entrega = f"Modalidad: {pedido.get_tipo_entrega_display()}\nDirección: {pedido.direccion}, {pedido.comuna}, {pedido.region}\nTeléfono: {pedido.telefono_display}"
    if pedido.tipo_entrega == 'PUNTO_BLUE' and pedido.punto_entrega_nombre:
        info_entrega = f"Modalidad: {pedido.get_tipo_entrega_display()}\nAgencia Blue: {pedido.punto_entrega_nombre} (ID: {pedido.punto_entrega_id})\nDirección: {pedido.direccion}\nTeléfono: {pedido.telefono_display}"

    info_factura = ""
    if pedido.requiere_factura:
        info_factura = f"\nSOLICITUD DE FACTURA:\nRazón Social: {pedido.razon_social}\nRUT: {pedido.rut_empresa}\nGiro: {pedido.giro_comercial}\n"

    costo_envio_str = "GRATIS" if pedido.costo_envio == 0 else f"${pedido.costo_envio:,}"

    return f"""¡Hola {pedido.nombre_completo}!

Confirmamos que tu compra en Rapidassure Retail ha sido procesada y confirmada con éxito.

============================================================
ORDEN DE COMPRA: #{pedido.codigo_orden}
============================================================

📦 AVISO IMPORTANTE SOBRE TU DESPACHO:
Pronto recibirás el número de seguimiento de tu envío.
Estamos preparando tus productos en bodega. En cuanto tu paquete sea entregado a la empresa de transporte, te enviaremos tu código de rastreo para que puedas seguir su trayecto en todo momento.

PRODUCTOS COMPRADOS:
{items_str}

RESUMEN DE PAGO:
- Subtotal: ${subtotal:,}
- Descuento: -${pedido.descuento_aplicado:,}
- Costo Envío ({pedido.get_tipo_entrega_display()}): {costo_envio_str}
------------------------------------------------------------
TOTAL PAGADO: ${total_final:,} CLP
Medio de Pago: {pedido.metodo_pago}
------------------------------------------------------------

DATOS DE ENTREGA:
{info_entrega}
{info_factura}
Si tienes dudas o necesitas asistencia con tu compra, no dudes en escribirnos a {EMAIL_CONTACTO_OFICIAL}.

¡Muchas gracias por elegir Rapidassure Retail!
https://rapidassure.cl
"""


def _generar_texto_plano_admin(pedido, items, total_final, link_panel):
    """Genera la versión en texto plano para el correo de administración."""
    lineas_items = []
    for item in items:
        lineas_items.append(f"- {item.cantidad}x {item.producto.nombre} | ${item.get_costo():,}")
    items_str = "\n".join(lineas_items)

    info_factura = "Boleta Electrónica"
    if pedido.requiere_factura:
        info_factura = f"FACTURA: Razón Social: {pedido.razon_social} | RUT: {pedido.rut_empresa} | Giro: {pedido.giro_comercial}"

    return f"""🔔 ALERTA DE NUEVO PEDIDO CONFIRMADO
============================================================
Orden: #{pedido.codigo_orden} (ID BD: #{pedido.id})
Total Pagado: ${total_final:,} CLP
Medio de Pago: {pedido.metodo_pago} (Cód. Aut: {pedido.codigo_autorizacion or 'N/A'})
Fecha: {pedido.creado.strftime('%d/%m/%Y %H:%M') if pedido.creado else 'Reciente'}
============================================================

CLIENTE:
- Nombre: {pedido.nombre_completo}
- RUT: {pedido.rut}
- Email: {pedido.email}
- Teléfono: {pedido.telefono_display} (WhatsApp: https://wa.me/{pedido.telefono_wa})

DESPACHO:
- Tipo: {pedido.get_tipo_entrega_display()}
- Dirección: {pedido.direccion}, {pedido.comuna}, {pedido.region}
- Costo Cobrado Envío: ${pedido.costo_envio:,}

DOCUMENTO TRIBUTARIO:
- {info_factura}

ÍTEMS COMPRADOS:
{items_str}

👉 GESTIONAR EN EL PANEL:
{link_panel}
"""


def _generar_texto_plano_seguimiento(pedido, items, url_rastreo):
    """Genera la versión en texto plano para el correo de despacho y seguimiento."""
    lineas_items = []
    for item in items:
        lineas_items.append(f"- {item.cantidad}x {item.producto.nombre}")
    items_str = "\n".join(lineas_items)

    rastreo_txt = f"Enlace de seguimiento: {url_rastreo}\n" if url_rastreo else ""

    return f"""¡Hola {pedido.nombre_completo}!

¡Te tenemos excelentes noticias! Tu pedido #{pedido.codigo_orden} de Rapidassure Retail ha sido enviado.

============================================================
DETALLES DEL DESPACHO:
============================================================
- Transporte: {pedido.empresa_transporte or 'Empresa de Envíos'}
- Código / Nº de Seguimiento: {pedido.numero_seguimiento}
{rastreo_txt}
DESTINO:
- Modalidad: {pedido.get_tipo_entrega_display()}
- Dirección: {pedido.direccion}, {pedido.comuna}, {pedido.region}
- Teléfono: {pedido.telefono_display}

PRODUCTOS EN ESTE ENVÍO:
{items_str}

Si tienes alguna consulta, puedes responder a este correo o escribir a {EMAIL_CONTACTO_OFICIAL}.

¡Muchas gracias por comprar en Rapidassure Retail!
https://rapidassure.cl
"""


def _ejecutar_envio_correos_confirmacion(pedido_id):
    """
    Tarea interna que ejecuta el envío real de los correos para cliente y admin.
    """
    from .models import Pedido
    try:
        pedido = Pedido.objects.filter(id=pedido_id).first()
        if not pedido:
            logger.error(f"[Emails] Pedido #{pedido_id} no encontrado para enviar correos.")
            return

        items = list(pedido.items.select_related('producto').all())
        subtotal = pedido.get_total_cost()
        total_final = pedido.get_total_final()
        link_panel = f"https://rapidassure.cl/panel/pedidos/{pedido.id}/"
        from_email = FROM_EMAIL_CONTACTO

        contexto = {
            'pedido': pedido,
            'items': items,
            'subtotal': f"{subtotal:,}",
            'total_final': f"{total_final:,}",
            'link_panel': link_panel,
        }

        # -------------------------------------------------------------
        # 1. CORREO AL CLIENTE (Remitente: contacto@rapidassure.cl)
        # -------------------------------------------------------------
        cliente_email = (pedido.email or '').strip()
        if cliente_email:
            try:
                asunto_cliente = f"¡Compra Confirmada! Pedido #{pedido.codigo_orden} - Rapidassure Retail"
                html_cliente = render_to_string('emails/cliente_confirmacion_compra.html', contexto)
                texto_cliente = _generar_texto_plano_cliente(pedido, items, total_final, subtotal)
                _despachar_email(
                    asunto_cliente,
                    texto_cliente,
                    html_cliente,
                    [cliente_email],
                    from_email=from_email,
                    reply_to=[EMAIL_CONTACTO_OFICIAL]
                )
                logger.info(f"[Emails] Correo de confirmación enviado al cliente: {cliente_email} desde {EMAIL_CONTACTO_OFICIAL}")
            except Exception as e_cliente:
                logger.error(f"[Emails] Error al enviar confirmación al cliente {cliente_email}: {e_cliente}")

        # -------------------------------------------------------------
        # 2. ALERTA AL ADMINISTRADOR (contacto@rapidassure.cl)
        # -------------------------------------------------------------
        destinatarios_admin = _construir_destinatarios_admin()
        if destinatarios_admin:
            try:
                asunto_admin = f"🔔 Nuevo Pedido Confirmado #{pedido.codigo_orden} - ${total_final:,} CLP - {pedido.nombre_completo}"
                html_admin = render_to_string('emails/admin_nuevo_pedido.html', contexto)
                texto_admin = _generar_texto_plano_admin(pedido, items, total_final, link_panel)
                _despachar_email(
                    asunto_admin,
                    texto_admin,
                    html_admin,
                    destinatarios_admin,
                    from_email=from_email,
                    reply_to=[EMAIL_CONTACTO_OFICIAL]
                )
                logger.info(f"[Emails] Alerta de nuevo pedido enviada a administradores: {destinatarios_admin}")
            except Exception as e_admin:
                logger.error(f"[Emails] Error al enviar alerta a admin {destinatarios_admin}: {e_admin}")

        # -------------------------------------------------------------
        # 3. REGISTRO EN AUDITORÍA LOG_PEDIDO
        # -------------------------------------------------------------
        try:
            LogPedido.objects.create(
                pedido_id=pedido.id,
                codigo_orden=pedido.codigo_orden,
                cliente_nombre=pedido.nombre_completo,
                cliente_email=pedido.email,
                accion='CORREO_CONFIRMACION',
                detalles=(
                    f"Correos de confirmación procesados | "
                    f"Cliente: {cliente_email} | "
                    f"Admin: {', '.join(destinatarios_admin)} | "
                    f"Remitente: {EMAIL_CONTACTO_OFICIAL}"
                )
            )
        except Exception as e_log:
            logger.warning(f"[Emails] No se pudo guardar el LogPedido: {e_log}")

    except Exception as e_gral:
        logger.error(f"[Emails] Error general procesando correos de confirmación para pedido #{pedido_id}: {e_gral}")


def enviar_alerta_compra_confirmada(pedido, async_send=True):
    """
    Punto de entrada principal para disparar las alertas de compra confirmada.
    - Envía confirmación al cliente notificando que pronto recibirá su número de seguimiento.
    - Envía alerta con detalles y link al panel a contacto@rapidassure.cl.
    - Si async_send es True, usa transaction.on_commit para asegurar que la
      transacción de base de datos esté committeada antes de leer datos en el thread.
    - Si async_send es False, ejecuta inmediatamente en el hilo actual.
    """
    if not pedido or not pedido.id:
        return

    pedido_id = pedido.id

    if not async_send:
        _ejecutar_envio_correos_confirmacion(pedido_id)
        return

    def _disparar():
        t = threading.Thread(
            target=_ejecutar_envio_correos_confirmacion,
            args=(pedido_id,),
            daemon=True
        )
        t.start()

    try:
        transaction.on_commit(_disparar)
    except Exception:
        _disparar()


def enviar_correo_seguimiento_despacho(pedido, request_user=None):
    """
    Envía el correo al cliente con el número de seguimiento y datos del despacho.
    Sale con remitente explícito: contacto@rapidassure.cl
    """
    if not pedido or not pedido.email:
        raise ValueError("El pedido no tiene un correo de cliente válido.")

    if not pedido.numero_seguimiento:
        raise ValueError("El pedido no cuenta con número de seguimiento ingresado.")

    items = list(pedido.items.select_related('producto').all())
    url_rastreo = _obtener_url_rastreo(pedido.empresa_transporte, pedido.numero_seguimiento)

    contexto = {
        'pedido': pedido,
        'items': items,
        'url_rastreo': url_rastreo,
        'email_contacto': EMAIL_CONTACTO_OFICIAL,
    }

    asunto = f"Tu pedido #{pedido.codigo_orden} de Rapidassure Retail ya va en camino"
    html_content = render_to_string('emails/cliente_seguimiento_envio.html', contexto)
    texto_content = _generar_texto_plano_seguimiento(pedido, items, url_rastreo)

    from_email = FROM_EMAIL_CONTACTO
    destinatario = pedido.email.strip()

    _despachar_email(
        asunto=asunto,
        texto=texto_content,
        html=html_content,
        destinatarios=[destinatario],
        from_email=from_email,
        reply_to=[EMAIL_CONTACTO_OFICIAL]
    )

    # Registrar en LogPedido
    usuario_log = request_user if request_user and getattr(request_user, 'is_authenticated', False) else None
    LogPedido.objects.create(
        pedido_id=pedido.id,
        codigo_orden=pedido.codigo_orden,
        cliente_nombre=pedido.nombre_completo,
        cliente_email=pedido.email,
        accion='SEGUIMIENTO',
        usuario=usuario_log,
        detalles=(
            f"Correo de despacho enviado a {destinatario} desde {EMAIL_CONTACTO_OFICIAL} | "
            f"Transporte: {pedido.empresa_transporte or 'No especificado'} | "
            f"Nº Seguimiento: {pedido.numero_seguimiento}"
        )
    )

    logger.info(f"[Emails] Correo de seguimiento enviado exitosamente a {destinatario} desde {EMAIL_CONTACTO_OFICIAL}")
    return True
