def get_cloudinary_url(image_field_or_url, width=None, quality="auto", format_type="auto"):
    """
    Genera una URL optimizada de Cloudinary manteniendo compatibilidad con
    archivos locales en modo de desarrollo.

    - Reemplaza f_jpg por f_auto (o format_type especificado).
    - Aplica q_auto (o quality especificado).
    - Aplica ancho dinámico (w_{width}) si width se especifica.
    - No fuerza sufijos/extensiones .jpg al final de la URL.
    """
    if not image_field_or_url:
        return ""

    try:
        url = getattr(image_field_or_url, 'url', None)
        if not url:
            url = str(image_field_or_url)
    except Exception:
        try:
            name = getattr(image_field_or_url, 'name', None) or str(image_field_or_url)
            url = f"/media/{name}" if name else ""
        except Exception:
            return ""

    if not url:
        return ""

    # Si no es una URL de Cloudinary (ej: desarrollo local en /media/)
    if 'cloudinary.com' not in url:
        if url.startswith('http://') or url.startswith('https://'):
            if url.startswith('http://'):
                return 'https://' + url[7:]
            return url
        if not url.startswith('/'):
            url = '/' + url
        return url

    # Forzar HTTPS en Cloudinary
    if url.startswith('http://'):
        url = 'https://' + url[7:]

    # Construir segmento de transformaciones
    transformations = [f"f_{format_type}", f"q_{quality}"]
    if width:
        transformations.append(f"w_{width}")
    
    transform_str = ",".join(transformations)

    # Si contiene /upload/ en la URL:
    if '/upload/' in url:
        parts = url.split('/upload/')
        prefix = parts[0] + '/upload/'
        suffix = parts[1]

        # Eliminar transformaciones previas si existen en el primer segmento del sufijo
        first_segment = suffix.split('/')[0]
        if any(p.startswith(('f_', 'q_', 'w_', 'c_', 'h_', 'g_')) for p in first_segment.split(',')):
            rest = "/".join(suffix.split('/')[1:])
            suffix = rest

        url = f"{prefix}{transform_str}/{suffix}"

    return url


import re

def normalizar_telefono_chile(raw_telefono):
    """
    Normaliza cualquier número de teléfono ingresado (móvil o fijo) al formato oficial
    requerido por la planilla de Carga Masiva de Blue Express y las comunicaciones:
    - Celular: 569XXXXXXXX (11 dígitos, ej: 56911111111)
    - Teléfono Fijo: 562XXXXXXX o 56XXXXXXXXX (ej: 562111111)
    """
    if not raw_telefono:
        return ""
    digits = re.sub(r'\D', '', str(raw_telefono).strip())
    if not digits:
        return ""

    # Si ya comienza con prefijo chileno 56
    if digits.startswith('56'):
        return digits

    # Si tiene 9 dígitos
    # - Celular chileno: 9XXXXXXXX -> 569XXXXXXXX
    # - Fijo: 2XXXXXXXX -> 562XXXXXXXX (o código de área de región)
    if len(digits) == 9:
        return f"56{digits}"

    # Si tiene 8 dígitos
    # - Fijo (ej: 21111111 o 2XXXXXXX): 562XXXXXXX
    # - Celular sin el 9 inicial (ej: 87654321): 56987654321
    if len(digits) == 8:
        if digits.startswith(('2', '3', '4', '5', '6', '7')):
            return f"56{digits}"
        return f"569{digits}"

    # Fijo antiguo de 7 dígitos (ej: 2111111)
    if len(digits) == 7:
        if digits.startswith('2'):
            return f"56{digits}"
        return f"562{digits}"

    # Fallback general
    return f"56{digits}"
