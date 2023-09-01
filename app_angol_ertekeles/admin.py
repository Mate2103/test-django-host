from django.contrib import admin
from .models import UserAdatok, Dolgozat, Jegy, Tanit

# Register your models here.
admin.site.register([UserAdatok, Dolgozat, Jegy, Tanit])
