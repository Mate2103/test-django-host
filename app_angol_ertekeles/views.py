import random
import string
import json
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from app_angol_ertekeles.models import UserAdatok, User, Jegy, Tanit, Group, Dolgozat
from app_angol_ertekeles.decorators import is_authenticated_tanar, is_authenticated_diak
import datetime
from django.contrib import messages


def index(request):
    if not request.user.is_authenticated:
        return redirect('/accounts/login/')
    elif request.user.groups.filter(name='tanar').exists():
        group = Tanit.objects.filter(tanar=request.user).first().csoport.name
        return redirect(f'/teacher/students/{group}')
    else:
        return redirect('/student/grades')

# diákok nézet
@is_authenticated_tanar
def tanardiaokview(request, csoport):
    user = request.user
    csoportok = Tanit.objects.filter(tanar=user)
    tanit = csoportok.first()
    diakok = UserAdatok.objects.filter(user__is_active=True).filter(csoport__name=csoport).order_by('user__last_name').order_by('user__first_name')

    context = {
        "tanar": True,
        "selectedcsoport": csoport,
        "csoportok": csoportok,
        "diakok": diakok,
        "maxpiros": range(tanit.maxpirospont),
        "maxfekete": range(tanit.maxfeketepont),
        "url": "/teacher/students",
    }

    return render(request, "diakok.html", context)


# itt látja a tanár egy diák jegyeit
@is_authenticated_tanar
def tanardiakjegy(request, csoport, username):

    diakuser = User.objects.filter(username=username)
    if len(diakuser) == 0 :
       return redirect(f'/teacher/students/{csoport}') 
    
    diakuser = diakuser.first()
    if not diakuser.is_active:
        return redirect(f'/teacher/students/{csoport}')
    if  diakuser.useradatok.csoport.name != csoport: 
        return redirect(f'/teacher/students/{csoport}')

    diak = diakuser.useradatok
    jegyek = UserAdatok.get_jegyek(diakuser)
    atlag = UserAdatok.get_atlag(diakuser)

    user = request.user
    csoportok = Tanit.objects.filter(tanar=user)
    tanit = csoportok.first()

    if request.method == 'POST':
        data = request.POST
        if 'move' in data.keys():
            diakok = UserAdatok.objects.filter(user__is_active=True).filter(csoport__name=csoport).order_by('user__last_name').order_by('user__first_name')
            diakok = list(diakok)
            currentindex = diakok.index(diak)
            if data['move'] == 'next':
                if currentindex+1 == len(diakok):
                    return redirect(f"/teacher/students/{csoport}/{diakok[0].user}")
                else:
                    return redirect(f"/teacher/students/{csoport}/{diakok[currentindex+1].user}")
            elif data['move'] == "prev":
                if currentindex == 0:
                    return redirect(f"/teacher/students/{csoport}/{diakok[len(diakok)-1].user}")
                else:
                    return redirect(f"/teacher/students/{csoport}/{diakok[currentindex-1].user}")
        else:    
            pont = list(data.keys())[1]
            if pont[0:3] == "del":
                Jegy.delete_jegy_by_delkey(pont)
            elif pont == 'minusred':
                if diak.pirosPontok > 0:
                    diak.pirosPontok -= 1
            elif pont == 'minusblack':
                if diak.feketePontok > 0:
                    diak.feketePontok -= 1
            elif pont == 'plusred':
                diak.pirosPontok += 1
                if diak.pirosPontok == tanit.maxpirospont:
                    Jegy.assign_grade("From red points", 100, 100,
                                    None, diak.user, datetime.datetime.now())
                    atlag = UserAdatok.get_atlag(diakuser)
                    diak.pirosPontok = 0
            elif pont == 'plusblack':
                diak.feketePontok += 1
                if diak.feketePontok == tanit.maxfeketepont:
                    Jegy.assign_grade("From black points", 100, 0,
                                    None, diak.user, datetime.datetime.now())
                    atlag = UserAdatok.get_atlag(diakuser)
                    diak.feketePontok = 0

            diak.save()
        return HttpResponseRedirect(f"/teacher/students/{csoport}/{username}")
    
    print(tanit.maxpirospont)
    context = {
        "tanar": True,
        "diak": diak,
        "jegyek": jegyek,
        "atlag": atlag,
        "selectedcsoport": csoport,
        "csoportok": csoportok,
        "maxpiros": range(tanit.maxpirospont-1, -1, -1),
        "maxfekete": range(tanit.maxfeketepont),
        "url": "/teacher/students",
    }

    return render(request, "tanardiakjegyek.html", context)


