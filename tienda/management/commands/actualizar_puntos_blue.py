import os
import json
import urllib.request
from django.core.management.base import BaseCommand
from django.conf import settings
from tienda.comunas_chile import normalizar_texto, REGIONES_Y_COMUNAS

class Command(BaseCommand):
    help = 'Descarga y actualiza el catálogo local de Puntos Blue Express (Copec y Pick-up)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Descargando catálogo oficial de Puntos Blue Express..."))
        
        url = 'https://pudom.api.blue.cl/pdoohd/agencies-external/v3/filters?country_id=75&status=1'
        req = urllib.request.Request(url, headers={
            'Content-Type': 'application/json',
            'x-api-key': 'uGo31Lp5eja66Ftj1juRe9oSiinzqhKi6p39mYok',
            'Channel': 'Mapa-pickup',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                raw_data = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error descargando datos de Blue Express: {e}"))
            return

        self.stdout.write(f"Total agencias recibidas: {len(raw_data)}")

        # Normalización de mapa de comunas para mapeo exacto
        mapa_comunas_canonica = {}
        for reg, comunas in REGIONES_Y_COMUNAS.items():
            for c in comunas:
                mapa_comunas_canonica[normalizar_texto(c)] = (c, reg)

        puntos_limpios = []
        for a in raw_data:
            if a.get('status') != 'active':
                continue
            if not a.get('pickupAvailability'):
                continue

            addr = a.get('address', {})
            commune_data = addr.get('commune', {})
            state_data = addr.get('state', {})
            geo = addr.get('geolocation', {})
            type_agency = a.get('typeAgency', {})

            raw_commune = (commune_data.get('name', '') if isinstance(commune_data, dict) else str(commune_data or '')).strip()
            raw_state = (state_data.get('name', '') if isinstance(state_data, dict) else str(state_data or '')).strip()

            # Resolver nombre canónico de comuna
            norm_c = normalizar_texto(raw_commune)
            if norm_c in mapa_comunas_canonica:
                comuna_canonica, region_canonica = mapa_comunas_canonica[norm_c]
            else:
                comuna_canonica = raw_commune.title()
                region_canonica = raw_state

            # Limpieza y formateo de calle y número
            calle = addr.get('streetName', '').strip()
            numero = str(addr.get('streetNumber', '') or '').strip()
            if numero and numero.lower() not in ('none', '0', 's/n') and numero not in calle:
                direccion_completa = f"{calle} {numero}".strip()
            else:
                direccion_completa = calle

            # Horario resumido
            sched = a.get('schedules', {})
            is_24_7 = sched.get('fullTime', False)
            if is_24_7:
                horario = '24/7 (Continuo)'
            else:
                attentions = sched.get('attentions', [])
                if attentions:
                    d_inicio = attentions[0].get('day', '')[:3]
                    d_fin = attentions[-1].get('day', '')[:3]
                    h_inicio = attentions[0].get('startTime', '')
                    h_fin = attentions[0].get('endTime', '')
                    horario = f"{d_inicio} a {d_fin}: {h_inicio} - {h_fin}"
                else:
                    horario = 'Horario de comercio'

            puntos_limpios.append({
                'id': a.get('agencyId'),
                'nombre': a.get('agencyName', '').strip(),
                'tipo': type_agency.get('name', 'Punto Blue Express').strip(),
                'calle': calle,
                'numero': numero,
                'comuna': comuna_canonica,
                'region': region_canonica,
                'direccion_completa': direccion_completa,
                'horario': horario,
                'es_24_7': is_24_7,
                'lat': geo.get('latitude'),
                'lng': geo.get('longitude'),
            })

        data_dir = os.path.join(settings.BASE_DIR, 'tienda', 'data')
        os.makedirs(data_dir, exist_ok=True)
        target_path = os.path.join(data_dir, 'puntos_blue_express.json')

        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(puntos_limpios, f, ensure_ascii=False, indent=2)

        self.stdout.write(self.style.SUCCESS(
            f"¡Éxito! Se guardaron {len(puntos_limpios)} Puntos Blue Express habilitados para retiro en:\n{target_path}"
        ))
