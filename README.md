# Rapidassure Retail 2.0 (Retail Pro Edition)

Plataforma e-commerce corporativa y centro de operaciones logísticas desarrollado a medida con **Python y Django**. Diseñada específicamente para la comercialización de equipamiento tecnológico, computación, terminales de punto de venta (POS), audio, gaming, periféricos y soluciones operacionales para empresas, PyMEs y clientes particulares en todo Chile.

> **Evolución 2.0:** Reemplazo integral de una tienda anterior en WordPress, logrando una plataforma rápida, segura, sin dependencias de plugins costosos, con experiencia visual premium (*glassmorphism*, responsive móvil optimizado) y automatización logística avanzada para couriers.

---

## 🚀 Características Principales

### 🛒 Tienda y Experiencia de Usuario (Frontend & CRO)
- **Hero Slider Dinámico**: Portada con carrusel de alto impacto visual (*Mundo Digital* y *Retail & Empresas*), optimizado para escritorio y dispositivos móviles sin deformaciones.
- **Catálogo Tecnológico Dinámico**: Filtrado por categorías, búsqueda en tiempo real, ordenamiento por precio y novedades, con indicadores de stock e inventario en vivo.
- **Carrito de Compras Corporativo**: Persistencia en sesión, cálculo de descuentos mediante cupones (`RAPIDA10`) y desglose de subtotales en vivo.
- **Checkout Optimizado en 2 Columnas**:
  - Columna izquierda con validación de datos de cliente, RUT, facturación electrónica (Boleta / Factura) y selección de ubicación.
  - Columna derecha con resumen de compra, desglose transparente de envíos y botón directo de **Transbank Webpay Plus**.
- **Sección Nosotros Corporativa**: Presentación de 4 pilares de valor (*Tecnología*, *Calidad*, *Empresas/Particulares*, *Rapidez y Seguridad*) en tarjetas *glassmorphism* con micro-animaciones *hover* y cita institucional.
- **Sección Contacto & Mapa Interactivo**: Integración de Google Maps con ubicación física (San Diego 174 Local 8, Santiago) y formulario flotante, adaptados en columna vertical para navegación táctil fluida en móviles.
- **Sistema de Reseñas Verificadas**: Enlaces tokenizados de valoración post-compra con insignia de cliente verificado y estrellas.
- **Blog Corporativo**: Artículos de tecnología, retail y guías prácticas.

---

### 🚚 Arquitectura Logística Omnicanal

La plataforma cuenta con 4 modalidades de entrega totalmente integradas en el checkout y en el backend:

1. **🚚 Despacho a Domicilio Blue Express (Estándar):**
   - Cotización en tiempo real basada en la tabla tarifaria oficial de Blue Express para todas las regiones y comunas de Chile.
2. **🎁 Envío Gratis RM (Compras +$19.990):**
   - Método condicional que se activa automáticamente al cumplirse: destino en la Región Metropolitana y subtotal de productos $\ge \$19.990$.
   - Costo de envío bonificado ($0) y retorno automático a tarifa estándar si el cliente cambia de región.
3. **📍 Puntos de Retiro Pick-up Blue Express / Copec:**
   - Base de datos local georreferenciada con **más de 1.000 puntos pick-up y agencias Copec** en todo Chile (`tienda/data/puntos_blue_express.json`).
   - Selector reactivo en checkout con filtrado instantáneo por comuna, mostrando dirección exacta, nombre de la agencia y horarios de atención.
4. **🏪 Retiro en Tienda / Local:**
   - Opción 100% gratuita para retiro en el local comercial de San Diego 174, Santiago Centro.

---

### 🧑‍💻 Panel de Control y Operaciones Logísticas (`/panel/`)

Un centro de mando administrativo pensado para agilizar el despacho y la gestión diaria del negocio:

- **Dashboard de Ventas**: Métricas mensuales, ingresos, pedidos pendientes y ranking de ventas.
- **Suite de Planillas Excel (.xlsx) por Canal de Entrega**:
  - **`🚚 Carga Domicilio`**: Generación masiva con el formato oficial del portal Blue Express PyME (27 columnas) para subida directa sin trabajo manual.
  - **`🎁 Gratis RM`**: Planilla especializada con cabecera verde esmeralda para la flota de reparto local o courier en la Región Metropolitana.
  - **`📍 Puntos Blue`**: Planilla con cabecera morada para la gestión individual de paquetes destinados a agencias Copec / Blue Express.
  - **`🏪 Retiro en Local`**: Hoja de picking y comprobante con espacio para fecha de retiro, RUT y **firma de conformidad del cliente en mesón**.
  - **`📊 Exportar Todo`**: Reporte global maestro de auditoría de ventas.
