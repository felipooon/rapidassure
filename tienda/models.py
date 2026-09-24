import uuid
import unicodedata
from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from .utils import get_cloudinary_url

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    imagen = models.ImageField(upload_to='categorias/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug or slugify(self.nombre) != self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse('categoria', args=[self.slug])

    @property
    def get_imagen_url_absoluta(self):
        return get_cloudinary_url(self.imagen, width=600)

    def get_imagen_url(self, width=600):
        return get_cloudinary_url(self.imagen, width=width)

    @property
    def get_imagen_url_300(self):
        return get_cloudinary_url(self.imagen, width=300)

    @property
    def get_imagen_url_600(self):
        return get_cloudinary_url(self.imagen, width=600)

    @property
    def get_imagen_url_1200(self):
        return get_cloudinary_url(self.imagen, width=1200)

    @property
    def icono_fontawesome(self):
        """Retorna un ícono representativo de FontAwesome según la temática tecnológica."""
        raw = f"{self.slug or ''} {self.nombre or ''}".lower()
        texto = ''.join(c for c in unicodedata.normalize('NFD', raw) if unicodedata.category(c) != 'Mn')

        if any(k in texto for k in ['pos', 'retail', 'caja', 'punto de venta', 'voucher', 'transbank']):
            return 'fa-cash-register'
        elif any(k in texto for k in ['audio', 'bluetooth', 'auricular', 'audifono', 'parlante', 'sonido', 'headphone', 'speaker']):
            return 'fa-headphones'
        elif any(k in texto for k in ['computador', 'pc', 'laptop', 'notebook', 'desktop', 'computacion', 'ordenador', 'servidor']):
            return 'fa-laptop'
        elif any(k in texto for k in ['celular', 'telefono', 'smartphone', 'movil', 'iphone', 'telefonia']):
            return 'fa-mobile-screen-button'
        elif any(k in texto for k in ['tablet', 'ipad']):
            return 'fa-tablet-screen-button'
        elif any(k in texto for k in ['tv', 'television', 'pantalla', 'monitor', 'display', 'proyector', 'video']):
            return 'fa-tv'
        elif any(k in texto for k in ['camara', 'fotografia', 'seguridad', 'vigilancia', 'cctv', 'webcam', 'dvr', 'nvr']):
            return 'fa-camera'
        elif any(k in texto for k in ['gamer', 'gaming', 'juego', 'consola', 'playstation', 'xbox', 'nintendo', 'arcade']):
            return 'fa-gamepad'
        elif any(k in texto for k in ['impresora', 'impresion', 'scanner', 'escaner', 'termica', 'tinta', 'toner', 'boleta']):
            return 'fa-print'
        elif any(k in texto for k in ['reloj', 'smartwatch', 'wearable', 'band']):
            return 'fa-clock'
        elif any(k in texto for k in ['red', 'redes', 'wifi', 'wi-fi', 'router', 'modem', 'switch', 'conectividad', 'fibra', 'ethernet']):
            return 'fa-network-wired'
        elif any(k in texto for k in ['almacenamiento', 'disco', 'ssd', 'hdd', 'usb', 'pendrive', 'memoria', 'micro sd', 'sd']):
            return 'fa-hard-drive'
        elif any(k in texto for k in ['bateria', 'cargador', 'powerbank', 'energia', 'cable', 'alimentacion', 'ups', 'fuente']):
            return 'fa-bolt'
        elif any(k in texto for k in ['teclado', 'mouse', 'periferico', 'gadget', 'accesorio', 'mousepad']):
            return 'fa-keyboard'
        elif any(k in texto for k in ['proteccion', 'garantia', 'seguro', 'funda', 'case', 'mica', 'vidrio']):
            return 'fa-shield-halved'
        elif any(k in texto for k in ['domotica', 'smart home', 'sensor', 'enchufe inteligente', 'iluminacion', 'led']):
            return 'fa-house-signal'
        elif any(k in texto for k in ['componente', 'hardware', 'procesador', 'placa', 'ram', 'tarjeta', 'gpu', 'cpu', 'cooler']):
            return 'fa-microchip'
        elif any(k in texto for k in ['herramienta', 'servicio', 'soporte', 'reparacion', 'mantenimiento', 'repuesto']):
            return 'fa-screwdriver-wrench'
        else:
            return 'fa-microchip'



class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True, null=True)
    descripcion = models.TextField(blank=True)
    precio = models.IntegerField()
    imagen = models.ImageField(upload_to='productos/')

    # Nuevo campo para el control de inventario
    stock = models.PositiveIntegerField(default=0, help_text="Cantidad disponible en inventario")
    disponible = models.BooleanField(default=True)

    # Especificación Técnica Extendida
    tiene_ficha_especie = models.BooleanField(default=True, help_text="Marcar para incluir Especificación Técnica Extendida")
    especie_nombre_comun = models.CharField(max_length=150, blank=True, help_text="Ej: Terminal POS Táctil 15'', Lector Láser 2D")
    especie_nombre_cientifico = models.CharField(max_length=150, blank=True, help_text="Ej: SKU-TEC-900-V2")
    especie_habitat = models.CharField(max_length=200, blank=True, help_text="Ej: Retail, Supermercados, Bodegas y Logística")
    especie_estado_conservacion = models.CharField(max_length=100, blank=True, help_text="Ej: Garantía 24 Meses, Norma IP65")
    especie_dato_curioso = models.TextField(blank=True, help_text="Ficha técnica o características destacadas del equipo")

    def __str__(self):
        return self.nombre
        
    def get_absolute_url(self):
        if self.slug:
            return reverse('producto_detail_slug', args=[self.slug])
        return reverse('producto_detail', args=[str(self.id)])

    def get_imagen_url(self, width=600):
        return get_cloudinary_url(self.imagen, width=width)

    @property
    def get_imagen_url_absoluta(self):
        return get_cloudinary_url(self.imagen, width=1200)

    @property
    def get_imagen_url_300(self):
        return get_cloudinary_url(self.imagen, width=300)

    @property
    def get_imagen_url_600(self):
        return get_cloudinary_url(self.imagen, width=600)

    @property
    def get_imagen_url_1200(self):
        return get_cloudinary_url(self.imagen, width=1200)
    
    # Opcional: un método rápido para saber si hay stock
    def hay_stock(self):
        return self.stock > 0 and self.disponible

    @property
    def promedio_calificacion(self):
        resenas = self.resenas.filter(aprobado=True)
        if not resenas.exists():
            return 0
        total = sum(r.calificacion for r in resenas)
        return round(total / resenas.count(), 1)

    @property
    def todas_las_imagenes(self):
        imgs = []
        if self.imagen:
            imgs.append({
                'id': 'main',
                'url': get_cloudinary_url(self.imagen, width=600),
                'url_300': get_cloudinary_url(self.imagen, width=300),
                'url_600': get_cloudinary_url(self.imagen, width=600),
                'url_1200': get_cloudinary_url(self.imagen, width=1200),
                'get_imagen_url_absoluta': get_cloudinary_url(self.imagen, width=1200),
                'es_principal': True
            })
        for img_extra in self.imagenes_adicionales.all():
            imgs.append({
                'id': img_extra.id,
                'url': get_cloudinary_url(img_extra.imagen, width=600),
                'url_300': get_cloudinary_url(img_extra.imagen, width=300),
                'url_600': get_cloudinary_url(img_extra.imagen, width=600),
                'url_1200': get_cloudinary_url(img_extra.imagen, width=1200),
                'get_imagen_url_absoluta': get_cloudinary_url(img_extra.imagen, width=1200),
                'es_principal': False
            })
        return imgs

    # --- LÓGICA DE AUTOMATIZACIÓN AL GUARDAR ---
    def save(self, *args, **kwargs):
        # 1. Si el stock es 0, forzamos 'disponible' a False (Agotado)
        if self.stock == 0:
            self.disponible = False

        # 2. Autogeneración de Slug único si no tiene uno asignado
        if not self.slug:
            base_slug = slugify(self.nombre) or "producto"
            slug_candidate = base_slug
            counter = 1
            while Producto.objects.filter(slug=slug_candidate).exclude(pk=self.pk).exists():
                slug_candidate = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug_candidate
            
        super().save(*args, **kwargs)


