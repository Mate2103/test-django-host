from django.conf import settings
from django.db import models
from django.contrib.auth.models import User, Group


class UserAdatok(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    csoport = models.ForeignKey(Group, on_delete=models.CASCADE)
    felev = models.IntegerField(blank=True, null=True)
    evvege = models.IntegerField(blank=True, null=True)
    pirosPontok = models.IntegerField(default=0)
    feketePontok = models.IntegerField(default=0)

    class Meta:
        verbose_name = "UserAdat"
        verbose_name_plural = "UserAdatok"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def get_jegyek(user):
        jegyek = Jegy.objects.filter(tanulo=user)
        return jegyek

    def get_atlag(self):
        ossz1 = 0
        ossz2 = 0
        if type(self) == UserAdatok:
            jegyek = UserAdatok.get_jegyek(self.user)
        else:
            jegyek = UserAdatok.get_jegyek(self)

        if not len(jegyek) > 0:
            return 0
        for jegy in jegyek:
            ossz1 += jegy.ertek * jegy.suly
            ossz2 += jegy.suly
        return round(ossz1/ossz2)


class Dolgozat(models.Model):

    nev = models.CharField(max_length=100)
    csoport = models.ForeignKey(Group, on_delete=models.CASCADE)
    suly = models.IntegerField(default=100)
    megirasnapja = models.DateField(
        auto_now=False, auto_now_add=False, null=True, blank=True)

    class Meta:
        verbose_name = "Dolgozat"
        verbose_name_plural = "Dolgozatok"

    def __str__(self):
        return self.nev

    def number_of_done(self):
        jegyek = Jegy.objects.filter(dolgozat=self).filter(tanulo__is_active=True)
        return len(jegyek)

    def get_avarage(self):
        ossz1 = 0
        ossz2 = 0
        jegyek = Jegy.objects.filter(dolgozat=self).filter(tanulo__is_active=True)
        if not len(jegyek) > 0:
            return 0
        for jegy in jegyek:
            ossz1 += jegy.ertek * jegy.suly
            ossz2 += jegy.suly
        return round(ossz1/ossz2)

    def delete_dolgozat_by_delkey(delkey):
        dolgid = delkey[4:len(delkey)]
        dolg = Dolgozat.objects.filter(id=dolgid).first()
        if dolg:
            Jegy.objects.filter(dolgozat=dolg).delete()
            dolg.delete()

    def create_dolg(nev, csoport, suly, datum):
        dolg = Dolgozat.objects.create(
            nev=nev, csoport=csoport, suly=suly, megirasnapja=datum)
        return dolg


class Jegy(models.Model):
    nev = models.CharField(max_length=100)
    suly = models.IntegerField(default=100)
    ertek = models.IntegerField(default=100)
    dolgozat = models.ForeignKey(
        Dolgozat, blank=True, null=True, on_delete=models.CASCADE)
    tanulo = models.ForeignKey(User, on_delete=models.CASCADE)
    datum = models.DateField()

    class Meta:
        verbose_name = "Jegy"
        verbose_name_plural = "Jegyek"

    def __str__(self):
        return f"{self.tanulo.username}: {self.nev}, w: {self.suly}, g: {self.ertek}"

    def delete_jegy_by_delkey(delkey):
        jegyid = delkey[4:len(delkey)]
        jegy = Jegy.objects.filter(id=jegyid).first()
        if jegy:
            jegy.delete()

    def assign_grade(nev, suly, ertek, dolg, tanulo, datum):
        Jegy.objects.create(nev=nev, suly=suly, ertek=ertek,
                            dolgozat=dolg, tanulo=tanulo, datum=datum)


class Tanit(models.Model):

    tanar = models.ForeignKey(User, on_delete=models.CASCADE)
    csoport = models.ForeignKey(Group, on_delete=models.CASCADE)
    maxfeketepont = models.IntegerField(default=4)
    maxpirospont = models.IntegerField(default=4)

    class Meta:
        verbose_name = "Tanár-Csoport reláció"
        verbose_name_plural = "Tanár-Csoport relációk"

    def __str__(self):
        return f"{self.tanar.first_name} {self.tanar.last_name}: {self.csoport.name}"
