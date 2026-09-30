"""
Módulo de Coberturas y Tarifario Blue Express para Rapidassure.
Contiene las 16 Regiones de Chile y sus 346 Comunas oficiales,
con tarifas zonales estimadas según el tarifario Blue Express Pyme (origen: Santiago).
"""

# Umbral para despacho gratuito exclusivo RM
UMBRAL_ENVIO_GRATIS = 19990

REGIONES_Y_COMUNAS = {
    "Región Metropolitana de Santiago": [
        "Cerrillos", "Cerro Navia", "Conchalí", "El Bosque", "Estación Central",
        "Huechuraba", "Independencia", "La Cisterna", "La Florida", "La Granja",
        "La Pintana", "La Reina", "Las Condes", "Lo Barnechea", "Lo Espejo",
        "Lo Prado", "Macul", "Maipú", "Ñuñoa", "Pedro Aguirre Cerda",
        "Peñalolén", "Providencia", "Pudahuel", "Quilicura", "Quinta Normal",
        "Recoleta", "Renca", "San Joaquín", "San Miguel", "San Ramón",
        "Santiago", "Vitacura", "Puente Alto", "Pirque", "San José de Maipo",
        "San Bernardo", "Buin", "Calera de Tango", "Paine", "Colina",
        "Lampa", "Tiltil", "Melipilla", "Alhué", "Curacaví",
        "María Pinto", "San Pedro", "Talagante", "El Monte", "Isla de Maipo",
        "Padre Hurtado", "Peñaflor"
    ],
    "Región de Valparaíso": [
        "Valparaíso", "Casablanca", "Concón", "Juan Fernández", "Puchuncaví",
        "Quintero", "Viña del Mar", "Isla de Pascua", "Los Andes", "Calle Larga",
        "Rinconada", "San Esteban", "La Ligua", "Cabildo", "Papudo",
        "Petorca", "Zapallar", "Quillota", "Calera", "Hijuelas",
        "La Cruz", "Nogales", "San Antonio", "Algarrobo", "Cartagena",
        "El Quisco", "El Tabo", "Santo Domingo", "San Felipe", "Catemu",
        "Llaillay", "Panquehue", "Putaendo", "Santa María", "Quilpué",
        "Limache", "Olmué", "Villa Alemana"
    ],
    "Región del Libertador Gral. Bernardo O'Higgins": [
        "Rancagua", "Codegua", "Coinco", "Coltauco", "Doñihue",
        "Graneros", "Las Cabras", "Machalí", "Malloa", "Mostazal",
        "Olivar", "Peumo", "Pichidegua", "Quinta de Tilcoco", "Rengo",
        "Requínoa", "San Vicente", "Pichilemu", "La Estrella", "Litueche",
        "Marchihue", "Navidad", "Paredones", "San Fernando", "Chépica",
        "Chimbarongo", "Lolol", "Nancagua", "Palmilla", "Peralillo",
        "Placilla", "Pumanque", "Santa Cruz"
    ],
    "Región de Coquimbo": [
        "La Serena", "Coquimbo", "Andacollo", "La Higuera", "Paiguano",
        "Vicuña", "Illapel", "Canela", "Los Vilos", "Salamanca",
        "Ovalle", "Combarbalá", "Monte Patria", "Punitaqui", "Río Hurtado"
    ],
    "Región del Maule": [
        "Talca", "Constitución", "Curepto", "Empedrado", "Maule",
        "Pelarco", "Pencahue", "Río Claro", "San Clemente", "San Rafael",
        "Cauquenes", "Chanco", "Pelluhue", "Curicó", "Hualañé",
        "Licantén", "Molina", "Rauco", "Romeral", "Sagrada Familia",
        "Teno", "Vichuquén", "Linares", "Colbún", "Longaví",
        "Parral", "Retiro", "San Javier", "Villa Alegre", "Yerbas Buenas"
    ],
    "Región de Ñuble": [
        "Chillán", "Bulnes", "Cobquecura", "Coelemu", "Coihueco",
        "Chillán Viejo", "El Carmen", "Ninhue", "Ñiquén", "Pemuco",
        "Pinto", "Portezuelo", "Quillón", "Quirihue", "Ránquil",
        "San Carlos", "San Fabián", "San Ignacio", "San Nicolás", "Treguaco",
        "Yungay"
    ],
    "Región del Biobío": [
        "Concepción", "Coronel", "Chiguayante", "Florida", "Hualqui",
        "Lota", "Penco", "San Pedro de la Paz", "Santa Juana", "Talcahuano",
        "Tomé", "Hualpén", "Lebu", "Arauco", "Cañete",
        "Contulmo", "Curanilahue", "Los Álamos", "Tirúa", "Los Ángeles",
        "Antuco", "Cabrero", "Laja", "Mulchén", "Nacimiento",
        "Negrete", "Quilaco", "Quilleco", "San Rosendo", "Santa Bárbara",
        "Tucapel", "Yumbel", "Alto Biobío"
    ],
    "Región de La Araucanía": [
        "Temuco", "Carahue", "Cunco", "Curarrehue", "Freire",
        "Galvarino", "Gorbea", "Lautaro", "Loncoche", "Melipeuco",
        "Nueva Imperial", "Padre Las Casas", "Perquenco", "Pitrufquén", "Pucón",
        "Saavedra", "Teodoro Schmidt", "Toltén", "Vilcún", "Villarrica",
        "Cholchol", "Angol", "Collipulli", "Curacautín", "Ercilla",
        "Lonquimay", "Los Sauces", "Lumaco", "Purén", "Renaico",
        "Traiguén", "Victoria"
    ],
    "Región de Los Ríos": [
        "Valdivia", "Corral", "Lanco", "Los Lagos", "Máfil",
        "Mariquina", "Paillaco", "Panguipulli", "La Unión", "Futrono",
        "Lago Ranco", "Río Bueno"
    ],
    "Región de Los Lagos": [
        "Puerto Montt", "Calbuco", "Cochamó", "Fresia", "Frutillar",
        "Los Muermos", "Llanquihue", "Maullín", "Puerto Varas", "Castro",
        "Ancud", "Chonchi", "Curaco de Vélez", "Dalcahue", "Puqueldón",
        "Queilén", "Quellón", "Quemchi", "Quinchao", "Osorno",
        "Puerto Octay", "Purranque", "Puyehue", "Río Negro", "San Juan de la Costa",
        "San Pablo", "Chaitén", "Futaleufú", "Hualaihué", "Palena"
    ],
    "Región de Atacama": [
        "Copiapó", "Caldera", "Tierra Amarilla", "Chañaral", "Diego de Almagro",
        "Vallenar", "Alto del Carmen", "Freirina", "Huasco"
    ],
    "Región de Antofagasta": [
        "Antofagasta", "Mejillones", "Sierra Gorda", "Taltal", "Calama",
        "Ollagüe", "San Pedro de Atacama", "Tocopilla", "María Elena"
    ],
    "Región de Tarapacá": [
        "Iquique", "Alto Hospicio", "Pozo Almonte", "Camiña", "Colchane",
        "Huara", "Pica"
    ],
    "Región de Arica y Parinacota": [
        "Arica", "Camarones", "Putre", "General Lagos"
    ],
    "Región de Aysén del Gral. Carlos Ibáñez del Campo": [
        "Coyhaique", "Lago Verde", "Aysén", "Cisnes", "Guaitecas",
        "Cochrane", "O'Higgins", "Tortel", "Chile Chico", "Río Ibáñez"
    ],
    "Región de Magallanes y de la Antártica Chilena": [
        "Punta Arenas", "Laguna Blanca", "Río Verde", "San Gregorio", "Cabo de Hornos",
        "Antártica", "Porvenir", "Primavera", "Timaukel", "Natales",
        "Torres del Paine"
    ]
}

