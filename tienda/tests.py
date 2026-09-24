from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from .models import Categoria, Producto, Pedido, ItemPedido
from .carrito import Carrito

class ProductoModelTests(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre="Smart POS & Cajas")
        
    def test_producto_sin_stock_se_agota_automaticamente(self):
        """Si se guarda un producto con stock 0, debe quedar como no disponible."""
        producto = Producto.objects.create(
            categoria=self.categoria,
            nombre="Terminal POS T-800",
            precio=150000,
            stock=0,
            disponible=True
        )
        # La lógica del método save() debería cambiar disponible a False
        self.assertFalse(producto.disponible)

    def test_producto_con_stock_sigue_disponible(self):
        """Un producto con stock se mantiene disponible si así se creó."""
        producto = Producto.objects.create(
            categoria=self.categoria,
            nombre="Scanner Códigos 2D",
            precio=85000,
            stock=10,
            disponible=True
        )
        self.assertTrue(producto.disponible)

    def test_producto_galeria_imagenes(self):
        """Un producto puede tener imágenes adicionales asociadas."""
        from .models import ImagenProducto
        producto = Producto.objects.create(
            categoria=self.categoria,
            nombre="Lector RFID UHF",
            precio=180000,
            stock=5,
            disponible=True
        )
        img_extra = ImagenProducto.objects.create(
            producto=producto,
            imagen="productos/galeria/test.jpg"
        )
        self.assertEqual(len(producto.todas_las_imagenes), 1)
        self.assertEqual(producto.todas_las_imagenes[0]['id'], img_extra.id)


class CloudinaryUrlTests(TestCase):
    def test_get_cloudinary_url_local(self):
        """Verifica que las URLs locales se formateen correctamente en entorno dev."""
        from .utils import get_cloudinary_url
        url = get_cloudinary_url("/media/productos/foto.png", width=600)
        self.assertEqual(url, "/media/productos/foto.png")

    def test_get_cloudinary_url_transformations(self):
        """Verifica que se aplique f_auto, q_auto y w_{width} sin forzar extensión .jpg."""
        from .utils import get_cloudinary_url
        raw_url = "https://res.cloudinary.com/demo/image/upload/v12345/sample.png"
        url = get_cloudinary_url(raw_url, width=600)
        self.assertEqual(url, "https://res.cloudinary.com/demo/image/upload/f_auto,q_auto,w_600/v12345/sample.png")

    def test_get_cloudinary_url_reemplaza_f_jpg(self):
        """Verifica que reemplace f_jpg por f_auto y elimine transformaciones obsoletas."""
        from .utils import get_cloudinary_url
        old_url = "https://res.cloudinary.com/demo/image/upload/f_jpg,q_auto,w_600/v12345/sample.png"
        url = get_cloudinary_url(old_url, width=300)
        self.assertEqual(url, "https://res.cloudinary.com/demo/image/upload/f_auto,q_auto,w_300/v12345/sample.png")

    def test_templatetag_cloudinary_url(self):
        """Verifica el funcionamiento del template filter cloudinary_url."""
        from .templatetags.imagen_tags import cloudinary_url
        raw_url = "https://res.cloudinary.com/demo/image/upload/v12345/sample.png"
        res = cloudinary_url(raw_url, 1200)
        self.assertEqual(res, "https://res.cloudinary.com/demo/image/upload/f_auto,q_auto,w_1200/v12345/sample.png")

    def test_categoria_y_blog_image_properties(self):
        """Verifica que Categoria y BlogPost dispongan de get_imagen_url_600 y propiedades de tamaño."""
        cat = Categoria.objects.create(nombre="Categoría Test", imagen="categorias/test.jpg")
        self.assertIsNotNone(cat.get_imagen_url_600)
        self.assertIsNotNone(cat.get_imagen_url_300)

        from .models import BlogPost
        post = BlogPost.objects.create(titulo="Blog Test", contenido="Test content", imagen="blog/test.jpg")
        self.assertIsNotNone(post.get_imagen_url_600)
        self.assertIsNotNone(post.get_imagen_url_1200)

    def test_categoria_icono_fontawesome(self):
        """Verifica que Categoria asigne íconos acordes a diferentes tipos de productos electrónicos."""
        casos = [
            ("Laptops y Computadores", "fa-laptop"),
            ("Smartphones y Celulares", "fa-mobile-screen-button"),
            ("Smart POS Retail", "fa-cash-register"),
            ("Audio y Audífonos", "fa-headphones"),
            ("Cámaras de Vigilancia", "fa-camera"),
            ("Consolas y Gaming", "fa-gamepad"),
            ("Impresoras Térmicas", "fa-print"),
            ("Redes y Routers Wi-Fi", "fa-network-wired"),
            ("Discos SSD y Almacenamiento", "fa-hard-drive"),
            ("Cargadores y Baterías", "fa-bolt"),
            ("Smartwatch y Relojes", "fa-clock"),
            ("Teclados y Mouses", "fa-keyboard"),
            ("Garantías y Protección", "fa-shield-halved"),
            ("Domótica y Smart Home", "fa-house-signal"),
            ("Componentes y Tarjetas", "fa-microchip"),
        ]
        for nombre, icono_esperado in casos:
            cat = Categoria(nombre=nombre)
            self.assertEqual(cat.icono_fontawesome, icono_esperado, f"Falló para categoría: {nombre}")


class CarritoTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.categoria = Categoria.objects.create(nombre="Categoría Test")
        self.producto = Producto.objects.create(
            categoria=self.categoria,
            nombre="Cámara de Seguridad",
            precio=100000,
            stock=3,
            disponible=True
        )

    def _get_request_con_sesion(self):
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(request)
        request.session.save()
        return request

    def test_agregar_producto_nuevo(self):
        """Agregar un producto válido lo pone en el carrito."""
        request = self._get_request_con_sesion()
        carrito = Carrito(request)
        resultado = carrito.agregar(self.producto, 1)
        
        self.assertTrue(resultado)
        self.assertEqual(len(carrito.carrito), 1)
        self.assertEqual(carrito.carrito[str(self.producto.id)]['cantidad'], 1)

    def test_agregar_mas_del_stock_permitido(self):
        """Si intentan agregar más del stock, el carrito bloquea la acción."""
        request = self._get_request_con_sesion()
        carrito = Carrito(request)
        
        # Intentamos agregar 5 (el stock es 3)
        resultado = carrito.agregar(self.producto, 5)
        
        self.assertFalse(resultado) # Devuelve False por exceder límite
        self.assertEqual(carrito.carrito[str(self.producto.id)]['cantidad'], 3) # Se capa en 3

    def test_calculo_total_correcto(self):
        """El total del carrito debe multiplicar cantidad por precio."""
        request = self._get_request_con_sesion()
        carrito = Carrito(request)
        
        producto2 = Producto.objects.create(
            categoria=self.categoria, nombre="Cable de Red Cat6", precio=2000, stock=10, disponible=True
        )
        
        carrito.agregar(self.producto, 2) # 2 x 100000 = 200000
        carrito.agregar(producto2, 3)     # 3 x 2000 = 6000
        
        self.assertEqual(carrito.get_total(), 206000)

    def test_iter_no_contamina_sesion_json(self):
        """La iteración del carrito no debe inyectar objetos Producto en la sesión original."""
        request = self._get_request_con_sesion()
        carrito = Carrito(request)
        carrito.agregar(self.producto, 1)
        
        # Iteramos sobre el carrito para forzar __iter__
        list(iter(carrito))
        
        # Guardar la sesión no debe lanzar TypeError
        try:
            request.session.save()
            sesion_valida = True
        except TypeError:
            sesion_valida = False
            
        self.assertTrue(sesion_valida)

