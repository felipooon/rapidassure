from .carrito import Carrito
from .deseos import Deseos
from .models import Categoria, ConfiguracionSitio, BannerPromocional

def carrito_global(request):
    """Procesador de contexto global para el Carrito de Compras"""
    try:
        return {
            'carrito': Carrito(request)
        }
    except Exception:
        return {
            'carrito': None
        }

def deseos_global(request):
    """Procesador de contexto global para la Lista de Deseos"""
    try:
        deseos_obj = Deseos(request)
        deseos_ids = [int(k) for k in deseos_obj.deseos.keys() if str(k).isdigit()]
        return {
            'deseos': deseos_obj,
            'deseos_ids': deseos_ids
        }
    except Exception:
        return {
            'deseos': None,
            'deseos_ids': []
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

def banners_global(request):
    """Procesador de contexto global para tener acceso a banners_promocionales en la portada"""
    try:
        return {
            'banners_promocionales': BannerPromocional.objects.filter(activo=True)
        }
    except Exception:
        return {
            'banners_promocionales': []
        }