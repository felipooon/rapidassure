from .carrito import Carrito
from .models import Categoria, ConfiguracionSitio

def carrito_global(request):
    """Procesador de contexto global para el Carrito de Compras"""
    return {
        'carrito': Carrito(request)
    }

def configuracion_sitio(request):
    """Procesador de contexto global para tener acceso a config_sitio en todas las plantillas HTML"""
    try:
        config = ConfiguracionSitio.get_solo()
    except Exception:
        config = None
    return {
        'config_sitio': config
    }

def categorias_global(request):
    """Procesador de contexto global para tener acceso a categorias_globales en la Navbar y menús"""
    try:
        return {
            'categorias_globales': Categoria.objects.all()
        }
    except Exception:
        return {
            'categorias_globales': []
        }