# Comunas RM que se consideran periféricas/rurales con costo levemente mayor
RM_PERIFERICAS = {
    "colina", "lampa", "tiltil", "pirque", "san jose de maipo", "san josé de maipo",
    "buin", "calera de tango", "paine", "melipilla", "alhue", "alhué",
    "curacavi", "curacaví", "maria pinto", "maría pinto", "san pedro",
    "talagante", "el monte", "isla de maipo", "padre hurtado", "penaflor", "peñaflor"
}

import re

def normalizar_texto(texto):
    """Limpia acentos y minúsculas para comparaciones seguras."""
    if not texto:
        return ""
    texto = texto.strip().lower()
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n',
        'ü': 'u'
    }
    for orig, rep in reemplazos.items():
        texto = texto.replace(orig, rep)
    return texto

def obtener_region_de_comuna(comuna_nombre):
    """Encuentra la región oficial dada una comuna."""
    comuna_norm = normalizar_texto(comuna_nombre)
    for region, comunas in REGIONES_Y_COMUNAS.items():
        for c in comunas:
            if normalizar_texto(c) == comuna_norm:
                return region
    return "Región Metropolitana de Santiago"

REGIONES_EXACTAS_BLUE_EXPRESS = [
    "Región Metropolitana de Santiago",
    "Región de Aysén del Gral. Carlos Ibañez del Campo",
    "Región de Antofagasta",
    "Región de Arica y Parinacota",
    "Región de Atacama",
    "Región de Coquimbo",
    "Región de Magallanes y de la Antártica Chilena",
    "Región de Tarapacá",
    "Región de Valparaíso",
    "Región de la Araucanía",
    "Región de los Lagos",
    "Región de los Ríos",
    "Región de Ñuble",
    "Región del Biobío",
    "Región del Libertador Gral. Bernardo O'Higgins",
    "Región del Maule"
]