class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes_adicionales')
    imagen = models.ImageField(upload_to='productos/galeria/')
    orden = models.PositiveIntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['orden', 'id']
        verbose_name = 'Imagen de Producto'
        verbose_name_plural = 'Imágenes de Producto'

    def __str__(self):
        return f"Imagen de {self.producto.nombre}"

    def get_imagen_url(self, width=600):
        return get_cloudinary_url(self.imagen, width=width)

    @property
    def get_imagen_url_absoluta(self):
        return get_cloudinary_url(self.imagen, width=1200)

    @property
    def get_imagen_url_300(self):
        return get_cloudinary_url(self.imagen, width=300)

    @property
    def get_imagen_url_600(self):
        return get_cloudinary_url(self.imagen, width=600)

    @property
    def get_imagen_url_1200(self):
        return get_cloudinary_url(self.imagen, width=1200)


    

    
    # =========================
    #   PEDIDOS (aun sin uso)
    # ========================= 

class Cupon(models.Model):
    codigo = models.CharField(max_length=50, unique=True, help_text="Código en mayúsculas (ej: RAPIDA10)")
    descuento_porcentaje = models.IntegerField(default=0, help_text="Porcentaje de descuento (0-100)")
    descuento_monto = models.IntegerField(default=0, help_text="Monto fijo de descuento en CLP")
    activo = models.BooleanField(default=True)
    usos_maximos = models.PositiveIntegerField(null=True, blank=True, help_text="Dejar en blanco para ilimitado")
    usos_actuales = models.PositiveIntegerField(default=0)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.codigo

    def es_valido(self):
        if not self.activo:
            return False, "El cupón no está activo."
        if self.usos_maximos and self.usos_actuales >= self.usos_maximos:
            return False, "El cupón ha alcanzado su límite de usos."
        if self.fecha_expiracion:
            from django.utils import timezone
            if timezone.now() > self.fecha_expiracion:
                return False, "El cupón ha expirado."
        return True, "Cupón válido."

    def calcular_descuento(self, total):
        if self.descuento_porcentaje > 0:
            return int(total * (self.descuento_porcentaje / 100.0))
        elif self.descuento_monto > 0:
            return min(total, self.descuento_monto)
        return 0

    class Meta:
        verbose_name = 'Cupón'
        verbose_name_plural = 'Cupones'


