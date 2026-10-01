from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Producto, Categoria, BlogPost

class ProductoViewSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9
    protocol = 'https'

    def items(self):
        return Producto.objects.filter(disponible=True).order_by('-id')

class CategoriaViewSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8
    protocol = 'https'

    def items(self):
        return Categoria.objects.all().order_by('id')

class BlogPostViewSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8
    protocol = 'https'

    def items(self):
        return BlogPost.objects.filter(publicado=True).order_by('-fecha_creacion')

    def lastmod(self, item):
        return item.fecha_creacion

class StaticViewSitemap(Sitemap):
    priority = 0.7
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return ['index', 'blog_list', 'terminos']

    def location(self, item):
        return reverse(item)