def normalizar_region_blue_express(region_nombre):
    """Retorna el nombre exacto de región esperado por la plantilla de Blue Express."""
    if not region_nombre:
        return "Región Metropolitana de Santiago"
    norm = normalizar_texto(region_nombre)
    for reg in REGIONES_EXACTAS_BLUE_EXPRESS:
        if normalizar_texto(reg) == norm:
            return reg
    if 'metropolitana' in norm or 'santiago' in norm:
        return "Región Metropolitana de Santiago"
    if 'araucania' in norm:
        return "Región de la Araucanía"
    if 'lagos' in norm:
        return "Región de los Lagos"
    if 'rios' in norm:
        return "Región de los Ríos"
    if 'aysen' in norm or 'ibanez' in norm:
        return "Región de Aysén del Gral. Carlos Ibañez del Campo"
    if 'magallanes' in norm or 'antartica' in norm:
        return "Región de Magallanes y de la Antártica Chilena"
    if 'ohiggins' in norm or "o'higgins" in norm:
        return "Región del Libertador Gral. Bernardo O'Higgins"
    return "Región Metropolitana de Santiago"

def normalizar_comuna_blue_express(comuna_nombre):
    """Ajusta nombres de comuna con particularidades en el catálogo de Blue Express."""
    if not comuna_nombre:
        return "Santiago Centro"
    norm = normalizar_texto(comuna_nombre)
    if norm in ('santiago', 'santiago centro'):
        return "Santiago Centro"
    if 'ohiggins' in norm or "o'higgins" in norm:
        return "O’higgins"
    return comuna_nombre.strip()

