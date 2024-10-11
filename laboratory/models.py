from django.db import models
from simple_history.models import HistoricalRecords

from core.models import Employee, Patient
from smit.models import Examen, Consultation


class CathegorieEchantillon(models.Model):
    nom = models.CharField(max_length=100, null=True, blank=True)
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.nom} - {self.parent}"


# Create your models here.
class TypeEchantillon(models.Model):
    nom = models.CharField(max_length=100, null=True, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.nom}"


class Echantillon(models.Model):
    code_echantillon = models.CharField(null=True, blank=True, max_length=10)
    examen_demande = models.ForeignKey(Examen, null=True, blank=True, on_delete=models.CASCADE, related_name='examen_demandee')
    type = models.ForeignKey('TypeEchantillon', null=True, blank=True, on_delete=models.CASCADE)
    cathegorie = models.ForeignKey('CathegorieEchantillon', null=True, blank=True, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE,related_name='echantillon_for_patient')
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE,related_name='echantillon_for_consultation')
    date_collect = models.DateTimeField(null=True, blank=True)
    site_collect = models.CharField(null=True, blank=True, max_length=100)
    agent_collect = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.CASCADE)
    status_echantillons = models.CharField(null=True, blank=True, max_length=10)
    storage_information = models.CharField(null=True, blank=True, max_length=100)
    storage_location = models.CharField(null=True, blank=True, max_length=100)
    storage_temperature = models.CharField(null=True, blank=True, max_length=100)
    volume = models.FloatField(null=True, blank=True, max_length=100, verbose_name='Volume de l\'échantillon (ml)')
    expiration_date = models.CharField(null=True, blank=True, max_length=100)
    linked = models.BooleanField(default=False, null=True, blank=True)
    used = models.BooleanField(default=False, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    # history = HistoricalRecords()

    # @property
    # def accusereception(self):
    #     """
    #     Renvoie les instances d'AccuseReception associées à cet échantillon.
    #     """
    #     return self.accusereception_set.all()

    def __str__(self):
        return f"{self.code_echantillon} - {self.examen_demande}"
