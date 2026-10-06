from django import forms
from .models import Producto
from .models import Categoria

class ProductoForm(forms.ModelForm):
    # Sobreescribimos el campo precio para recibirlo como texto primero
    precio = forms.CharField(widget=forms.TextInput(attrs={'type': 'text'}))
    precio_oferta = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_precio_oferta'})
    )
    monto_descuento = forms.CharField(
        required=False,
        label="Monto de Descuento ($ CLP)",
        widget=forms.TextInput(attrs={
            'id': 'id_monto_descuento',
            'placeholder': 'Ej: 15.000',
            'style': 'font-weight: 700; font-size: 1.05rem;'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and self.initial.get('stock') is None:
            self.initial['stock'] = 1

        # Control de Descuento
        self.fields['porcentaje_descuento'].required = False
        if self.instance.pk and self.instance.tiene_descuento:
            ahorro = self.instance.monto_ahorro
            if ahorro:
                self.initial['monto_descuento'] = f"{ahorro:,}".replace(',', '.')
            if self.instance.precio_oferta:
                self.initial['precio_oferta'] = str(self.instance.precio_oferta)

        # Especificación Técnica Extendida obligatoria
        self.fields['tiene_ficha_especie'].widget = forms.HiddenInput()
        self.fields['tiene_ficha_especie'].initial = True
        self.fields['especie_nombre_comun'].required = True
        self.fields['especie_habitat'].required = True
        self.fields['especie_estado_conservacion'].required = True
        self.fields['especie_dato_curioso'].required = True

    class Meta:
        model = Producto
        exclude = ['slug']
        widgets = {
            'marca': forms.TextInput(attrs={'placeholder': 'Ej: Zebra, Epson, Honeywell, SAT', 'list': 'lista-marcas-sugeridas', 'autocomplete': 'off'}),
            'stock': forms.NumberInput(attrs={'min': '0', 'style': 'text-align: center; font-weight: 700; font-size: 1.05rem;'}),
            'en_oferta': forms.CheckboxInput(attrs={'id': 'id_en_oferta'}),
            'porcentaje_descuento': forms.NumberInput(attrs={'id': 'id_porcentaje_descuento', 'min': '0', 'max': '99', 'placeholder': 'Ej: 20', 'style': 'font-weight: 700; font-size: 1.05rem;'}),
            'alto': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'placeholder': 'Ej: 15.0', 'id': 'id_envio_alto'}),
            'ancho': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'placeholder': 'Ej: 20.0', 'id': 'id_envio_ancho'}),
            'largo': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'placeholder': 'Ej: 30.0', 'id': 'id_envio_largo'}),
            'peso': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'placeholder': 'Ej: 1.25', 'id': 'id_envio_peso'}),
            'especie_nombre_comun': forms.TextInput(attrs={'placeholder': 'Ej: Terminal POS T-800, Antena RFID UHF'}),
            'especie_nombre_cientifico': forms.TextInput(attrs={'placeholder': 'Ej: Modelo RA-900-V2'}),
            'especie_habitat': forms.TextInput(attrs={'placeholder': 'Ej: Retail, Supermercados, Bodegas y Logística'}),
            'especie_estado_conservacion': forms.TextInput(attrs={'placeholder': 'Ej: Garantía 24 Meses, Norma IP65'}),
            'especie_dato_curioso': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ej: Equipamiento de alta durabilidad con batería de respaldo...'}),
        }
        labels = {
            'marca': 'Marca / Fabricante',
            'en_oferta': 'Activar Oferta Promocional (% OFF)',
            'porcentaje_descuento': 'Porcentaje de Descuento (% OFF)',
            'alto': 'Alto (cm)',
            'ancho': 'Ancho (cm)',
            'largo': 'Largo (cm)',
            'peso': 'Peso (kg)',
            'tiene_ficha_especie': 'Especificación Técnica Extendida',
            'especie_nombre_comun': 'Nombre del Modelo / Especificación',
            'especie_nombre_cientifico': 'Código / SKU Técnico (Opcional)',
            'especie_habitat': 'Campo de Aplicación / Industria',
            'especie_estado_conservacion': 'Garantía / Certificación',
            'especie_dato_curioso': 'Ficha Técnica / Destacados',
        }

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['tiene_ficha_especie'] = True
        
        en_oferta = cleaned_data.get('en_oferta')
        porcentaje = cleaned_data.get('porcentaje_descuento') or 0
        monto_desc_raw = cleaned_data.get('monto_descuento')
        precio_oferta_raw = cleaned_data.get('precio_oferta')
        precio_val = cleaned_data.get('precio')

        precio_clean = 0
        if precio_val:
            try:
                precio_clean = int(str(precio_val).replace('$', '').replace('.', '').replace(' ', '').strip())
            except (ValueError, TypeError):
                precio_clean = 0

        monto_clean = None
        if monto_desc_raw:
            try:
                m_str = str(monto_desc_raw).replace('$', '').replace('.', '').replace(' ', '').strip()
                if m_str:
                    monto_clean = int(m_str)
            except (ValueError, TypeError):
                pass

        precio_oferta_clean = None
        if precio_oferta_raw:
            try:
                po_str = str(precio_oferta_raw).replace('$', '').replace('.', '').replace(' ', '').strip()
                if po_str:
                    precio_oferta_clean = int(po_str)
            except (ValueError, TypeError):
                pass

        if en_oferta:
            # Caso 1: Se especificó monto de descuento directo (ej: $30.000)
            if monto_clean is not None and monto_clean > 0:
                if precio_clean > 0:
                    if monto_clean >= precio_clean:
                        self.add_error('monto_descuento', 'El monto de descuento debe ser menor al precio regular.')
                    else:
                        precio_oferta_clean = precio_clean - monto_clean
                        porcentaje = min(99, max(1, int(round((monto_clean / precio_clean) * 100))))
            # Caso 2: Se especificó precio de oferta directo
            elif precio_oferta_clean is not None and 0 < precio_oferta_clean < precio_clean:
                monto_clean = precio_clean - precio_oferta_clean
                porcentaje = min(99, max(1, int(round((monto_clean / precio_clean) * 100))))
            # Caso 3: Solo se ingresó porcentaje (ej: 20%)
            elif porcentaje and 0 < porcentaje < 100:
                if precio_clean > 0:
                    descuento = int(round((precio_clean * porcentaje) / 100.0))
                    precio_oferta_clean = max(0, precio_clean - descuento)
            else:
                self.add_error('porcentaje_descuento', 'Debes ingresar un porcentaje o monto de descuento mayor a 0 para activar la oferta.')

            if porcentaje >= 100:
                self.add_error('porcentaje_descuento', 'El porcentaje de descuento debe ser menor al 100%.')
        else:
            porcentaje = 0
            precio_oferta_clean = None

        cleaned_data['porcentaje_descuento'] = porcentaje
        cleaned_data['precio_oferta'] = precio_oferta_clean
            
        return cleaned_data

    def clean_precio(self):
        data = self.cleaned_data.get('precio')
        
        # 1. Quitamos puntos y espacios por si acaso escribió "18.000 "
        data = data.replace('.', '').replace(' ', '')
        
        try:
            # 2. Intentamos convertirlo a entero
            precio_final = int(data)
        except ValueError:
            raise forms.ValidationError("Por favor, ingresa un precio válido sin letras.")

        # 3. Validación de negativo
        if precio_final < 0:
            raise forms.ValidationError("El precio no puede ser negativo.")
            
        return precio_final

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "imagen"]

