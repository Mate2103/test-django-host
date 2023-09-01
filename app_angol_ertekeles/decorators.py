import functools
from django.shortcuts import redirect
from app_angol_ertekeles.models import Tanit


def is_authenticated_tanar(view_func, redirect_url="/accounts/login"):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect(redirect_url)
        if user.groups.filter(name='tanar').count() == 0:
            return redirect("/student/grades")

        linkek = Tanit.objects.filter(tanar=user)
        c = 0
        for link in linkek:
            if link.csoport.name == kwargs['csoport']:
                c += 1
        if c == 0:
            return redirect("/student/grades")
        return view_func(request, *args, **kwargs)
    return wrapper


def is_authenticated_diak(view_func, redirect_url="/accounts/login"):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect(redirect_url)
        if user.groups.filter(name='diak').count() == 0:
            csoport = Tanit.objects.filter(tanar=user).first().csoport.name
            return redirect(f"/teacher/students/{csoport}")

        return view_func(request, *args, **kwargs)
    return wrapper
