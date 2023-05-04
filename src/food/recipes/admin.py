from django.contrib import admin

# Register your models here.
from .models import Recipe, Cuisine

admin.site.register(Recipe)
admin.site.register(Cuisine)