class Pedido(models.Model):
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente de Pago'),
        ('PAGADO', 'Pagado'),
        ('EN_PREPARACION', 'En Preparación'),
        ('ENVIADO', 'Enviado'),
        ('ENTREGADO', 'Entregado'),
        ('CANCELADO', 'Cancelado'),
    )

    TIPO_ENTREGA_CHOICES = (
        ('ENVIO', 'Despacho a Domicilio'),
        ('RETIRO', 'Retiro en Local'),
    )

    # 1. Datos del cliente (Compra como invitado)
    nombre_completo = models.CharField(max_length=200)
    rut = models.CharField(max_length=12, help_text="Formato: 12.345.678-9")
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    tipo_entrega = models.CharField(max_length=20, choices=TIPO_ENTREGA_CHOICES, default='ENVIO', help_text="Forma de entrega seleccionada por el cliente")
    direccion = models.CharField(max_length=250)
    ciudad = models.CharField(max_length=100, default="Puerto Montt")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # 2. Estado y Seguimiento de Envío
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    empresa_transporte = models.CharField(max_length=100, blank=True, default='', help_text="Ej: Starken, Chilexpress")
    numero_seguimiento = models.CharField(max_length=100, blank=True, default='')

    # 3. Cupón de descuento aplicado
    cupon = models.ForeignKey(Cupon, null=True, blank=True, on_delete=models.SET_NULL, related_name='pedidos')
    descuento_aplicado = models.IntegerField(default=0)

    # 4. Datos opcionales de Factura Electrónica
    requiere_factura = models.BooleanField(default=False, help_text="Marcar si el cliente solicitó Factura Electrónica")
    razon_social = models.CharField(max_length=200, blank=True, default='', help_text="Razón social para la factura")
    rut_empresa = models.CharField(max_length=15, blank=True, default='', help_text="RUT de la empresa para la factura")
    giro_comercial = models.CharField(max_length=200, blank=True, default='', help_text="Giro comercial de la empresa")

    @property
    def codigo_orden(self):
        """
        Suma 1100 al ID real. Si el ID en base de datos es 7, 
        para el cliente será el pedido 1107.
        """        
        return str(self.id + 1100)
    
    # 4. Datos de la transacción
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    pagado = models.BooleanField(default=False)
    id_transaccion = models.CharField(max_length=100, blank=True, null=True, help_text="ID de MercadoPago o Webpay")
    token_resena = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=True, blank=True)

    def get_enlace_resena(self):
        if not self.token_resena:
            self.token_resena = uuid.uuid4()
            self.save()
        return f"https://rapidassure.cl/evaluar-compra/{self.token_resena}/"

    class Meta:
        ordering = ['-creado'] # Los pedidos más nuevos saldrán primero en tu panel
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    def __str__(self):
        return f"Pedido #{self.id} - {self.nombre_completo}"

    def get_total_cost(self):
        # Calcula el total sumando el costo de cada item
        return sum(item.get_costo() for item in self.items.all())
        
    def get_total_final(self):
        return max(0, self.get_total_cost() - self.descuento_aplicado)
    
    def confirmar_pago(self):
        # 1. Marcamos el pedido como pagado
        self.pagado = True
        self.save()

        # 2. Recorremos cada item comprado optimizando la consulta
        for item in self.items.select_related('producto').all():
            producto = item.producto
            
            # Restamos la cantidad comprada al stock del producto
            if producto.stock >= item.cantidad:
                producto.stock -= item.cantidad
            else:
                producto.stock = 0 # Evitamos números negativos por seguridad
            
            # 3. Si el stock llega a 0, lo bajamos de la tienda automáticamente
            if producto.stock == 0:
                producto.disponible = False
                
            # Guardamos los cambios en el producto
            producto.save()


