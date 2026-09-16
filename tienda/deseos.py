from .models import Producto

class Deseos:
    def __init__(self, request):
        """
        Inicializa la lista de deseos anónima usando la sesión de Django.
        """
        self.session = request.session
        deseos = self.session.get('deseos')
        
        if not deseos:
            deseos = self.session['deseos'] = {}
            
        self.deseos = deseos

    def toggle(self, producto):
        """
        Agrega o quita un producto de la lista de deseos.
        Devuelve True si fue agregado, False si fue eliminado.
        """
        id = str(producto.id if hasattr(producto, 'id') else producto)
        
        if id in self.deseos:
            del self.deseos[id]
            self.guardar()
            return False
        else:
            if hasattr(producto, 'id'):
                p_obj = producto
            else:
                p_obj = Producto.objects.filter(id=int(id)).first()

            if p_obj:
                self.deseos[id] = {
                    "producto_id": p_obj.id,
                    "nombre": p_obj.nombre,
                    "precio": str(p_obj.precio),
                    "imagen": p_obj.imagen.url if p_obj.imagen else ""
                }
                self.guardar()
                return True
            return False

    def agregar(self, producto):
        id = str(producto.id if hasattr(producto, 'id') else producto)
        if id not in self.deseos:
            self.toggle(producto)

    def eliminar(self, producto):
        id = str(producto.id if hasattr(producto, 'id') else producto)
        if id in self.deseos:
            del self.deseos[id]
            self.guardar()

    def limpiar(self):
        self.session['deseos'] = {}
        self.guardar()

    def guardar(self):
        self.session.modified = True

    def contiene(self, producto_id):
        return str(producto_id) in self.deseos

    def __len__(self):
        return len(self.deseos)

    def __iter__(self):
        producto_ids = self.deseos.keys()
        productos = Producto.objects.filter(id__in=producto_ids)
        deseos_copia = {key: value.copy() for key, value in self.deseos.items()}

        for producto in productos:
            key = str(producto.id)
            if key in deseos_copia:
                deseos_copia[key]['producto_real'] = producto

        for item in deseos_copia.values():
            yield item