def parsear_direccion_chilena(direccion):
    """
    Separa una dirección en calle, número de domicilio, departamento/oficina y ayuda.
    Cumple con el formato de Carga Masiva de Blue Express.
    """
    if not direccion:
        return ("", "S/N", "", "")
    dir_str = direccion.strip()
    depto = ""
    depto_patterns = [
        r'(?:depto|dpto|departamento|oficina|of|of\.|block|piso)\s*[:#]?\s*([a-zA-Z0-9\-]+)',
        r'#\s*([a-zA-Z0-9\-]+)'
    ]
    for pattern in depto_patterns:
        match = re.search(pattern, dir_str, re.IGNORECASE)
        if match:
            depto = match.group(1).strip()
            dir_str = (dir_str[:match.start()] + dir_str[match.end():]).strip().rstrip(',').strip()
            break

    num_match = re.search(r'\b(\d+[a-zA-Z]?)\b(?=[^\d]*$)', dir_str)
    if num_match:
        numero = num_match.group(1)
        calle = dir_str[:num_match.start()].strip().rstrip(',').strip()
        resto = dir_str[num_match.end():].strip().lstrip(',').strip()
        if resto and not depto:
            depto = resto
    else:
        calle = dir_str
        numero = "S/N"

    if not calle:
        calle = direccion
        numero = "S/N"

    return (calle, numero, depto, "")

# =========================================================================
# TARIFARIO OFICIAL BLUE EXPRESS PYME (CON ENTREGA A DOMICILIO - CON IVA)
# =========================================================================
# Tallas:
#   XS: hasta 0.5 kg
#   S:  hasta 3.0 kg
#   M:  hasta 6.0 kg
#   L:  hasta 20.0 kg
#
# Zonas (desde origen Santiago):
#   - RM (Misma zona y región):           XS: $3.100 | S: $4.200 | M: $4.800 | L: $5.400
#   - Centro (Copiapó a Puerto Montt):    XS: $4.300 | S: $5.600 | M: $7.300 | L: $9.200
#   - Extremo (Arica, Iquique, Aysén,
#              Magallanes y Punta Arenas): XS: $5.200 | S: $9.500 | M: $14.500 | L: $17.000
# =========================================================================

# Tarifas con Entrega a Domicilio (con IVA)
TARIFAS_BLUE_EXPRESS = {
    'XS': {'RM': 3100, 'CENTRO': 4300, 'EXTREMO': 5200},
    'S':  {'RM': 4200, 'CENTRO': 5600, 'EXTREMO': 9500},
    'M':  {'RM': 4800, 'CENTRO': 7300, 'EXTREMO': 14500},
    'L':  {'RM': 5400, 'CENTRO': 9200, 'EXTREMO': 17000},
}

# Tarifas con Entrega Fuera de Casa (Punto Blue Express / Copec - con IVA)
TARIFAS_BLUE_EXPRESS_PUNTO = {
    'XS': {'RM': 2600, 'CENTRO': 3800, 'EXTREMO': 4700},
    'S':  {'RM': 3700, 'CENTRO': 5100, 'EXTREMO': 9000},
    'M':  {'RM': 4300, 'CENTRO': 6800, 'EXTREMO': 14000},
    'L':  {'RM': 4900, 'CENTRO': 8700, 'EXTREMO': 16500},
}

REGIONES_EXTREMO = {
    "Región de Arica y Parinacota",
    "Región de Tarapacá",
    "Región de Antofagasta",
    "Región de Aysén del Gral. Carlos Ibáñez del Campo",
    "Región de Magallanes y de la Antártica Chilena"
}

def determinar_talla_peso(peso_kg):
    try:
        p = float(peso_kg)
    except (ValueError, TypeError):
        p = 0.40

    if p <= 0.5:
        return 'XS'
    elif p <= 3.0:
        return 'S'
    elif p <= 6.0:
        return 'M'
    else:
        return 'L'

def obtener_zona_blue_express(region):
    if region == "Región Metropolitana de Santiago":
        return 'RM'
    if region in REGIONES_EXTREMO:
        return 'EXTREMO'
    return 'CENTRO'