# tanár itt ír be jegyeket
@is_authenticated_tanar
def tanarjegybeiras(request, csoport):
    user = request.user
    csoportok = Tanit.objects.filter(tanar=user)
    diakok = UserAdatok.objects.filter(user__is_active=True).filter(csoport__name=csoport).order_by("user__last_name").order_by("user__first_name")

    if request.method == 'POST':
        dictPost = request.POST
        nev = dictPost["nev"]
        suly = dictPost["suly"]
        datum = dictPost["datum"]
        dogae = len(dictPost.getlist('dolgozate')) > 0
        diakokkeys: list = list(dictPost.keys())
        keys = [key for key in diakokkeys if key not in {
            "csrfmiddlewaretoken", "nev", "suly", "datum", "dolgozate"}]
        dolgozat = None
        if dogae:
            csoportlink = Group.objects.get(name=csoport)
            dolgozat = Dolgozat.create_dolg(nev, csoportlink, suly, datum)
            print(dolgozat)

        for diak in keys:
            diakid = diak
            diak = User.objects.get(id=diakid)
            if dictPost[diakid]:
                Jegy.assign_grade(
                    nev, suly, dictPost[diakid], dolgozat, diak, datum)

    context = {
        "tanar": True,
        "selectedcsoport": csoport,
        "csoportok": csoportok,
        "diakok": diakok,
        "url": "/teacher/grade-assign"
    }

    return render(request, "assign-grades.html", context)


# tanár itt látja a dogákat
@is_authenticated_tanar
def tanardogak(request, csoport):
    if request.method == 'POST':
        key = list(request.POST.keys())[1]
        Dolgozat.delete_dolgozat_by_delkey(key)

    user = request.user
    csoportok = Tanit.objects.filter(tanar=user)

    diakok = UserAdatok.objects.filter(csoport__name=csoport)
    dolgozatok = Dolgozat.objects.filter(csoport__name=csoport)

    context = {
        "tanar": True,
        "selectedcsoport": csoport,
        "csoportok": csoportok,
        "diakok": diakok,
        "dolgozatok": dolgozatok,
        "url": "/teacher/tests",
    }

    return render(request, "tests.html", context)


# tanár itt látja egy dogának a jegyeit
@is_authenticated_tanar
def tanardogajegyek(request: HttpRequest, csoport: str, dolgozat: str) -> HttpResponse:
    user = request.user
    csoportok = Tanit.objects.filter(tanar=user)
    dolg = Dolgozat.objects.filter(id=dolgozat).first()
    if not dolg:
        context = {
            "text": "There is no test with this id",
            "text2": dolgozat,
        }
        return render(request, "nincsilyen.html", context)

    jegyek = Jegy.objects.filter(tanulo__is_active=True).filter(dolgozat=dolg).order_by("tanulo__last_name").order_by("tanulo__first_name")
    csoportlink = Group.objects.get(name=csoport)
    diakok = UserAdatok.objects.filter(user__is_active=True).filter(csoport=csoportlink).order_by("user__last_name").order_by("user__first_name")

    if csoport != dolg.csoport.name:
        return redirect(f"/teacher/tests/{csoport}")

    if request.method == 'POST':
        dictPost = request.POST
        if len(dictPost.keys()) == 2:
            key = list(request.POST.keys())[1]
            Jegy.delete_jegy_by_delkey(key)
        else:
            ertek = dictPost["ertek"]
            diak = dictPost["diak"]
            duser = User.objects.get(username=diak)
            if len(Jegy.objects.filter(tanulo=duser).filter(dolgozat=dolg)) == 0:
                Jegy.assign_grade(dolg.nev, dolg.suly, ertek,
                                  dolg, duser, dolg.megirasnapja)
            else:
                messages.warning(request, "This grade already exist!")

    context = {
        "tanar": True,
        "selectedcsoport": csoport,
        "csoportok": csoportok,
        "dolgozat": dolg,
        "jegyek": jegyek,
        "diakok": diakok,
        "url": "/teacher/tests",
    }
    return render(request, "testgrades.html", context)