- **Gestión de Pedidos**: Control de estados (*Pendiente, Pagado, En Preparación, Enviado, Entregado, Cancelado*), asignación de tracking (OT) y envío de correos de seguimiento al cliente.
- **Gestión de Inventario & Stock**: Catálogo de productos, control de existencias y exportación completa a Excel.
- **Gestión de Cupones**: Administración de descuentos por porcentaje o monto fijo.
- **Auditoría & Logs**: Historial de cambios de estado registrado automáticamente en `LogPedido`.

---

## 🛠️ Stack Tecnológico

| Capa | Tecnologías |
| :--- | :--- |
| **Backend** | Python 3.12, Django 5.x, Gunicorn, PostgreSQL / SQLite (local) |
| **Frontend** | HTML5 Semántico, Vanilla CSS (Design Tokens, Glassmorphism, Responsive), JavaScript ES6+ |
| **Integraciones** | Transbank Webpay Plus, Blue Express API / Dataset local, Mercado Pago SDK |
| **Exportación & Datos** | OpenPyXL (generación y formateo de planillas Excel avanzadas) |
| **Recursos & Fuentes** | Font Awesome 6, Google Fonts (Montserrat, Open Sans, Nunito) |
| **Testing** | Django Test Suite (45 pruebas unitarias automatizadas con 100% de éxito) |

---

## 📁 Estructura del Proyecto

```text
rapidasure/
├── Entrega/                   # Plantillas oficiales de couriers (.xlsx)
├── media/                     # Archivos multimedia y fotos de productos
├── static/
│   ├── css/style.css          # Estilos globales, diseño responsive y glassmorphism
│   ├── img/                   # Logotipos, fondos corporativos y badges
│   └── js/                    # Scripts interactivos y utilitarios
├── templates/
│   ├── base.html              # Plantilla maestra con navbar y footer corporativo
│   ├── index.html             # Portada (Hero Slider, Catálogo, Nosotros, Contacto)
│   ├── checkout.html          # Proceso de compra 2 columnas y selección logística
│   └── panel/
│       ├── pedidos.html       # Listado de órdenes y barra de exportación de planillas
│       ├── detalle_pedido.html# Ficha del pedido con mapa y datos de entrega
│       └── ...
├── tienda/
│   ├── comunas_chile.py       # Tarifario oficial y cálculo logístico por región
│   ├── models.py              # Modelos: Pedido, Producto, Cupon, LogPedido, etc.
│   ├── urls.py                # Enrutamiento de URLs públicas y de administración
│   ├── tests.py               # 45 pruebas unitarias automatizadas
│   ├── data/
│   │   └── puntos_blue_express.json # Base de datos local de puntos pick-up
│   ├── management/commands/
│   │   └── actualizar_puntos_blue.py # Comando Django para actualizar agencias
│   └── views/
│       ├── checkout_pagos.py  # Cotización en vivo, checkout y pasarelas
│       ├── panel_admin.py     # Lógica administrativa y exportadores Excel
│       └── tienda_publica.py  # Vistas de catálogo, carrito y contacto
└── manage.py
```

---

## ⚙️ Puesta en Marcha Local

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/felipooon/rapidassure.git
   cd rapidassure
   ```

2. **Crear y activar el entorno virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Linux / macOS
   # venv\Scripts\activate   # En Windows
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Variables de entorno (`.env`)**:
   ```env
   DEBUG=True
   SECRET_KEY=tu_clave_secreta_django
   TRANSBANK_COMMERCE_CODE=tu_codigo_comercio
   TRANSBANK_API_KEY=tu_api_key
   ```

5. **Aplicar migraciones de base de datos**:
   ```bash
   python manage.py migrate
   ```

6. **Ejecutar la suite de pruebas unitarias**:
   ```bash
   python manage.py test
   ```

7. **Iniciar servidor de desarrollo**:
   ```bash
   python manage.py runserver
   ```
   Accede a la tienda en `http://127.0.0.1:8000/` y al panel en `http://127.0.0.1:8000/panel/`.

---

## 📄 Licencia y Derechos

© Rapidassure Retail — Todos los derechos reservados. Desarrollado como plataforma e-commerce de alto rendimiento.