def obtener_tarifa_blue_express(comuna_nombre, peso_kg=0.40):
    region = obtener_region_de_comuna(comuna_nombre)
    zona = obtener_zona_blue_express(region)
    talla = determinar_talla_peso(peso_kg)
    return TARIFAS_BLUE_EXPRESS.get(talla, TARIFAS_BLUE_EXPRESS['XS'])[zona]

def obtener_tarifa_blue_express_punto(comuna_nombre, peso_kg=0.40):
    """Tarifa reducida para entrega fuera de casa en Punto Blue Express / Copec."""
    region = obtener_region_de_comuna(comuna_nombre)
    zona = obtener_zona_blue_express(region)
    talla = determinar_talla_peso(peso_kg)
    return TARIFAS_BLUE_EXPRESS_PUNTO.get(talla, TARIFAS_BLUE_EXPRESS_PUNTO['XS'])[zona]

def obtener_tarifa_base_comuna(comuna_nombre):
    """Alias compatible con la tarifa base estándar (Talla XS)"""
    return obtener_tarifa_blue_express(comuna_nombre, 0.40)

def calcular_costo_envio(comuna_nombre, total_carrito=0, peso_kg=0.40, tipo_entrega='ENVIO'):
    """
    Calcula el costo final de envío considerando las alternativas disponibles:
    1. RETIRO: Siempre $0 (Retiro en Local).
    2. GRATIS_RM: $0 si cumple condiciones (Región Metropolitana y compra >= $19.990).
    3. PUNTO_BLUE: Tarifa reducida oficial Punto Blue Express / Copec.
    4. ENVIO: Tarifa oficial entrega a domicilio Blue Express según peso y zona.
    """
    if tipo_entrega == 'RETIRO':
        return 0

    try:
        total = int(total_carrito)
    except (ValueError, TypeError):
        total = 0

    region = obtener_region_de_comuna(comuna_nombre)

    if tipo_entrega == 'GRATIS_RM':
        if region == "Región Metropolitana de Santiago" and total >= UMBRAL_ENVIO_GRATIS:
            return 0
        return obtener_tarifa_blue_express(comuna_nombre, peso_kg)

    if tipo_entrega == 'PUNTO_BLUE':
        return obtener_tarifa_blue_express_punto(comuna_nombre, peso_kg)

    return obtener_tarifa_blue_express(comuna_nombre, peso_kg)


# Cache en memoria para puntos Blue Express
_CACHE_PUNTOS_BLUE = None

def cargar_puntos_blue_express():
    """Carga y agrupa por comuna normalizada los puntos de retiro Blue Express desde el archivo local JSON."""
    global _CACHE_PUNTOS_BLUE
    if _CACHE_PUNTOS_BLUE is not None:
        return _CACHE_PUNTOS_BLUE

    import os
    import json
    from django.conf import settings

    json_path = os.path.join(settings.BASE_DIR, 'tienda', 'data', 'puntos_blue_express.json')
    if not os.path.exists(json_path):
        _CACHE_PUNTOS_BLUE = {}
        return _CACHE_PUNTOS_BLUE

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            lista = json.load(f)
    except Exception:
        lista = []

    agrupados = {}
    for p in lista:
        c_norm = normalizar_texto(p.get('comuna', ''))
        if c_norm not in agrupados:
            agrupados[c_norm] = []
        agrupados[c_norm].append(p)

    _CACHE_PUNTOS_BLUE = agrupados
    return _CACHE_PUNTOS_BLUE

def obtener_puntos_blue_por_comuna(comuna_nombre):
    """Retorna la lista de Puntos Blue Express habilitados para la comuna indicada."""
    if not comuna_nombre:
        return []
    puntos_map = cargar_puntos_blue_express()
    c_norm = normalizar_texto(comuna_nombre)
    return puntos_map.get(c_norm, [])


def invalidar_cache_puntos_blue():
    """Limpia el caché en memoria para forzar la recarga del archivo JSON."""
    global _CACHE_PUNTOS_BLUE
    _CACHE_PUNTOS_BLUE = None