# diákok itt látják a jegyeiket
@is_authenticated_diak
def diakoknak(request):
    user = request.user
    jegyek = UserAdatok.get_jegyek(user)
    atlag = UserAdatok.get_atlag(user)
    data = user.useradatok
    tanit = Tanit.objects.filter(csoport=data.csoport).first()

    context = {
        "tanar": False,
        "atlag": atlag,
        "jegyek": jegyek,
        "userdata": data,
        "maxpiros": range(tanit.maxpirospont-1, -1, -1),
        "maxfekete": range(tanit.maxfeketepont),
    }
    template = "diakview.html"

    return render(request, template, context)


# admin oldal tanároknak
@is_authenticated_tanar
def tanaradminoldal(request, csoport):
    user = request.user
    csoportok = Tanit.objects.filter(tanar=user)

    context = {
        "tanar": True,
        "adminsite": True,
        "csoportok": csoportok,
        "selectedcsoport": csoport,
        "url": "/teacher/admin",
    }
        
    context["csoportedited"] = csoport

    tanit = Tanit.objects.filter(csoport__name=csoport).first()
    csoportref = tanit.csoport
    diakok = UserAdatok.objects.filter(
                csoport=csoportref).order_by('user__last_name').order_by('user__first_name')
    
    context['pirospontok'] = tanit.maxpirospont
    context['feketepontok'] = tanit.maxfeketepont

    atlagok = {}
    for useradat in diakok:
         atlagok[useradat] = useradat.get_atlag()
                    
    context['diakok'] = atlagok

    
    if request.method == 'POST':
        data = request.POST
        print(data)
        if 'first_name' in data.keys():
            letters = string.ascii_lowercase
            username = f"{data['first_name'].lower()}_{data['last_name'].lower()}_{''.join(random.choice(letters) for i in range(4))}"
            new_user = User.objects.create_user(username=username, email=data['email'], password='_jelszo')

            new_user.groups.add(csoportref.id,  Group.objects.filter(name='diak').first().id)
            new_user.first_name = data['first_name']
            new_user.last_name = data['last_name']
            new_user.save()

            new_user_adatok = UserAdatok.objects.create(user=new_user, csoport=csoportref, felev=0, evvege=0, feketePontok=0, pirosPontok=0)
            new_user_adatok.save()
        elif len(data.keys()) == 0: 
            body_data = json.loads(request.body.decode("utf-8"))
            print(body_data)
            if 'toggleCheck' in body_data.keys():
                user_to_toggle = User.objects.filter(id=body_data['toggleCheck']).first()
                temp = user_to_toggle.is_active
                user_to_toggle.is_active = not temp
                user_to_toggle.save()
        elif 'setpiros' or "setfekete" in data.keys():
            pirosvalue = data['setred']
            if pirosvalue > 10:
                pirosvalue = 10
            feketevalue = data['setblack']
            if feketevalue > 10:
                feketevalue = 10
            tanit.maxpirospont = pirosvalue
            tanit.maxfeketepont = feketevalue
            tanit.save()
        return HttpResponseRedirect(f"/teacher/admin/{csoport}")
        
       
            
        

    return render(request, 'teacheradmin.html', context)
