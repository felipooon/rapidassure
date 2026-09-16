# Rapidassure Retail

Plataforma e-commerce corporativa y panel de gestión integral desarrollada con Python y Django, diseñada para la comercialización de equipamiento tecnológico para comercio, terminales de punto de venta (POS), escáneres, soluciones de protección y garantías extendidas para la industria del retail.

---

## Características Principales

### 🛒 Tienda y Experiencia de Usuario
- **Catálogo Dinámico de Soluciones Retail**: Filtrado por categorías de tecnología y protección, ordenamiento por precio, novedades e indicadores de stock en tiempo real.
- **Carrito de Compras Corporativo**: Persistencia en sesión, modal interactivo con cálculo de descuentos mediante cupones (`RAPIDA10`) y desglose de totales.
- **Proceso de Checkout Seguro**: Validación de RUT corporativo/personal, dirección de despacho para sucursales, integración con pasarela de pagos Mercado Pago y generación de órdenes únicas.
- **Sistema de Reseñas Verificadas**: Enlaces tokenizados para evaluación de compras y equipamiento con distinción de cliente verificado y calificación por estrellas.
- **Blog Novedades & Publicaciones Corporativas**: Publicación de noticias sobre tecnología retail, coberturas de garantía y guías operacionales.
- **Páginas de Error Personalizadas**: Vistas corporativas para errores 404 y 500.

### 🧑‍💻 Panel de Administración Personalizado (`/panel/`)
- **Dashboard Ejecutivo**: Métricas de ventas mensuales, control de pedidos pendientes/pagados, alertas de stock agotado y ranking de productos más vendidos.
- **Gestión de Inventario**:
  - Filtros por categoría y estado de disponibilidad.
  - Exportación de catálogo completo a Excel (`.xlsx`).
  - Generador de enlaces de valoración ⭐ con accesos directos para copiar o enviar por WhatsApp.
- **Gestión de Pedidos y Despachos**: Control de estados (Pendiente, Pagado, Enviado, Entregado, Cancelado), empresa de transporte, número de seguimiento y envío automático de correos de despacho.
- **Gestión de Cupones**: Creación de cupones de descuento corporativos por porcentaje o monto fijo.
- **Moderación de Reseñas y Blog**: Editor de publicaciones institucionales y moderación de testimonios de clientes.
- **Guía del Panel**: Manual de uso integrado en `/panel/guia/`.

---

## Tecnologías Utilizadas

- **Backend**: Python, Django, Gunicorn, PostgreSQL, `dj-database-url`.
- **Frontend**: HTML5, Vanilla CSS (Diseño responsivo y Glassmorphism), JavaScript (ES6+), Font Awesome, Google Fonts (Montserrat, Open Sans).
- **Integraciones & Herramientas**: Mercado Pago SDK, WhiteNoise (Gestión de archivos estáticos en producción), OpenPyXL (Reportes Excel).
- **SEO**: Sitemap XML dinámico (`django.contrib.sitemaps`) y configuración de `robots.txt`.

---

## Estructura de Rutas Principales

### Públicas
- `/` — Portada y soluciones destacadas.
- `/categoria/<slug>/` — Catálogo filtrado por categoría.
- `/producto/<slug>/` — Detalle del producto y reseñas verificadas.
- `/ver-carrito/` / `/checkout/` — Carrito de compras y proceso de pago.
- `/pedido-confirmado/<id>/` — Confirmación y resumen de la compra.
- `/blog/` / `/blog/<slug>/` — Artículos del blog corporativo.
- `/evaluar-compra/<token>/` — Formulario de evaluación tokenizado.

### Administración
- `/panel/` — Dashboard del panel de administración.
- `/panel/productos/` — Gestión de inventario y generador de enlaces de reseña.
- `/panel/pedidos/` — Control de ventas y envíos.
- `/panel/cupones/` — Administración de descuentos.
- `/panel/blog/` — Editor y lista de artículos.
- `/panel/guia/` — Manual del panel de administración.
- `/admin/` — Django Admin nativo para auditoría y logs.

---

## Configuración e Instalación Local

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/empresa/rapidasure.git
   cd rapidasure
   ```

2. **Crear y activar entorno virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Linux/macOS
   # venv\Scripts\activate   # En Windows
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno (`.env`)**:
   ```env
   DEBUG=True
   SECRET_KEY=tu_secret_key
   MERCADOPAGO_ACCESS_TOKEN=tu_access_token
   ```

5. **Ejecutar migraciones e iniciar servidor**:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

---

## Licencia & Derechos

Rapidassure Retail — Todos los derechos reservados.