import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rapidassure_app.settings")
django.setup()

from tienda.models import Categoria, Producto, BlogPost, ConfiguracionSitio, ResenaProducto

def run():
    print("Populating Rapidassure Retail database with live tech catalog...")

    # Deshabilitar blog según requerimiento
    config = ConfiguracionSitio.get_solo()
    config.mostrar_blog = False
    config.mostrar_resenas = False
    config.save()

    # Seguridad: no sobrescribir si ya existen productos a menos que se fuerce explícitamente
    if Producto.objects.exists() and "--force" not in sys.argv:
        print("Ya existen productos en la base de datos. Omitiendo seed para proteger tus datos.")
        return

    # Limpiar datos antiguos solo si está vacío o con --force
    Producto.objects.all().delete()
    Categoria.objects.all().delete()
    BlogPost.objects.all().delete()

    # Categorías alineadas a rapidassure.cl
    cat_audio = Categoria.objects.create(
        nombre="Audio & Bluetooth",
        slug="audio-bluetooth",
    )
    cat_pos = Categoria.objects.create(
        nombre="Smart POS & Retail Tech",
        slug="smart-pos-retail-tech",
    )
    cat_gadgets = Categoria.objects.create(
        nombre="Gadgets & Periféricos Tech",
        slug="gadgets-perifericos-tech",
    )
    cat_proteccion = Categoria.objects.create(
        nombre="Protección & Garantías",
        slug="proteccion-garantias",
    )

    productos = [
        # Audio & Bluetooth
        {
            "categoria": cat_audio,
            "nombre": "Audífonos Bluetooth JBL Tune 770NC Cancelación de Ruido",
            "descripcion": "Disfruta del sonido JBL Pure Bass con cancelación de ruido adaptativa Smart Ambient. Hasta 70 horas de autonomía y carga rápida USB-C.",
            "precio": 99990,
            "stock": 15,
            "disponible": True,
            "imagen": "productos/jbl_tune_770nc.jpg"
        },
        {
            "categoria": cat_audio,
            "nombre": "Parlante Bluetooth JBL Go 4 Violeta Ultra Portátil",
            "descripcion": "Sonido JBL Pro de tamaño compacto con resistencia al agua y polvo IP67. Hasta 7 horas de reproducción continua.",
            "precio": 49990,
            "stock": 25,
            "disponible": True,
            "imagen": "productos/jbl_go_4.jpg"
        },
        {
            "categoria": cat_audio,
            "nombre": "Audífonos Inalámbricos Bluetooth Pro Sport IPX7",
            "descripcion": "Audífonos ergonómicos deportivos con aislamiento de ruido pasivo, controles táctiles y estuche de carga inteligente.",
            "precio": 39990,
            "stock": 30,
            "disponible": True,
            "imagen": "productos/audifonos_sport_pro.jpg"
        },
        # Smart POS & Retail Tech
        {
            "categoria": cat_pos,
            "nombre": "Terminal POS Táctil Dual HD Rapid 15''",
            "descripcion": "Sistema POS integral de alta velocidad con pantalla táctil capacitiva HD de 15 pulgadas, procesador Intel Quad-Core y soporte para múltiples periféricos de cobro.",
            "precio": 349990,
            "stock": 10,
            "disponible": True,
            "imagen": "productos/pos_dual_hd.jpg"
        },
        {
            "categoria": cat_pos,
            "nombre": "Terminal POS Móvil Android con Impresora Térmica",
            "descripcion": "Dispositivo portátil de cobro multifuncional con pantalla de 5.5'', conectividad 4G/WiFi, lector NFC e impresora de tickets integrada.",
            "precio": 189990,
            "stock": 20,
            "disponible": True,
            "imagen": "productos/pos_movil_android.jpg"
        },
        # Gadgets & Periféricos Tech
        {
            "categoria": cat_gadgets,
            "nombre": "Lector de Código de Barras 2D/QR Inalámbrico Industrial",
            "descripcion": "Scanner de código de barras 1D/2D y QR de alta precisión. Conexión inalámbrica de hasta 50 metros con base cargadora USB.",
            "precio": 64990,
            "stock": 40,
            "disponible": True,
            "imagen": "productos/scanner_2d_qr.jpg"
        },
        {
            "categoria": cat_gadgets,
            "nombre": "Cargador Rápido GaN 65W Multi-Puerto USB-C / USB-A",
            "descripcion": "Tecnología GaN ultra eficiente para carga ultra rápida simultánea de laptops, smartphones y terminales POS.",
            "precio": 34990,
            "stock": 35,
            "disponible": True,
            "imagen": "productos/cargador_gan_65w.jpg"
        },
        {
            "categoria": cat_gadgets,
            "nombre": "Soporte Ajustable Ergonómico para Tablet & POS",
            "descripcion": "Base de aluminio premium antideslizante con rotación de 360 grados para mostradores y atención de público.",
            "precio": 29990,
            "stock": 40,
            "disponible": True,
            "imagen": "productos/soporte_tablet_pos.jpg"
        },
        # Protección & Garantías
        {
            "categoria": cat_proteccion,
            "nombre": "Plan de Cobertura Extendida RapidAssure Care+ (12 Meses)",
            "descripcion": "Servicio de reemplazo express inmediato en 24h, soporte técnico prioritario 24/7 y cobertura total contra fallas operacionales.",
            "precio": 45000,
            "stock": 999,
            "disponible": True,
            "imagen": "productos/cobertura_rapidassure_care.jpg"
        },
        {
            "categoria": cat_proteccion,
            "nombre": "Respaldo de Energía UPS 1500VA para Cajas & Equipos Tech",
            "descripcion": "Unidad de alimentación ininterrumpida que protege tus terminales de cobro y servidores ante cortes de luz y variaciones de voltaje.",
            "precio": 129990,
            "stock": 15,
            "disponible": True,
            "imagen": "productos/ups_1500va.jpg"
        }
    ]

    prods_map = {}
    for p in productos:
        created_prod = Producto.objects.create(**p)
        prods_map[created_prod.nombre] = created_prod

    # Reseñas alineadas a rapidassure.cl
    ResenaProducto.objects.all().delete()

    resenas = [
        {
            "producto": prods_map["Terminal POS Táctil Dual HD Rapid 15''"],
            "nombre_cliente": "Patricio M. — Gerente de Operaciones Retail",
            "email_cliente": "operaciones@retail-santiago.cl",
            "calificacion": 5,
            "comentario": "Excelente rendimiento en nuestras cajas de alto flujo. La velocidad transaccional y la estabilidad del equipo redujeron nuestros tiempos de espera en caja en más de un 35%.",
            "aprobado": True,
            "comprador_verificado": True
        },
        {
            "producto": prods_map["Terminal POS Móvil Android con Impresora Térmica"],
            "nombre_cliente": "Felipe A. — Cadena Minimarket Express",
            "email_cliente": "felipe@expressmarket.cl",
            "calificacion": 5,
            "comentario": "Implementamos los POS móviles en nuestras 4 sucursales para cobro rápido en fila. La batería dura toda la jornada y la impresora térmica integrada emite tickets al instante.",
            "aprobado": True,
            "comprador_verificado": True
        },
        {
            "producto": prods_map["Lector de Código de Barras 2D/QR Inalámbrico Industrial"],
            "nombre_cliente": "Constanza R. — Jefa de Logística & Inventarios",
            "email_cliente": "logistica@solucionesretail.cl",
            "calificacion": 5,
            "comentario": "Escaneo instantáneo de códigos QR y de barras 1D/2D, incluso en pantallas o etiquetas con cierto desgaste. La conexión inalámbrica tiene un alcance impecable en mostrador y bodega.",
            "aprobado": True,
            "comprador_verificado": True
        },
        {
            "producto": prods_map["Respaldo de Energía UPS 1500VA para Cajas & Equipos Tech"],
            "nombre_cliente": "Roberto V. — Jefe de TI & Infraestructura",
            "email_cliente": "ti@supermercados-sur.cl",
            "calificacion": 5,
            "comentario": "Protección clave para mantener operativas las cajas registradoras durante microcortes de energía o caídas de tensión. Evita la pérdida de datos de ventas.",
            "aprobado": True,
            "comprador_verificado": True
        },
        {
            "producto": prods_map["Plan de Cobertura Extendida RapidAssure Care+ (12 Meses)"],
            "nombre_cliente": "Mariana S. — Administradora de Tienda",
            "email_cliente": "administracion@tiendas-ms.cl",
            "calificacion": 5,
            "comentario": "El respaldo de RapidAssure es fantástico. Tuvimos un imprevisto técnico y la gestión de soporte express nos entregó un reemplazo en menos de 24 horas.",
            "aprobado": True,
            "comprador_verificado": True
        }
    ]

    for r in resenas:
        ResenaProducto.objects.create(**r)

    print("Rapidassure Retail database seeded successfully!")

if __name__ == "__main__":
    run()