from .models import Cupon

class CuponForm(forms.ModelForm):
    class Meta:
        model = Cupon
        fields = [
            "codigo",
            "descuento_porcentaje",
            "descuento_monto",
            "tope_descuento",
            "monto_minimo_compra",
            "excluir_ofertas",
            "activo",
            "usos_maximos",
            "fecha_expiracion"
        ]
        widgets = {
            'fecha_expiracion': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'tope_descuento': forms.NumberInput(attrs={'min': '0', 'placeholder': 'Ej: 15000 (Opcional)'}),
            'monto_minimo_compra': forms.NumberInput(attrs={'min': '0', 'placeholder': 'Ej: 30000 (Opcional)'}),
            'descuento_porcentaje': forms.NumberInput(attrs={'min': '0', 'max': '100', 'placeholder': 'Ej: 15'}),
            'descuento_monto': forms.NumberInput(attrs={'min': '0', 'placeholder': 'Ej: 5000'}),
            'usos_maximos': forms.NumberInput(attrs={'min': '1', 'placeholder': 'Ej: 100 (Opcional)'}),
        }
        labels = {
            'codigo': 'Código del Cupón',
            'descuento_porcentaje': '% Descuento',
            'descuento_monto': 'Monto Fijo ($ CLP)',
            'tope_descuento': 'Tope Máximo de Descuento ($ CLP)',
            'monto_minimo_compra': 'Compra Mínima Requerida ($ CLP)',
            'excluir_ofertas': 'No acumular con productos ya en oferta',
            'usos_maximos': 'Usos Máximos Permitidos',
            'fecha_expiracion': 'Fecha y Hora de Expiración',
            'activo': 'Cupón Activo',
        }

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').strip().upper()
        if not codigo:
            raise forms.ValidationError("Ingresa un código de cupón válido.")
        return codigo

    def clean(self):
        cleaned_data = super().clean()
        pct = cleaned_data.get('descuento_porcentaje') or 0
        monto = cleaned_data.get('descuento_monto') or 0
        tope = cleaned_data.get('tope_descuento')
        minimo = cleaned_data.get('monto_minimo_compra')

        if pct <= 0 and monto <= 0:
            raise forms.ValidationError("Debes ingresar al menos un porcentaje de descuento (% OFF) o un monto fijo en CLP.")

        if pct > 100:
            self.add_error('descuento_porcentaje', "El porcentaje de descuento no puede ser mayor al 100%.")

        if tope is not None and tope < 0:
            self.add_error('tope_descuento', "El tope de descuento no puede ser un número negativo.")

        if minimo is not None and minimo < 0:
            self.add_error('monto_minimo_compra', "El monto mínimo de compra no puede ser un número negativo.")

        return cleaned_data


