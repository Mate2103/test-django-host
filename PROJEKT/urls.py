from django.contrib import admin
from django.urls import path, include
from app_angol_ertekeles.views import index, diakoknak, tanardiaokview, tanardiakjegy, tanarjegybeiras, tanardogak, tanardogajegyek, tanaradminoldal

urlpatterns = [
    path('', index, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('student/grades/', diakoknak),
    path('teacher/students/<str:csoport>', tanardiaokview),
    path('teacher/students/<str:csoport>/<str:username>', tanardiakjegy),
    path('teacher/tests/<str:csoport>', tanardogak),
    path('teacher/tests/<str:csoport>/<str:dolgozat>', tanardogajegyek),
    path('teacher/grade-assign/<str:csoport>', tanarjegybeiras),
    path('teacher/admin/<str:csoport>', tanaradminoldal)
]