class ItemPedido(models.Model):
    # Relaciona el producto específico con el pedido general
    pedido = models.ForeignKey(Pedido, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, related_name='items_pedido', on_delete=models.CASCADE)
    precio = models.IntegerField(help_text="Precio al momento de la compra") 
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"

    def get_costo(self):
        return self.precio * self.cantidad


class ConfiguracionSitio(models.Model):
    mostrar_blog = models.BooleanField(default=False, help_text="Mostrar u ocultar la sección de Blog en la tienda")
    mostrar_resenas = models.BooleanField(default=False, help_text="Mostrar u ocultar la sección de reseñas en los productos")

    class Meta:
        verbose_name = 'Configuración del Sitio'
        verbose_name_plural = 'Configuración del Sitio'

    def __str__(self):
        return "Configuración del Sitio"

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj


class BannerPromocional(models.Model):
    ESTILO_CHOICES = [
        ('dark-navy', 'Dark Navy Metallic'),
        ('vibrant-blue', 'Azul Vibrante'),
        ('gradient-purple', 'Púrpura Deep'),
        ('emerald-green', 'Verde Esmeralda'),
    ]

    ICONO_CHOICES = [
        ('fa-cash-register', 'Caja Registradora / Smart POS'),
        ('fa-headphones', 'Audífonos / Audio Profesional'),
        ('fa-print', 'Impresora Térmica / Insumos'),
        ('fa-microchip', 'Microchip / Gadgets Tech'),
        ('fa-truck-fast', 'Despacho Corporativo'),
        ('fa-shield-halved', 'Garantía / Cobertura Care+'),
        ('fa-bolt', 'Smart / Oferta Relámpago'),
        ('fa-tag', 'Etiqueta de Descuento / Oferta'),
        ('fa-store', 'Tienda / Comercio Retail'),
        ('fa-qrcode', 'Lector QR / Código de Barras'),
        ('fa-mobile-screen', 'POS Móvil Android'),
        ('fa-boxes-stacked', 'Inventario / Accesorios'),
    ]

    titulo = models.CharField(max_length=150, help_text="Título principal del banner")
    subtitulo = models.TextField(help_text="Descripción o detalles promocionales del banner")
    badge = models.CharField(max_length=60, default="OFERTA TECH", help_text="Etiqueta superior (ej: EQUIPAMIENTO DE CAJA, TENDENCIA 2026)")
    badge_gold = models.BooleanField(default=False, help_text="Marcar para mostrar la etiqueta en tono dorado/amarillo")
    url_destino = models.CharField(max_length=250, default="/", help_text="Enlace al hacer clic en el botón (ej: /categoria/smart-pos-retail-tech/)")
    texto_boton = models.CharField(max_length=60, default="Ver Colección", help_text="Texto del botón de acción")
    estilo_fondo = models.CharField(max_length=30, choices=ESTILO_CHOICES, default='dark-navy', help_text="Estilo de gradiente de fondo")
    icono_fontawesome = models.CharField(max_length=50, choices=ICONO_CHOICES, default="fa-cash-register", help_text="Icono FontAwesome decorativo de fondo")
    orden = models.PositiveIntegerField(default=1, help_text="Orden de aparición en la portada")
    activo = models.BooleanField(default=True, help_text="Marcar para mostrar en la portada")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['orden', '-fecha_creacion']
        verbose_name = 'Banner Promocional'
        verbose_name_plural = 'Banners Promocionales'

    def __str__(self):
        return f"{self.titulo} ({self.get_estilo_fondo_display()})"