from .models import BlogPost, ResenaProducto, ConfiguracionSitio, BannerPromocional

class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['titulo', 'autor', 'resumen', 'contenido', 'imagen', 'publicado']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título del artículo'}),
            'autor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del autor (Ej: Equipo Rapidassure, Soporte, etc.)'}),
            'resumen': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Breve resumen para las tarjetas'}),
            'contenido': forms.Textarea(attrs={'class': 'form-control', 'rows': 12, 'id': 'editor-contenido', 'placeholder': 'Escribe el contenido de tu artículo...'}),
        }

class ResenaForm(forms.ModelForm):
    class Meta:
        model = ResenaProducto
        fields = ['nombre_cliente', 'email_cliente', 'calificacion', 'comentario']
        widgets = {
            'nombre_cliente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre'}),
            'email_cliente': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Tu correo (opcional)'}),
            'calificacion': forms.Select(choices=[(i, f"{i} Estrella{'s' if i > 1 else ''}") for i in range(5, 0, -1)], attrs={'class': 'form-control'}),
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '¿Qué te pareció este producto?'}),
        }

class ConfiguracionSitioForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionSitio
        fields = ['mostrar_resenas']
        labels = {
            'mostrar_resenas': 'Activar Reseñas y Calificaciones con Estrellas en productos',
        }

class BannerPromocionalForm(forms.ModelForm):
    url_destino_select = forms.ChoiceField(
        required=False,
        label="Seleccionar Enlace Rápido",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'url_destino_select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [
            ('', '-- Seleccionar destino de la tienda --'),
            ('Secciones de Inicio', (
                ('/', 'Página Principal (/)'),
                ('/#categorias', 'Sección Categorías (/#categorias)'),
                ('/#promociones', 'Sección Promociones (/#promociones)'),
                ('/#destacados', 'Sección Productos Destacados (/#destacados)'),
                ('/#contacto', 'Sección Contacto (/#contacto)'),
                ('/blog/', 'Sección Blog (/blog/)'),
                ('/deseos/', 'Lista de Deseos (/deseos/)'),
            )),
        ]
        
        try:
            cat_choices = []
            for cat in Categoria.objects.all().order_by('nombre'):
                url = cat.get_absolute_url()
                cat_choices.append((url, f"Categoría: {cat.nombre} ({url})"))
                
                # Marcas registradas en esta categoría
                marcas_cat = list(
                    Producto.objects.filter(categoria=cat, disponible=True)
                    .exclude(marca='')
                    .values_list('marca', flat=True)
                    .distinct()
                    .order_by('marca')
                )
                for m in marcas_cat:
                    url_marca = f"{url}?marca={m}"
                    cat_choices.append((url_marca, f"  ↳ {cat.nombre} ➔ Marca: {m}"))

            if cat_choices:
                choices.append(('Categorías & Marcas', tuple(cat_choices)))
        except Exception:
            pass

        choices.append(('Opción Manual', (('custom', 'Ingresar enlace personalizado manualmente...'),)))

        self.fields['url_destino_select'].choices = choices
        
        if self.instance and self.instance.pk and self.instance.url_destino:
            current_url = self.instance.url_destino
            all_urls = [c[0] for group in choices for c in (group[1] if isinstance(group[1], (tuple, list)) else [(group[0], group[1])])]
            if current_url in all_urls:
                self.fields['url_destino_select'].initial = current_url
            else:
                self.fields['url_destino_select'].initial = 'custom'

    class Meta:
        model = BannerPromocional
        fields = ['titulo', 'subtitulo', 'badge', 'badge_gold', 'url_destino_select', 'url_destino', 'texto_boton', 'estilo_fondo', 'icono_fontawesome', 'orden', 'activo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'id': 'banner_titulo_input', 'placeholder': 'Ej: Smart POS Dual Screen'}),
            'subtitulo': forms.Textarea(attrs={'class': 'form-control', 'id': 'banner_subtitulo_input', 'rows': 2, 'placeholder': 'Ej: Terminales Android de alta velocidad con cobro contactless...'}),
            'badge': forms.TextInput(attrs={'class': 'form-control', 'id': 'banner_badge_input', 'placeholder': 'Ej: EQUIPAMIENTO DE CAJA'}),
            'badge_gold': forms.CheckboxInput(attrs={'id': 'banner_badge_gold_input'}),
            'url_destino': forms.TextInput(attrs={'class': 'form-control', 'id': 'url_destino_input', 'placeholder': 'Ej: /categoria/smart-pos-retail-tech/'}),
            'texto_boton': forms.TextInput(attrs={'class': 'form-control', 'id': 'banner_btn_input', 'placeholder': 'Ej: Equipar mi Caja'}),
            'estilo_fondo': forms.Select(attrs={'class': 'form-control', 'id': 'estilo_fondo_select'}),
            'icono_fontawesome': forms.Select(attrs={'class': 'form-control', 'id': 'icono_select'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }