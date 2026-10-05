from django import template
from ..utils import get_cloudinary_url

register = template.Library()

@register.filter
def cloudinary_url(image_field_or_url, width=None):
    """
    Filtro de plantilla para formatear URLs optimizadas de Cloudinary.
    Uso en template: {{ producto.imagen|cloudinary_url:600 }}
    """
    if width is not None:
        try:
            width = int(width)
        except (ValueError, TypeError):
            width = None

    return get_cloudinary_url(image_field_or_url, width=width)


@register.filter(name='formato_miles')
def formato_miles(valor):
    """
    Formatea números con separador de miles chileno usando punto (ej: 5841 -> 5.841).
    """
    if valor is None or valor == '':
        return '0'
    try:
        num = int(round(float(valor)))
        return f"{num:,}".replace(',', '.')
    except (ValueError, TypeError):
        return str(valor)