class PedidoModelTests(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre="Categoría Test")
        self.producto = Producto.objects.create(
            categoria=self.categoria,
            nombre="Pedestal Anti-Hurto",
            precio=15000,
            stock=5,
            disponible=True
        )
        self.pedido = Pedido.objects.create(
            nombre_completo="Juan Pérez",
            rut="12345678-9",
            email="juan@ejemplo.com",
            telefono="987654321",
            direccion="Calle Falsa 123",
            ciudad="Santiago"
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            producto=self.producto,
            precio=15000,
            cantidad=2
        )

    def test_confirmar_pago_descuenta_stock(self):
        """Al confirmar el pago, se debe restar el inventario."""
        self.pedido.confirmar_pago()
        
        # Actualizamos el producto desde la base de datos
        self.producto.refresh_from_db()
        
        # Habían 5, compraron 2, deberían quedar 3
        self.assertEqual(self.producto.stock, 3)
        self.assertTrue(self.producto.disponible)
        self.assertTrue(self.pedido.pagado)

    def test_confirmar_pago_agota_stock(self):
        """Si la compra consume todo el stock, el producto debe marcarse agotado."""
        item = self.pedido.items.first()
        item.cantidad = 5
        item.save()
        
        self.pedido.confirmar_pago()
        
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 0)
        self.assertFalse(self.producto.disponible)

class CuponModelTests(TestCase):
    def test_validacion_cupon(self):
        """Un cupón activo debe calcular el descuento correctamente."""
        from tienda.models import Cupon
        cupon = Cupon.objects.create(
            codigo="RAPIDA10",
            descuento_porcentaje=10,
            activo=True
        )
        valido, msg = cupon.es_valido()
        self.assertTrue(valido)
        self.assertEqual(cupon.calcular_descuento(10000), 1000)

class ApiBusquedaTests(TestCase):
    def test_api_buscar_productos(self):
        """La API de búsqueda debe retornar coincidencias en formato JSON."""
        categoria = Categoria.objects.create(nombre="Tecnología")
        Producto.objects.create(categoria=categoria, nombre="Terminal POS Smart", precio=120000, stock=5, disponible=True)
        
        response = self.client.get('/api/buscar-productos/?q=Smart')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['productos']), 1)
        self.assertIn("Terminal POS Smart", data['productos'][0]['nombre'])


class CategoriaIndexTests(TestCase):
    def test_index_oculta_categorias_sin_productos_disponibles(self):
        """La vista de inicio solo debe mostrar categorías con al menos un producto disponible."""
        cat_activa = Categoria.objects.create(nombre="Categoría Activa")
        cat_sin_stock = Categoria.objects.create(nombre="Categoría Sin Stock")
        cat_vacia = Categoria.objects.create(nombre="Categoría Vacía")

        Producto.objects.create(categoria=cat_activa, nombre="Producto Disponible", precio=1000, stock=5, disponible=True)
        Producto.objects.create(categoria=cat_sin_stock, nombre="Producto Agotado", precio=1000, stock=0, disponible=False)

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        categorias_en_contexto = list(response.context['categorias'])
        
        self.assertIn(cat_activa, categorias_en_contexto)
        self.assertNotIn(cat_sin_stock, categorias_en_contexto)
        self.assertNotIn(cat_vacia, categorias_en_contexto)


class CarritoTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.categoria = Categoria.objects.create(nombre="Tecnología")
        self.p1 = Producto.objects.create(categoria=self.categoria, nombre="Producto A", precio=10000, stock=10, disponible=True)
        self.p2 = Producto.objects.create(categoria=self.categoria, nombre="Producto B", precio=5000, stock=10, disponible=True)

    def test_carrito_length_y_total_items(self):
        """Verifica que len(carrito) y get_total_items devuelvan la suma correcta de cantidades."""
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(request)
        request.session.save()

        carrito = Carrito(request)
        self.assertEqual(len(carrito), 0)
        self.assertEqual(carrito.get_total_items(), 0)

        carrito.agregar(self.p1, cantidad=2)
        carrito.agregar(self.p2, cantidad=3)

        self.assertEqual(len(carrito), 5)
        self.assertEqual(carrito.get_total_items(), 5)
        self.assertEqual(carrito.get_total(), 35000)


class DeseosTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.categoria = Categoria.objects.create(nombre="Tecnología")
        self.p1 = Producto.objects.create(categoria=self.categoria, nombre="Producto A", precio=10000, stock=10, disponible=True)

    def test_deseos_toggle_y_mover_a_carrito(self):
        """Verifica que toggle agregue/elimine de deseos y se puedan mover al carrito."""
        from .deseos import Deseos
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(request)
        request.session.save()

        deseos = Deseos(request)
        self.assertEqual(len(deseos), 0)

        deseos.toggle(self.p1)
        self.assertEqual(len(deseos), 1)

        # Mover al carrito
        carrito = Carrito(request)
        carrito.agregar(self.p1, 1)
        deseos.eliminar(self.p1)

        self.assertEqual(len(deseos), 0)
        self.assertEqual(len(carrito), 1)

    def test_deseos_context_processor_ids(self):
        """Verifica que deseos_global proporcione la lista de IDs para el estado de los corazones."""
        from .context_processors import deseos_global
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(request)
        request.session.save()

        ctx = deseos_global(request)
        self.assertEqual(ctx['deseos_ids'], [])

        ctx['deseos'].toggle(self.p1)
        ctx_actualizado = deseos_global(request)
        self.assertIn(self.p1.id, ctx_actualizado['deseos_ids'])


class BannerPromocionalTests(TestCase):
    def test_banner_promocional_creation_and_context(self):
        """Verifica la creación de un BannerPromocional y su presencia en la portada."""
        from .models import BannerPromocional
        banner = BannerPromocional.objects.create(
            titulo="Banner Test POS",
            subtitulo="Descripción de prueba",
            badge="TEST BADGE",
            badge_gold=True,
            url_destino="/categoria/test/",
            texto_boton="Ver Más",
            estilo_fondo="dark-navy",
            icono_fontawesome="fa-cash-register",
            orden=1,
            activo=True
        )
        self.assertEqual(str(banner), "Banner Test POS (Dark Navy Metallic (Azul Marino & Índigo))")
        
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        banners_en_contexto = list(response.context['banners_promocionales'])
        self.assertIn(banner, banners_en_contexto)

    def test_banner_promocional_nuevos_gradientes_e_iconos(self):
        """Verifica que los nuevos gradientes e iconos de tecnología se guarden y muestren adecuadamente."""
        from .models import BannerPromocional
        banner = BannerPromocional.objects.create(
            titulo="Gaming & Metaverso",
            subtitulo="Consolas y visores VR",
            badge="HOT TECH",
            badge_gold=True,
            url_destino="/",
            texto_boton="Explorar",
            estilo_fondo="electric-violet",
            icono_fontawesome="fa-gamepad",
            orden=2,
            activo=True
        )
        self.assertEqual(banner.estilo_fondo, "electric-violet")
        self.assertEqual(banner.icono_fontawesome, "fa-gamepad")
        self.assertIn("Violeta Neón", banner.get_estilo_fondo_display())


class TipoEntregaCheckoutTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.categoria = Categoria.objects.create(nombre="Equipos POS")
        self.producto = Producto.objects.create(
            categoria=self.categoria,
            nombre="Impresora Térmica 80mm",
            precio=45000,
            stock=10,
            disponible=True
        )

    def test_procesar_pedido_con_retiro_en_local(self):
        """Verifica que al seleccionar Retiro en Local se asigne tipo_entrega RETIRO y la dirección por defecto."""
        session = self.client.session
        session['carrito'] = {
            str(self.producto.id): {
                'producto_id': self.producto.id,
                'nombre': self.producto.nombre,
                'precio': '45000',
                'cantidad': 1,
                'imagen': ''
            }
        }
        session.save()

        response = self.client.post('/checkout/', {
            'nombre_completo': 'Juan Pérez',
            'rut': '12.345.678-5',
            'email': 'juan@ejemplo.com',
            'telefono': '912345678',
            'tipo_entrega': 'RETIRO',
            'direccion': '',
            'ciudad': '',
            'terminos_aceptados': 'on'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'webpay_redirect.html')
        pedido = Pedido.objects.last()
        self.assertIsNotNone(pedido)
        self.assertEqual(pedido.tipo_entrega, 'RETIRO')
        self.assertEqual(pedido.direccion, 'Retiro en Local - San Diego 174 local 8')
        self.assertEqual(pedido.ciudad, 'Santiago')


class ControladorOfertasTests(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre="Smart POS")
        self.producto_oferta = Producto.objects.create(
            categoria=self.categoria,
            nombre="Terminal POS Pro Táctil",
            precio=100000,
            stock=5,
            disponible=True,
            en_oferta=True,
            porcentaje_descuento=20,
            tiene_ficha_especie=True,
            especie_nombre_comun="POS Pro",
            especie_habitat="Retail",
            especie_estado_conservacion="Garantía 24M",
            especie_dato_curioso="Pantalla capacitiva HD"
        )
        self.producto_normal = Producto.objects.create(
            categoria=self.categoria,
            nombre="Lector Código de Barras 2D",
            precio=50000,
            stock=10,
            disponible=True,
            en_oferta=False,
            porcentaje_descuento=0,
            tiene_ficha_especie=True,
            especie_nombre_comun="Lector 2D",
            especie_habitat="Logística",
            especie_estado_conservacion="Garantía 12M",
            especie_dato_curioso="Sensor CMOS rápido"
        )

    def test_calculo_precio_oferta_y_ahorro(self):
        """El precio_final debe descontar el porcentaje y el monto_ahorro ser exacto."""
        self.assertTrue(self.producto_oferta.tiene_descuento)
        self.assertEqual(self.producto_oferta.precio_final, 80000)
        self.assertEqual(self.producto_oferta.monto_ahorro, 20000)

        # Producto regular sin oferta
        self.assertFalse(self.producto_normal.tiene_descuento)
        self.assertEqual(self.producto_normal.precio_final, 50000)
        self.assertEqual(self.producto_normal.monto_ahorro, 0)

    def test_carrito_con_precio_en_oferta(self):
        """Al agregar al carrito un producto en oferta, el precio registrado debe ser el precio_final."""
        from tienda.carrito import Carrito
        from django.test import RequestFactory
        from django.contrib.sessions.middleware import SessionMiddleware

        factory = RequestFactory()
        request = factory.get('/')
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        carrito = Carrito(request)
        carrito.agregar(self.producto_oferta, cantidad=1)

        item = carrito.carrito[str(self.producto_oferta.id)]
        self.assertEqual(item['precio'], '80000')
        self.assertEqual(item['precio_original'], '100000')
        self.assertTrue(item['en_oferta'])
        self.assertEqual(item['porcentaje_descuento'], 20)

    def test_tienda_publica_muestra_precio_oferta_y_tachado(self):
        """En el detalle del producto debe figurar el precio rebajado y el precio original tachado."""
        response = self.client.get(self.producto_oferta.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('80.000', content)
        self.assertIn('100.000', content)
        self.assertIn('-20% OFF', content)


class WebpayPlusIntegrationTests(TestCase):
    def setUp(self):
        from unittest.mock import patch, MagicMock
        self.categoria = Categoria.objects.create(nombre="Hardware POS")
        self.producto = Producto.objects.create(
            categoria=self.categoria,
            nombre="Impresora Térmica 80mm",
            precio=65000,
            stock=10,
            disponible=True
        )

    def test_iniciar_pago_webpay_en_checkout(self):
        """Al procesar el pedido con Webpay, debe llamar a Transaction.create y mostrar la plantilla de redirección."""
        from unittest.mock import patch
        
        # Simular sesión con carrito
        session = self.client.session
        session['carrito'] = {
            str(self.producto.id): {
                'producto_id': self.producto.id,
                'nombre': self.producto.nombre,
                'precio': '65000',
                'cantidad': 1,
                'imagen': ''
            }
        }
        session.save()

        with patch('tienda.views.checkout_pagos.Transaction.create') as mock_create:
            mock_create.return_value = {
                'token': 'mock-token-webpay-123456',
                'url': 'https://webpay3gint.transbank.cl/webpayserver/initTransaction'
            }

            response = self.client.post('/checkout/', {
                'nombre_completo': 'Carlos Valdés',
                'rut': '12.345.678-5',
                'email': 'carlos@example.com',
                'telefono': '987654321',
                'tipo_entrega': 'ENVIO',
                'direccion': 'Av Providencia 1234',
                'ciudad': 'Santiago',
                'terminos_aceptados': 'on'
            })

            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'webpay_redirect.html')
            self.assertIn('mock-token-webpay-123456', response.content.decode('utf-8'))
            self.assertTrue(mock_create.called)

            # Verificar que el pedido se creó con token y metodo_pago WEBPAY
            pedido = Pedido.objects.latest('id')
            self.assertEqual(pedido.id_transaccion, 'mock-token-webpay-123456')
            self.assertEqual(pedido.metodo_pago, 'WEBPAY')
            self.assertFalse(pedido.pagado)

    def test_retorno_webpay_exitoso_confirma_pedido_y_descuenta_stock(self):
        """Cuando Webpay retorna token_ws aprobado, el pedido se marca pagado y descuenta stock."""
        from unittest.mock import patch

        pedido = Pedido.objects.create(
            nombre_completo='Fernanda Lagos',
            rut='15.345.678-9',
            email='fernanda@example.com',
            telefono='912345678',
            tipo_entrega='RETIRO',
            direccion='San Diego 174',
            ciudad='Santiago',
            id_transaccion='token-aprobado-777',
            metodo_pago='WEBPAY'
        )
        ItemPedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            precio=65000,
            cantidad=2
        )

        with patch('tienda.views.checkout_pagos.Transaction.commit') as mock_commit:
            mock_commit.return_value = {
                'response_code': 0,
                'status': 'AUTHORIZED',
                'buy_order': f'ORD-{pedido.codigo_orden}',
                'session_id': f'PEDIDO-{pedido.id}',
                'amount': 130000,
                'authorization_code': '123456',
                'payment_type_code': 'VD',
                'card_detail': {'card_number': '6623'},
                'installments_number': 0
            }

            response = self.client.post('/webpay/retorno/', {'token_ws': 'token-aprobado-777'})
            self.assertRedirects(response, f'/pedido-confirmado/{pedido.id}/')

            pedido.refresh_from_db()
            self.assertTrue(pedido.pagado)
            self.assertEqual(pedido.codigo_autorizacion, '123456')
            self.assertEqual(pedido.tipo_pago, 'Redcompra (Débito)')
            self.assertEqual(pedido.tarjeta_ultimos_digitos, '6623')

            self.producto.refresh_from_db()
            self.assertEqual(self.producto.stock, 8)

    def test_retorno_webpay_rechazado(self):
        """Cuando Webpay retorna response_code != 0, el pedido no se marca como pagado."""
        from unittest.mock import patch

        pedido = Pedido.objects.create(
            nombre_completo='Pedro Soto',
            rut='12.345.678-5',
            email='pedro@example.com',
            telefono='911223344',
            tipo_entrega='ENVIO',
            direccion='Alameda 100',
            ciudad='Santiago',
            id_transaccion='token-rechazado-999',
            metodo_pago='WEBPAY'
        )

        with patch('tienda.views.checkout_pagos.Transaction.commit') as mock_commit:
            mock_commit.return_value = {
                'response_code': -1,
                'status': 'FAILED',
                'buy_order': f'ORD-{pedido.codigo_orden}',
                'session_id': f'PEDIDO-{pedido.id}',
                'amount': 65000
            }

            response = self.client.post('/webpay/retorno/', {'token_ws': 'token-rechazado-999'})
            self.assertRedirects(response, '/?cart=open')

            pedido.refresh_from_db()
            self.assertFalse(pedido.pagado)

    def test_retorno_webpay_cancelado_por_usuario(self):
        """Cuando el cliente cancela en Webpay (TBK_TOKEN), se redirige y no se marca como pagado."""
        pedido = Pedido.objects.create(
            nombre_completo='Lucia Diaz',
            rut='16.789.012-3',
            email='lucia@example.com',
            telefono='955667788',
            tipo_entrega='RETIRO',
            direccion='San Diego 174',
            ciudad='Santiago',
            id_transaccion='token-anulado-000',
            metodo_pago='WEBPAY'
        )

        response = self.client.post('/webpay/retorno/', {
            'TBK_TOKEN': 'token-anulado-000',
            'TBK_ORDEN_COMPRA': f'ORD-{pedido.codigo_orden}'
        })
        self.assertRedirects(response, '/?cart=open')

        pedido.refresh_from_db()
        self.assertFalse(pedido.pagado)








