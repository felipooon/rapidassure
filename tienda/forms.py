from django import forms
from .models import Producto
from .models import Categoria

class ProductoForm(forms.ModelForm):
    # Sobreescribimos el campo precio para recibirlo como texto primero
    precio = forms.CharField(widget=forms.TextInput(attrs={'type': 'text'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and self.initial.get('stock') is None:
            self.initial['stock'] = 1

    class Meta:
        model = Producto
        exclude = ['slug']
        widgets = {
            'stock': forms.NumberInput(attrs={'min': '0', 'style': 'text-align: center; font-weight: 700; font-size: 1.05rem;'}),
            'especie_nombre_comun': forms.TextInput(attrs={'placeholder': 'Ej: Terminal POS T-800, Antena RFID UHF'}),
            'especie_nombre_cientifico': forms.TextInput(attrs={'placeholder': 'Ej: Modelo RA-900-V2'}),
            'especie_habitat': forms.TextInput(attrs={'placeholder': 'Ej: Retail, Supermercados, Bodegas y Logística'}),
            'especie_estado_conservacion': forms.TextInput(attrs={'placeholder': 'Ej: Garantía 24 Meses, Norma IP65'}),
            'especie_dato_curioso': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ej: Equipamiento de alta durabilidad con batería de respaldo...'}),
        }
        labels = {
            'tiene_ficha_especie': 'Incluir Especificación Técnica Extendida',
            'especie_nombre_comun': 'Nombre del Modelo / Especificación',
            'especie_nombre_cientifico': 'Código / SKU Técnico',
            'especie_habitat': 'Campo de Aplicación / Industria',
            'especie_estado_conservacion': 'Garantía / Certificación',
            'especie_dato_curioso': 'Ficha Técnica / Destacados',
        }

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
        fields = ["codigo", "descuento_porcentaje", "descuento_monto", "activo", "usos_maximos", "fecha_expiracion"]
        widgets = {
            'fecha_expiracion': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').strip().upper()
        if not codigo:
            raise forms.ValidationError("Ingresa un código de cupón válido.")
        return codigo


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
        fields = ['mostrar_blog', 'mostrar_resenas']
        labels = {
            'mostrar_blog': 'Activar Sección de Blog en la tienda (Navbar y menú)',
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
            for cat in Categoria.objects.all():
                url = cat.get_absolute_url()
                cat_choices.append((url, f"Categoría: {cat.nombre} ({url})"))
                
            if cat_choices:
                choices.append(('Categorías de Productos', tuple(cat_choices)))
        except Exception:
            pass

        choices.append(('Opción Manual', (('custom', '✏️ Ingresar enlace personalizado manualmente...'),)))

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
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Smart POS Dual Screen'}),
            'subtitulo': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ej: Terminales Android de alta velocidad con cobro contactless...'}),
            'badge': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: EQUIPAMIENTO DE CAJA'}),
            'url_destino': forms.TextInput(attrs={'class': 'form-control', 'id': 'url_destino_input', 'placeholder': 'Ej: /categoria/smart-pos-retail-tech/'}),
            'texto_boton': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Equipar mi Caja'}),
            'estilo_fondo': forms.Select(attrs={'class': 'form-control'}),
            'icono_fontawesome': forms.Select(attrs={'class': 'form-control', 'id': 'icono_select'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }