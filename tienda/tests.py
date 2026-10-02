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

    def test_producto_con_marca(self):
        """Un producto puede guardar su marca correctamente."""
        producto = Producto.objects.create(
            categoria=self.categoria,
            marca="Zebra Technologies",
            nombre="Impresora Térmica ZD220",
            precio=199990,
            stock=4,
            disponible=True
        )
        self.assertEqual(producto.marca, "Zebra Technologies")

    def test_producto_form_con_marca(self):
        """El formulario ProductoForm procesa y guarda el campo marca."""
        from .forms import ProductoForm
        from django.core.files.uploadedfile import SimpleUploadedFile

        imagen_dummy = SimpleUploadedFile(
            name='test_img.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/jpeg'
        )

        form = ProductoForm(
            data={
                'categoria': self.categoria.id,
                'marca': 'Honeywell',
                'nombre': 'Lector Láser Voyager 1200g',
                'precio': '89.990',
                'stock': 12,
                'disponible': True,
                'tiene_ficha_especie': True,
                'especie_nombre_comun': 'Lector 1D',
                'especie_habitat': 'Retail y Farmacias',
                'especie_estado_conservacion': 'Garantía 12 Meses',
                'especie_dato_curioso': 'Lectura precisa de alta velocidad',
            },
            files={'imagen': imagen_dummy}
        )
        self.assertTrue(form.is_valid(), form.errors)
        prod = form.save()
        self.assertEqual(prod.marca, 'Honeywell')

    def test_producto_dimensiones_y_peso_blueexpress(self):
        """Un producto puede almacenar alto, ancho, largo y peso y calcular volumen y peso volumétrico."""
        from decimal import Decimal
        producto = Producto.objects.create(
            categoria=self.categoria,
            nombre="Caja POS Terminal",
            precio=250000,
            stock=10,
            disponible=True,
            alto=Decimal('20.00'),
            ancho=Decimal('30.00'),
            largo=Decimal('40.00'),
            peso=Decimal('2.50')
        )
        self.assertEqual(producto.alto, Decimal('20.00'))
        self.assertEqual(producto.ancho, Decimal('30.00'))
        self.assertEqual(producto.largo, Decimal('40.00'))
        self.assertEqual(producto.peso, Decimal('2.50'))
        self.assertEqual(producto.volumen_cm3, 24000.0)
        # Fórmula: (20 * 30 * 40) / 4000 = 6.00
        self.assertEqual(producto.peso_volumetrico, 6.0)

    def test_producto_dimensiones_opcionales(self):
        """Las dimensiones y peso para Blue Express son completamente opcionales."""
        producto = Producto.objects.create(
            categoria=self.categoria,
            nombre="Producto Sin Medidas",
            precio=5000,
            stock=1,
            disponible=True
        )
        self.assertIsNone(producto.alto)
        self.assertIsNone(producto.ancho)
        self.assertIsNone(producto.largo)
        self.assertIsNone(producto.peso)
        self.assertIsNone(producto.peso_volumetrico)
        self.assertIsNone(producto.volumen_cm3)

    def test_producto_form_dimensiones_blueexpress(self):
        """El formulario ProductoForm permite guardar o dejar vacías las dimensiones."""
        from .forms import ProductoForm
        from django.core.files.uploadedfile import SimpleUploadedFile
        from decimal import Decimal

        imagen_dummy = SimpleUploadedFile(
            name='test_img_dim.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/jpeg'
        )

        form = ProductoForm(
            data={
                'categoria': self.categoria.id,
                'nombre': 'Equipo POS con Medidas',
                'precio': '150.000',
                'stock': 5,
                'disponible': True,
                'alto': '15.5',
                'ancho': '25.0',
                'largo': '35.0',
                'peso': '1.80',
                'tiene_ficha_especie': True,
                'especie_nombre_comun': 'Equipo POS',
                'especie_habitat': 'Comercio',
                'especie_estado_conservacion': 'Garantía 1 Año',
                'especie_dato_curioso': 'Ficha técnica completa',
            },
            files={'imagen': imagen_dummy}
        )
        self.assertTrue(form.is_valid(), form.errors)
        prod = form.save()
        self.assertEqual(prod.alto, Decimal('15.5'))
        self.assertEqual(prod.ancho, Decimal('25.0'))
        self.assertEqual(prod.largo, Decimal('35.0'))
        self.assertEqual(prod.peso, Decimal('1.80'))


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

    def test_limpiar_carrito_vacia_memoria_y_sesion(self):
        """limpiar() debe vaciar el diccionario en memoria y el diccionario de sesión."""
        request = self._get_request_con_sesion()
        carrito = Carrito(request)
        carrito.agregar(self.producto, 2)
        self.assertEqual(len(carrito), 2)
        self.assertGreater(carrito.get_total(), 0)

        carrito.limpiar()
        self.assertEqual(len(carrito), 0)
        self.assertEqual(carrito.get_total(), 0)
        self.assertEqual(carrito.carrito, {})
        self.assertEqual(request.session.get('carrito'), {})

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

    def test_producto_form_calcula_porcentaje_desde_monto_descuento(self):
        """Si en el formulario se ingresa monto_descuento pero no porcentaje, debe calcular el porcentaje automáticamente."""
        from tienda.forms import ProductoForm
        from django.core.files.uploadedfile import SimpleUploadedFile

        gif_bytes = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        imagen_dummy = SimpleUploadedFile("test.gif", gif_bytes, content_type="image/gif")
        data = {
            'nombre': 'Lector Barcode QR',
            'categoria': self.categoria.id,
            'marca': 'Zebra',
            'precio': '100.000',
            'stock': '5',
            'disponible': 'on',
            'en_oferta': 'on',
            'monto_descuento': '25.000',
            'porcentaje_descuento': '',
            'especie_nombre_comun': 'Lector QR',
            'especie_habitat': 'Retail',
            'especie_estado_conservacion': 'Garantía 12M',
            'especie_dato_curioso': 'Lectura omnidireccional',
        }
        form = ProductoForm(data=data, files={'imagen': imagen_dummy})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['porcentaje_descuento'], 25)

    def test_producto_form_inicializa_monto_descuento_al_editar(self):
        """Al instanciar ProductoForm con un producto que tiene descuento, monto_descuento debe inicializarse."""
        from tienda.forms import ProductoForm
        form = ProductoForm(instance=self.producto_oferta)
        self.assertEqual(form.initial.get('monto_descuento'), '20.000')

    def test_descuento_monto_fijo_exacto_sin_desfase_redondeo(self):
        """Validar que un descuento de $30.000 sobre $69.990 resulte en $39.990 exactos y no $39.894 (sin desfase de $96 pesos)."""
        from tienda.forms import ProductoForm
        from django.core.files.uploadedfile import SimpleUploadedFile
        from tienda.carrito import Carrito
        from django.test import RequestFactory
        from django.contrib.sessions.middleware import SessionMiddleware

        gif_bytes = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        imagen_dummy = SimpleUploadedFile("test.gif", gif_bytes, content_type="image/gif")

        data = {
            'nombre': 'Terminal POS Especial',
            'categoria': self.categoria.id,
            'marca': 'POSBrand',
            'precio': '69.990',
            'stock': '15',
            'disponible': 'on',
            'en_oferta': 'on',
            'monto_descuento': '30.000',
            'porcentaje_descuento': '43',
            'especie_nombre_comun': 'Terminal POS',
            'especie_habitat': 'Retail',
            'especie_estado_conservacion': 'Garantía 24M',
            'especie_dato_curioso': 'Batería de larga duración',
        }
        form = ProductoForm(data=data, files={'imagen': imagen_dummy})
        self.assertTrue(form.is_valid(), form.errors)
        producto = form.save()

        # El precio final debe ser exactamente 39.990 (69.990 - 30.000)
        self.assertEqual(producto.precio, 69990)
        self.assertEqual(producto.precio_oferta, 39990)
        self.assertEqual(producto.precio_final, 39990)
        self.assertEqual(producto.monto_ahorro, 30000)
        self.assertEqual(producto.porcentaje_descuento, 43)

        # En el carrito debe registrar exactamente 39.990
        factory = RequestFactory()
        request = factory.get('/')
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        carrito = Carrito(request)
        carrito.agregar(producto, cantidad=1)
        item = carrito.carrito[str(producto.id)]
        self.assertEqual(item['precio'], '39990')
        self.assertEqual(item['precio_original'], '69990')



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
            self.assertRedirects(response, f'/pedido-confirmado/{pedido.id}/?token=token-aprobado-777')

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


class BlueExpressIntegrationTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.admin_user = User.objects.create_superuser(
            username='admin_bx',
            email='admin@rapidassure.cl',
            password='adminpassword123'
        )
        self.categoria = Categoria.objects.create(nombre="Logística & POS")
        self.producto = Producto.objects.create(
            categoria=self.categoria,
            nombre="Lector Código de Barras 2D",
            precio=15000,
            stock=10,
            peso=0.6,
            alto=10,
            ancho=12,
            largo=18,
            disponible=True
        )

    def test_calcular_costo_envio_zonas(self):
        """Verifica que las tarifas zonales de Blue Express calculen adecuadamente."""
        from .comunas_chile import calcular_costo_envio, obtener_tarifa_base_comuna

        # Tarifas oficiales Talla XS (hasta 0.5 kg)
        self.assertEqual(obtener_tarifa_base_comuna('Santiago'), 3100)
        self.assertEqual(obtener_tarifa_base_comuna('Providencia'), 3100)
        self.assertEqual(obtener_tarifa_base_comuna('Viña del Mar'), 4300)
        self.assertEqual(obtener_tarifa_base_comuna('Punta Arenas'), 5200)

        # Tarifas por Tallas (XS, S, M, L)
        from .comunas_chile import obtener_tarifa_blue_express
        # Santiago (RM): 3100, 4200, 4800, 5400
        self.assertEqual(obtener_tarifa_blue_express('Santiago', peso_kg=0.3), 3100)
        self.assertEqual(obtener_tarifa_blue_express('Santiago', peso_kg=1.5), 4200)
        self.assertEqual(obtener_tarifa_blue_express('Santiago', peso_kg=4.0), 4800)
        self.assertEqual(obtener_tarifa_blue_express('Santiago', peso_kg=10.0), 5400)

        # Centro (Copiapó a Puerto Montt): 4300, 5600, 7300, 9200
        self.assertEqual(obtener_tarifa_blue_express('Valparaíso', peso_kg=0.3), 4300)
        self.assertEqual(obtener_tarifa_blue_express('Concepción', peso_kg=2.0), 5600)
        self.assertEqual(obtener_tarifa_blue_express('Temuco', peso_kg=5.0), 7300)
        self.assertEqual(obtener_tarifa_blue_express('Puerto Montt', peso_kg=8.0), 9200)

        # Extremo (Arica, Iquique, Aysén, Magallanes): 5200, 9500, 14500, 17000
        self.assertEqual(obtener_tarifa_blue_express('Arica', peso_kg=0.4), 5200)
        self.assertEqual(obtener_tarifa_blue_express('Punta Arenas', peso_kg=2.5), 9500)
        self.assertEqual(obtener_tarifa_blue_express('Coyhaique', peso_kg=4.5), 14500)
        self.assertEqual(obtener_tarifa_blue_express('Punta Arenas', peso_kg=12.0), 17000)

        # Envío gratis para compras >= 19.990 aplica con tipo_entrega='GRATIS_RM' en la Región Metropolitana
        self.assertEqual(calcular_costo_envio('Santiago', 20000, 2.0, tipo_entrega='GRATIS_RM'), 0)
        self.assertEqual(calcular_costo_envio('Providencia', 25000, 0.4, tipo_entrega='GRATIS_RM'), 0)
        # Si no cumple el monto mínimo o es fuera de RM, calcula la tarifa correspondiente
        self.assertEqual(calcular_costo_envio('Santiago', 15000, 0.4, tipo_entrega='GRATIS_RM'), 3100)
        self.assertEqual(calcular_costo_envio('Punta Arenas', 20000, 0.4, tipo_entrega='GRATIS_RM'), 5200)

        # Fuera de la RM se cobra siempre la tarifa correspondiente según peso
        self.assertEqual(calcular_costo_envio('Viña del Mar', 50000, 0.4), 4300)
        self.assertEqual(calcular_costo_envio('Concepción', 100000, 2.0), 5600)

    def test_pedido_calculo_total_con_costo_envio(self):
        """El método get_total_final del Pedido debe sumar el costo_envio."""
        pedido = Pedido.objects.create(
            nombre_completo='Mario Casas',
            rut='15.456.789-0',
            email='mario@example.com',
            telefono='911223344',
            tipo_entrega='ENVIO',
            direccion='Av. Alemania 500',
            ciudad='Temuco',
            comuna='Temuco',
            region='Región de La Araucanía',
            costo_envio=5600,
            empresa_transporte='Blue Express'
        )
        ItemPedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            precio=15000,
            cantidad=1
        )
        # Total esperado: 15.000 + 5.600 = 20.600
        self.assertEqual(pedido.get_total_cost(), 15000)
        self.assertEqual(pedido.costo_envio, 5600)
        self.assertEqual(pedido.get_total_final(), 20600)

    def test_api_cotizar_envio_endpoint(self):
        """El endpoint /api/cotizar-envio/ debe responder JSON con la cotización correcta."""
        # Carrito vacío (peso por defecto 0.40 kg = Talla XS)
        response = self.client.get('/api/cotizar-envio/?comuna=Santiago')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['comuna'], 'Santiago')
        self.assertEqual(data['costo_envio'], 3100)

        # Cotización a Punta Arenas (Talla XS Extremo)
        response_ext = self.client.get('/api/cotizar-envio/?comuna=Punta Arenas')
        self.assertEqual(response_ext.status_code, 200)
        data_ext = response_ext.json()
        self.assertEqual(data_ext['costo_envio'], 5200)

    def test_exportar_pedidos_blue_express_excel(self):
        """Verifica que la exportación de Carga Masiva Blue Express genere un archivo .xlsx válido."""
        Pedido.objects.create(
            nombre_completo='Cliente Despacho',
            rut='18.111.222-3',
            email='despacho@example.com',
            telefono='987654321',
            tipo_entrega='ENVIO',
            direccion='Los Alerces 123',
            ciudad='Providencia',
            comuna='Providencia',
            region='Región Metropolitana de Santiago',
            costo_envio=3490,
            estado='PAGADO',
            pagado=True,
            empresa_transporte='Blue Express'
        )

        self.client.login(username='admin_bx', password='adminpassword123')
        response = self.client.get('/panel/pedidos/exportar-blue-express/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', response['Content-Type'])
        self.assertIn('Carga_Masiva_Blue_Express', response['Content-Disposition'])

        import io, openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        self.assertIn('Carga Masiva', wb.sheetnames)
        ws = wb['Carga Masiva']
        # Cabeceras oficiales en fila 5
        self.assertEqual(ws.cell(5, 3).value, 'Nº Referencia*')
        self.assertEqual(ws.cell(5, 4).value, 'Nombre Completo*')
        self.assertEqual(ws.cell(5, 7).value, 'Región*')
        self.assertEqual(ws.cell(5, 8).value, 'Comuna*')
        self.assertEqual(ws.cell(5, 9).value, 'Nombre calle*')
        self.assertEqual(ws.cell(5, 10).value, 'N° Domicilio *')
        # Datos del pedido en fila 6
        self.assertEqual(ws.cell(6, 4).value, 'Cliente Despacho')
        self.assertEqual(ws.cell(6, 7).value, 'Región Metropolitana de Santiago')
        self.assertEqual(ws.cell(6, 8).value, 'Providencia')
        self.assertEqual(ws.cell(6, 9).value, 'Los Alerces')
        self.assertEqual(ws.cell(6, 10).value, '123')
        self.assertEqual(ws.cell(6, 19).value, 'EXPRESS')
        self.assertEqual(ws.cell(6, 20).value, 'No')

        # Verificar que el pedido cambió de estado a EN_PREPARACION
        p_updated = Pedido.objects.get(email='despacho@example.com')
        self.assertEqual(p_updated.estado, 'EN_PREPARACION')

    def test_api_puntos_blue_express(self):
        """Verifica que el endpoint /api/puntos-blue/ retorne los puntos disponibles en la comuna."""
        response = self.client.get('/api/puntos-blue/?comuna=Santiago')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertGreater(data['total'], 0)
        primer_punto = data['puntos'][0]
        self.assertIn('id', primer_punto)
        self.assertIn('nombre', primer_punto)
        self.assertIn('direccion_completa', primer_punto)

    def test_cotizar_punto_blue_express(self):
        """Verifica que la cotización para PUNTO_BLUE aplique la tarifa reducida oficial."""
        # Cotización normal Punto Blue Santiago (< 19990) -> 2600
        response = self.client.get('/api/cotizar-envio/?comuna=Santiago&tipo_entrega=PUNTO_BLUE')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['costo_envio'], 2600)
        self.assertEqual(data['tipo_entrega'], 'PUNTO_BLUE')

        # Cotización Punto Blue Valparaíso / Viña del Mar -> 3800
        response_vina = self.client.get('/api/cotizar-envio/?comuna=Viña del Mar&tipo_entrega=PUNTO_BLUE')
        self.assertEqual(response_vina.status_code, 200)
        self.assertEqual(response_vina.json()['costo_envio'], 3800)

    def test_exportar_pedidos_blue_express_excluye_puntos_blue(self):
        """Verifica que los pedidos con PUNTO_BLUE NO entren a la planilla de carga masiva de domicilio."""
        Pedido.objects.create(
            nombre_completo='Cliente Punto Excluido',
            rut='19.222.333-4',
            email='excluido@example.com',
            telefono='911223344',
            tipo_entrega='PUNTO_BLUE',
            punto_entrega_id='3167',
            punto_entrega_nombre='Punto Blue Express Good Travel',
            direccion='Sargento aldea 776 (Punto Blue)',
            ciudad='Iquique',
            comuna='Iquique',
            region='Región de Tarapacá',
            costo_envio=4700,
            estado='PAGADO',
            pagado=True,
            empresa_transporte='Blue Express'
        )

        self.client.login(username='admin_bx', password='adminpassword123')
        response = self.client.get('/panel/pedidos/exportar-blue-express/')
        self.assertEqual(response.status_code, 200)

        import io, openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        ws = wb['Carga Masiva']
        nombres_en_hoja = [ws.cell(row, 4).value for row in range(6, ws.max_row + 1)]
        self.assertNotIn('Cliente Punto Excluido', nombres_en_hoja, "Los pedidos con PUNTO_BLUE no deben estar en la carga masiva a domicilio")

    def test_exportar_pedidos_puntos_blue_excel(self):
        """Verifica que la planilla individual de Puntos Blue Express exporte correctamente sus datos."""
        Pedido.objects.create(
            nombre_completo='Cliente Para Gestion Individual',
            rut='17.333.444-5',
            email='individual@example.com',
            telefono='988776655',
            tipo_entrega='PUNTO_BLUE',
            punto_entrega_id='5038',
            punto_entrega_nombre='Punto Blue Express Minimarket El Almacen',
            direccion='TORONTO 3711',
            ciudad='Iquique',
            comuna='Iquique',
            region='Región de Tarapacá',
            costo_envio=4700,
            estado='PAGADO',
            pagado=True,
            empresa_transporte='Blue Express'
        )

        self.client.login(username='admin_bx', password='adminpassword123')
        response = self.client.get('/panel/pedidos/exportar-puntos-blue/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', response['Content-Type'])
        self.assertIn('Planilla_Puntos_Blue_Express', response['Content-Disposition'])

        import io, openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        ws = wb['Puntos Blue Express']
        # Cabeceras
        self.assertEqual(ws.cell(1, 1).value, 'Nº Pedido')
        self.assertEqual(ws.cell(1, 3).value, 'Cliente')
        self.assertEqual(ws.cell(1, 7).value, 'ID Agencia Blue')
        self.assertEqual(ws.cell(1, 8).value, 'Nombre Punto Blue')
        self.assertEqual(ws.cell(1, 9).value, 'Dirección Punto')

        # Buscar fila del pedido
        encontrado = False
        for row in range(2, ws.max_row + 1):
            if ws.cell(row, 3).value == 'Cliente Para Gestion Individual':
                encontrado = True
                self.assertEqual(ws.cell(row, 7).value, '5038')
                self.assertEqual(ws.cell(row, 8).value, 'Punto Blue Express Minimarket El Almacen')
                self.assertEqual(ws.cell(row, 9).value, 'TORONTO 3711')
                break
        self.assertTrue(encontrado, "El pedido con PUNTO_BLUE debe estar presente en la planilla individual de Puntos Blue")

        # Verificar cambio de estado a EN_PREPARACION
        p_updated = Pedido.objects.get(email='individual@example.com')
        self.assertEqual(p_updated.estado, 'EN_PREPARACION')

    def test_envio_gratis_rm_metodo_y_panel(self):
        """Verifica que GRATIS_RM se cotice a $0 cuando cumple condiciones, se filtre y muestre en el panel de pedidos y se exporte en Blue Express."""
        # 1. Cotizar en API sin cumplir monto (< 19.990) -> No permite gratis
        resp_invalido = self.client.get('/api/cotizar-envio/?comuna=Santiago&tipo_entrega=GRATIS_RM')
        self.assertEqual(resp_invalido.status_code, 200)
        self.assertFalse(resp_invalido.json()['permite_gratis_rm'])
        self.assertEqual(resp_invalido.json()['tipo_entrega'], 'ENVIO')

        # Cargar carrito con $25.000 en sesión
        session = self.client.session
        session['carrito'] = {
            str(self.producto.id): {
                'producto_id': self.producto.id,
                'nombre': self.producto.nombre,
                'precio': 25000,
                'cantidad': 1,
                'precio_total': 25000,
                'peso': 0.4
            }
        }
        session.save()

        # Cotizar en API cumpliendo monto (>= 19.990) -> $0 y permite_gratis_rm=True
        response = self.client.get('/api/cotizar-envio/?comuna=Santiago&tipo_entrega=GRATIS_RM')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['permite_gratis_rm'])
        self.assertEqual(data['costo_envio'], 0)
        self.assertEqual(data['tipo_entrega'], 'GRATIS_RM')

        # 2. Crear pedido con GRATIS_RM
        pedido_gratis = Pedido.objects.create(
            nombre_completo='Cliente Gratis RM',
            rut='18.999.888-7',
            email='gratis_rm@example.com',
            telefono='911223344',
            tipo_entrega='GRATIS_RM',
            direccion='Av. Providencia 1234',
            ciudad='Providencia',
            comuna='Providencia',
            region='Región Metropolitana de Santiago',
            costo_envio=0,
            estado='PAGADO',
            pagado=True,
            empresa_transporte='Blue Express'
        )

        # 3. Verificar filtro y visualización en el Panel de Pedidos
        self.client.login(username='admin_bx', password='adminpassword123')
        resp_panel = self.client.get('/panel/pedidos/?tipo_entrega=GRATIS_RM')
        self.assertEqual(resp_panel.status_code, 200)
        self.assertContains(resp_panel, 'Cliente Gratis RM')
        self.assertContains(resp_panel, 'Gratis RM')

        # 4. Verificar detalle de pedido
        resp_detalle = self.client.get(f'/panel/pedidos/{pedido_gratis.id}/')
        self.assertEqual(resp_detalle.status_code, 200)
        self.assertContains(resp_detalle, 'Envío Gratis RM')

        # 5. Verificar exportación masiva de Blue Express incluye GRATIS_RM
        resp_export = self.client.get('/panel/pedidos/exportar-blue-express/?todos=1')
        self.assertEqual(resp_export.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', resp_export['Content-Type'])
        import io, openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(resp_export.content))
        ws = wb.active
        nombres_en_planilla = [ws.cell(r, 4).value for r in range(6, ws.max_row + 1)]
        self.assertIn('Cliente Gratis RM', nombres_en_planilla)

    def test_exportar_pedidos_gratis_rm_excel(self):
        """Verifica la generación de la planilla exclusiva de pedidos con Envío Gratis RM."""
        p_gratis = Pedido.objects.create(
            nombre_completo='Cliente Planilla RM',
            rut='19.555.666-7',
            email='planilla_rm@example.com',
            telefono='988776655',
            tipo_entrega='GRATIS_RM',
            direccion='Av. Vitacura 5000',
            ciudad='Vitacura',
            comuna='Vitacura',
            region='Región Metropolitana de Santiago',
            costo_envio=0,
            estado='PAGADO',
            pagado=True,
            empresa_transporte='Blue Express'
        )

        self.client.login(username='admin_bx', password='adminpassword123')
        resp = self.client.get('/panel/pedidos/exportar-gratis-rm/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', resp['Content-Type'])
        self.assertIn('Planilla_Envios_Gratis_RM', resp['Content-Disposition'])

        import io, openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(resp.content))
        self.assertIn('Envios Gratis RM', wb.sheetnames)
        ws = wb['Envios Gratis RM']
        self.assertEqual(ws.cell(1, 1).value, 'Nº Pedido')
        self.assertEqual(ws.cell(1, 3).value, 'Cliente')
        self.assertEqual(ws.cell(2, 3).value, 'Cliente Planilla RM')
        self.assertEqual(ws.cell(2, 7).value, 'Av. Vitacura 5000')

        # Verificar actualización de estado a EN_PREPARACION
        p_gratis.refresh_from_db()
        self.assertEqual(p_gratis.estado, 'EN_PREPARACION')

    def test_exportar_pedidos_retiro_local_excel(self):
        """Verifica la generación de la planilla para Retiros en Local / Tienda."""
        p_retiro = Pedido.objects.create(
            nombre_completo='Cliente Retiro Tienda',
            rut='16.444.333-2',
            email='retiro_tienda@example.com',
            telefono='977665544',
            tipo_entrega='RETIRO',
            direccion='San Diego 174',
            ciudad='Santiago',
            comuna='Santiago',
            region='Región Metropolitana de Santiago',
            costo_envio=0,
            estado='PAGADO',
            pagado=True
        )

        self.client.login(username='admin_bx', password='adminpassword123')
        resp = self.client.get('/panel/pedidos/exportar-retiro-local/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', resp['Content-Type'])
        self.assertIn('Planilla_Retiro_en_Local', resp['Content-Disposition'])

        import io, openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(resp.content))
        self.assertIn('Retiros en Local', wb.sheetnames)
        ws = wb['Retiros en Local']
        self.assertEqual(ws.cell(1, 1).value, 'Nº Pedido')
        self.assertEqual(ws.cell(1, 3).value, 'Cliente')
        self.assertEqual(ws.cell(1, 7).value, 'Productos para Preparar (Picking)')
        self.assertEqual(ws.cell(1, 14).value, 'Firma / Conforme')
        self.assertEqual(ws.cell(2, 3).value, 'Cliente Retiro Tienda')

        # Verificar actualización de estado a EN_PREPARACION
        p_retiro.refresh_from_db()
        self.assertEqual(p_retiro.estado, 'EN_PREPARACION')

    def test_checkout_compra_menor_umbral_no_permite_gratis_rm(self):
        """Verifica que compras menores a $19.990 no ofrezcan GRATIS_RM en checkout y que en el POST se normalice a ENVIO cobrando la tarifa."""
        from unittest.mock import patch, MagicMock

        # Crear producto de $50 y cargarlo en carrito
        prod_50 = Producto.objects.create(
            categoria=self.categoria,
            nombre="Teclado Barato",
            precio=50,
            stock=10,
            disponible=True
        )
        session = self.client.session
        session['carrito'] = {
            str(prod_50.id): {
                'producto_id': prod_50.id,
                'nombre': prod_50.nombre,
                'precio': 50,
                'cantidad': 1,
                'precio_total': 50,
                'peso': 0.4
            }
        }
        session.save()

        # 1. GET /checkout/ no debe permitir gratis RM ni formatear con puntos en JavaScript
        resp_get = self.client.get('/checkout/')
        self.assertEqual(resp_get.status_code, 200)
        self.assertFalse(resp_get.context['permite_gratis_rm'])
        self.assertEqual(resp_get.context['tipo_entrega_default'], 'ENVIO')
        content = resp_get.content.decode('utf-8')
        self.assertIn('const UMBRAL_GRATIS = 19990;', content)
        self.assertNotIn('const UMBRAL_GRATIS = 19.990;', content)
        self.assertIn('id="btn-entrega-gratis-rm"', content)
        self.assertIn('display: none;', content)

        # 2. POST /checkout/ forzando tipo_entrega='GRATIS_RM' debe normalizarse a 'ENVIO' y cobrar $3.100
        mock_tx = MagicMock()
        mock_tx.create.return_value = {'token': 'test_tok_123', 'url': 'https://webpay.test/pay'}

        with patch('tienda.views.checkout_pagos.get_webpay_transaction', return_value=mock_tx):
            post_data = {
                'nombre_completo': 'Comprador Menor Umbral',
                'rut': '12.345.678-5',
                'email': 'menor@example.com',
                'telefono': '911111111',
                'tipo_entrega': 'GRATIS_RM',
                'region': 'Región Metropolitana de Santiago',
                'comuna': 'Santiago',
                'direccion': 'Calle Falsa 123',
                'terminos_aceptados': 'on'
            }
            resp_post = self.client.post('/checkout/', post_data)
            self.assertEqual(resp_post.status_code, 200)

        # Verificar que el pedido creado en la BD quedó con tipo_entrega='ENVIO' y costo_envio=3100
        pedido = Pedido.objects.get(email='menor@example.com')
        self.assertEqual(pedido.tipo_entrega, 'ENVIO')
        self.assertEqual(pedido.costo_envio, 3100)
        self.assertEqual(pedido.get_total_final(), 3150)


class ContactoFormTests(TestCase):
    def test_api_contacto_exitoso_form_data(self):
        """Verifica que el formulario de contacto con email separado envíe correo y configure reply_to."""
        from django.core import mail
        resp = self.client.post('/api/contacto/', {
            'nombre': 'Carlos Pérez',
            'email': 'carlos@tiendachile.cl',
            'asunto': 'Cotización POS',
            'mensaje': 'Hola, necesito cotizar 5 terminales Smart POS para mi local en Santiago.'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('contacto@rapidassure.cl', email.to)
        self.assertIn('Carlos Pérez', email.subject)
        self.assertIn('Cotización POS', email.subject)
        self.assertEqual(email.reply_to, ['carlos@tiendachile.cl'])
        self.assertIn('carlos@tiendachile.cl', email.body)
        self.assertIn('5 terminales Smart POS', email.body)
        self.assertEqual(len(email.alternatives), 1)
        self.assertEqual(email.alternatives[0][1], 'text/html')
        self.assertIn('Carlos Pérez', email.alternatives[0][0])
        self.assertIn('Cotización POS', email.alternatives[0][0])
        self.assertIn('Nueva Consulta Web', email.alternatives[0][0])

    def test_api_contacto_exitoso_json(self):
        """Verifica que el endpoint procese payloads JSON con email separado."""
        import json
        from django.core import mail
        resp = self.client.post(
            '/api/contacto/',
            data=json.dumps({
                'nombre': 'Andrea Gómez',
                'email': 'andrea@supermercado.cl',
                'asunto': 'Consulta sobre antenas RFID',
                'mensaje': 'Consulta sobre antenas RFID.'
            }),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('contacto@rapidassure.cl', mail.outbox[0].to)
        self.assertEqual(mail.outbox[0].reply_to, ['andrea@supermercado.cl'])

    def test_api_contacto_exige_email_obligatorio(self):
        """Rechaza peticiones si falta el correo del cliente."""
        from django.core import mail
        resp = self.client.post('/api/contacto/', {
            'nombre': 'Carlos Pérez',
            'email': '',
            'asunto': 'Cotización',
            'mensaje': 'Hola'
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertEqual(data['status'], 'error')
        self.assertIn('correo electrónico es obligatorio', data['mensaje'])
        self.assertEqual(len(mail.outbox), 0)

    def test_api_contacto_valida_formato_email(self):
        """Rechaza correos con formato inválido."""
        from django.core import mail
        resp = self.client.post('/api/contacto/', {
            'nombre': 'Carlos Pérez',
            'email': 'formato-invalido-sin-arroba',
            'asunto': 'Cotización',
            'mensaje': 'Hola'
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertEqual(data['status'], 'error')
        self.assertIn('correo electrónico válido', data['mensaje'])
        self.assertEqual(len(mail.outbox), 0)

    def test_index_contiene_modal_y_campos_separados(self):
        """Verifica que el index cargue los campos de email y asunto separados y el modal."""
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'name="email"')
        self.assertContains(resp, 'name="asunto"')
        self.assertContains(resp, 'id="modal-contacto-exito"')
        self.assertContains(resp, 'contacto@rapidassure.cl')

    def test_panel_configuracion_muestra_stats_blue(self):
        """Verifica que panel de configuración muestre el card de Puntos Blue y requiera login."""
        from django.contrib.auth.models import User
        user = User.objects.create_superuser('admin_sync_blue', 'admin@test.cl', 'pass123')
        self.client.login(username='admin_sync_blue', password='pass123')
        resp = self.client.get('/panel/configuracion/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Catálogo de Puntos Blue Express')
        self.assertContains(resp, 'Sincronizar Puntos Blue Express con la API')

    def test_sincronizar_puntos_blue_requiere_staff(self):
        """Usuarios no autenticados no pueden llamar a la sincronización."""
        resp = self.client.post('/panel/configuracion/sincronizar-puntos-blue/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('login', resp.url)

    def test_alerta_compra_confirmada_envia_correos_cliente_y_admin(self):
        """Alerta de compra confirmada envía email al cliente con aviso de seguimiento y a contacto@rapidassure.cl con link al panel."""
        from django.core import mail
        from tienda.emails import enviar_alerta_compra_confirmada
        from tienda.models import LogPedido, Categoria, Producto

        mail.outbox = []

        cat = Categoria.objects.create(nombre='POS Hardware', slug='pos-hw')
        prod = Producto.objects.create(
            categoria=cat,
            nombre='Impresora Térmica 80mm',
            precio=65000,
            stock=10,
            disponible=True
        )

        pedido = Pedido.objects.create(
            nombre_completo='Andrés Morales',
            rut='16.789.123-4',
            email='andres@empresa.cl',
            telefono='911223344',
            tipo_entrega='ENVIO',
            direccion='Moneda 1120, Of 402',
            comuna='Santiago',
            ciudad='Santiago',
            region='Metropolitana de Santiago',
            costo_envio=3500,
            metodo_pago='WEBPAY',
            codigo_autorizacion='998877',
            pagado=True,
            estado='PAGADO'
        )
        ItemPedido.objects.create(
            pedido=pedido,
            producto=prod,
            precio=65000,
            cantidad=1
        )

        enviar_alerta_compra_confirmada(pedido, async_send=False)

        # Se deben enviar al menos 2 correos (cliente y admin)
        self.assertGreaterEqual(len(mail.outbox), 2)

        # Correo cliente
        email_cliente = next(m for m in mail.outbox if 'andres@empresa.cl' in m.to)
        self.assertIn('Compra Confirmada', email_cliente.subject)
        self.assertIn(pedido.codigo_orden, email_cliente.subject)
        self.assertIn('Pronto recibirás el número de seguimiento de tu envío', email_cliente.body)
        self.assertEqual(email_cliente.reply_to, ['contacto@rapidassure.cl'])

        # Correo admin
        email_admin = next(m for m in mail.outbox if any('contacto@rapidassure.cl' in d for d in m.to))
        self.assertIn('Nuevo Pedido Confirmado', email_admin.subject)
        self.assertIn(pedido.codigo_orden, email_admin.subject)
        self.assertIn('Andrés Morales', email_admin.body)
        self.assertIn(f'/panel/pedidos/{pedido.id}/', email_admin.body)

        # Verificar que NO se use el dominio con una sola 's'
        for m in mail.outbox:
            for dest in m.to:
                self.assertNotIn('rapidasure.cl', dest)

        # Verificar LogPedido
        log = LogPedido.objects.filter(pedido_id=pedido.id, accion='CORREO_CONFIRMACION').first()
        self.assertIsNotNone(log)
        self.assertIn('andres@empresa.cl', log.detalles)

    def test_enviar_seguimiento_email_desde_contacto_rapidassure(self):
        """El botón del panel envía correo de seguimiento al cliente desde contacto@rapidassure.cl."""
        from django.core import mail
        from django.contrib.auth.models import User
        from tienda.models import Categoria, Producto, LogPedido

        mail.outbox = []

        user = User.objects.create_superuser('admin_seguimiento', 'admin@test.cl', 'pass123')
        self.client.login(username='admin_seguimiento', password='pass123')

        cat = Categoria.objects.create(nombre='Lectores', slug='lectores')
        prod = Producto.objects.create(
            categoria=cat,
            nombre='Lector Código Barras 2D',
            precio=45000,
            stock=5,
            disponible=True
        )

        pedido = Pedido.objects.create(
            nombre_completo='Valeria Castro',
            rut='17.654.321-0',
            email='valeria@retail.cl',
            telefono='922334455',
            tipo_entrega='ENVIO',
            direccion='Ahumada 341, Local 12',
            comuna='Santiago',
            ciudad='Santiago',
            region='Metropolitana de Santiago',
            empresa_transporte='Blue Express',
            numero_seguimiento='BX-99887766',
            pagado=True,
            estado='ENVIADO'
        )
        ItemPedido.objects.create(
            pedido=pedido,
            producto=prod,
            precio=45000,
            cantidad=1
        )

        resp = self.client.get(f'/panel/pedidos/enviar-seguimiento/{pedido.id}/')
        self.assertRedirects(resp, f'/panel/pedidos/{pedido.id}/')

        # Verificar que se envió un correo
        self.assertEqual(len(mail.outbox), 1)
        email_seg = mail.outbox[0]
        self.assertEqual(email_seg.to, ['valeria@retail.cl'])
        self.assertIn('ya va en camino', email_seg.subject)
        self.assertIn('BX-99887766', email_seg.body)
        self.assertIn('contacto@rapidassure.cl', email_seg.from_email)
        self.assertEqual(email_seg.reply_to, ['contacto@rapidassure.cl'])

        # Verificar log
        log = LogPedido.objects.filter(pedido_id=pedido.id, accion='SEGUIMIENTO').first()
        self.assertIsNotNone(log)
        self.assertIn('BX-99887766', log.detalles)
        self.assertIn('contacto@rapidassure.cl', log.detalles)