class BlogPost(models.Model):
    titulo = models.CharField(max_length=250)
    slug = models.SlugField(max_length=270, unique=True, blank=True)
    autor = models.CharField(max_length=100, blank=True, default='Rapidassure', help_text="Nombre del autor del artículo (opcional)")
    resumen = models.TextField(blank=True, help_text="Breve resumen para las tarjetas de blog")
    contenido = models.TextField(help_text="Contenido completo del artículo")
    imagen = models.ImageField(upload_to='blog/', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    publicado = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Artículo del Blog'
        verbose_name_plural = 'Artículos del Blog'

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse('blog_detail', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.titulo) or "articulo"
            candidate = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base_slug}-{counter}"
                counter += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def get_imagen_url(self, width=1200):
        return get_cloudinary_url(self.imagen, width=width)

    @property
    def get_imagen_url_absoluta(self):
        return get_cloudinary_url(self.imagen, width=1200)

    @property
    def get_imagen_url_300(self):
        return get_cloudinary_url(self.imagen, width=300)

    @property
    def get_imagen_url_600(self):
        return get_cloudinary_url(self.imagen, width=600)

    @property
    def get_imagen_url_1200(self):
        return get_cloudinary_url(self.imagen, width=1200)




class ResenaProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='resenas')
    pedido = models.ForeignKey(Pedido, on_delete=models.SET_NULL, null=True, blank=True, related_name='resenas_pedido')
    nombre_cliente = models.CharField(max_length=100)
    email_cliente = models.EmailField(blank=True)
    calificacion = models.IntegerField(default=5, help_text="Calificación de 1 a 5 estrellas")
    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    aprobado = models.BooleanField(default=True)
    comprador_verificado = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Reseña de Producto'
        verbose_name_plural = 'Reseñas de Productos'

    def __str__(self):
        return f"Reseña de {self.nombre_cliente} en {self.producto.nombre} ({self.calificacion}⭐)"


class LogProducto(models.Model):
    ACCION_CHOICES = [
        ('CREACION', '🟢 Creación'),
        ('EDICION', '🔵 Edición'),
        ('TOGGLE', '🟡 Cambio de Estado'),
        ('VENTA', '🛍️ Venta Realizada'),
        ('ELIMINACION', '🔴 Eliminación'),
    ]

    producto_id = models.IntegerField(null=True, blank=True, help_text="ID del producto en la base de datos")
    nombre_producto = models.CharField(max_length=250, help_text="Nombre del producto en el momento del evento")
    accion = models.CharField(max_length=20, choices=ACCION_CHOICES)
    usuario = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    detalles = models.TextField(blank=True, help_text="Detalles o cambios registrados")
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Log de Producto'
        verbose_name_plural = 'Logs de Productos'

    def __str__(self):
        return f"{self.get_accion_display()} - {self.nombre_producto} ({self.fecha.strftime('%d/%m/%Y %H:%M')})"


class LogPedido(models.Model):
    ACCION_CHOICES = [
        ('CREACION', '🟢 Pedido Creado'),
        ('PAGO_OK', '✅ Pago Confirmado'),
        ('ESTADO_CAMBIO', '🚚 Cambio de Estado'),
        ('SEGUIMIENTO', '📦 Datos de Seguimiento'),
        ('ERROR', '⚠️ Error / Fallo de Pago'),
        ('CANCELADO', '❌ Pedido Cancelado'),
    ]

    pedido_id = models.IntegerField(null=True, blank=True, help_text="ID del pedido en la base de datos")
    codigo_orden = models.CharField(max_length=50, help_text="Código de orden del pedido (ej: #1005)")
    cliente_nombre = models.CharField(max_length=150, help_text="Nombre del cliente")
    cliente_email = models.EmailField(blank=True, help_text="Email del cliente")
    accion = models.CharField(max_length=20, choices=ACCION_CHOICES)
    usuario = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, help_text="Usuario admin si la acción fue manual")
    detalles = models.TextField(blank=True, help_text="Detalles técnicos o resumen del evento")
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Log de Pedido'
        verbose_name_plural = 'Logs de Pedidos'

    def __str__(self):
        return f"{self.get_accion_display()} - Pedido #{self.codigo_orden} ({self.cliente_nombre})"


class MetricaDiaria(models.Model):
    fecha = models.DateField(auto_now_add=True, unique=True)
    visitas_humanos = models.PositiveIntegerField(default=0)
    visitas_bots = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Métrica Diaria'
        verbose_name_plural = 'Métricas Diarias'

    def __str__(self):
        return f"Métricas del {self.fecha}"


class MetricaProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='metricas')
    fecha = models.DateField(auto_now_add=True)
    vistas = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-fecha', '-vistas']
        unique_together = ('producto', 'fecha')
        verbose_name = 'Métrica de Producto'
        verbose_name_plural = 'Métricas de Productos'

    def __str__(self):
        return f"{self.producto.nombre} - {self.fecha} ({self.vistas} vistas)"