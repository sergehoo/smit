import re
import uuid
from datetime import datetime, timedelta

import phonenumbers
from allauth.account.forms import LoginForm
from django import forms
from django.contrib.auth.models import Permission, Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from django_countries.fields import CountryField
from tinymce.widgets import TinyMCE

from core.models import situation_matrimoniales_choices, villes_choices, Sexe_choices, pays_choices, \
    professions_choices, Goupe_sanguin_choices, communes_et_quartiers_choices, nationalite_choices, \
    Patient_statut_choices, CasContact, Location

from pharmacy.models import Medicament, RendezVous, ArticleCommande, Commande, Fournisseur, MouvementStock
from smit.models import Patient, Appointment, Service, Employee, Constante, \
    Hospitalization, Consultation, Symptomes, Allergies, AntecedentsMedicaux, Examen, Prescription, LitHospitalisation, \
    Analyse, TestRapideVIH, RAPID_HIV_TEST_TYPES, EnqueteVih, MaladieOpportuniste, SigneFonctionnel, \
    IndicateurBiologique, IndicateurFonctionnel, IndicateurSubjectif, HospitalizationIndicators, PrescriptionExecution, \
    Diagnostic, AvisMedical, EffetIndesirable, HistoriqueMaladie, Observation, CommentaireInfirmier, Suivi, \
    UniteHospitalisation, TypeAntecedent, TypeEchantillon, CathegorieEchantillon, Echantillon, ModeDeVie, Appareil, \
    ProblemePose, ResumeSyndromique, ExamenStandard, ImagerieMedicale, BilanParaclinique, SuiviProtocole, Protocole, \
    TraitementARV, ResultatAnalyse
from django_select2 import forms as s2forms

POSOLOGY_CHOICES = [
    ('Une fois par jour', 'Une fois par jour'),
    ('Deux fois par jour', 'Deux fois par jour'),
    ('Trois fois par jour', 'Trois fois par jour'),
    ('Quatre fois par jour', 'Quatre fois par jour'),
    ('Toutes les 4 heures', 'Toutes les 4 heures'),
    ('Toutes les 6 heures', 'Toutes les 6 heures'),
    ('Toutes les 8 heures', 'Toutes les 8 heures'),
    ('Si besoin', 'Si besoin'),
    ('Avant les repas', 'Avant les repas'),
    ('Après les repas', 'Après les repas'),
    ('Au coucher', 'Au coucher'),
    ('Une fois par semaine', 'Une fois par semaine'),
    ('Deux fois par semaine', 'Deux fois par semaine'),
    ('Un jour sur deux', 'Un jour sur deux'),
]

school_level = [
    ('Inconnu', 'Inconnu'),
    ('Non-scolarisé', 'Non-scolarisé'),
    ('Primaire', 'Primaire'),
    ('Secondaire', 'Secondaire'),
    ('Universitaire', 'Universitaire'),

]
ethnic_groups = [
    # AKAN Group
    ('Autre', 'Autre'),
    ('Abbey', 'Abbey'),
    ('Abidji', 'Abidji'),
    ('Abron', 'Abron'),
    ('Abouré', 'Abouré'),
    ('Ega', 'Ega'),
    ('Agni', 'Agni'),
    ('Ahizi', 'Ahizi'),
    ('Adjoukrou', 'Adjoukrou'),
    ('Alladian', 'Alladian'),
    ('N’zima', 'N’zima'),
    ('Attié', 'Attié'),
    ('Avikam', 'Avikam'),
    ('Ayahou', 'Ayahou'),
    ('Baoulé', 'Baoulé'),
    ('Brignan', 'Brignan'),
    ('Ebrié', 'Ebrié'),
    ('Ehotilé', 'Ehotilé'),
    ('Elomouin', 'Elomouin'),
    ('Essouma', 'Essouma'),
    ('Gwa', 'Gwa'),
    ('M’batto', 'M’batto'),
    ('Yowrè', 'Yowrè'),
    # GOUR Group
    ('Birifor', 'Birifor'),
    ('Camara', 'Camara'),
    ('Degha', 'Degha'),
    ('Djafolo', 'Djafolo'),
    ('Djimini', 'Djimini'),
    ('Djamala', 'Djamala'),
    ('Gbin', 'Gbin'),
    ('Koulango', 'Koulango'),
    ('Lobi', 'Lobi'),
    ('Lohon', 'Lohon'),
    ('Lohron', 'Lohron'),
    ('Tagbana', 'Tagbana'),
    ('Ténéwéré', 'Ténéwéré'),
    ('Tiembara', 'Tiembara'),
    ('Nafara', 'Nafara'),
    ('Niarafolo', 'Niarafolo'),
    ('Samassogo', 'Samassogo'),
    ('Sénoufo', 'Sénoufo'),
    # MANDE Group
    ('Gouro', 'Gouro'),
    ('Koyata', 'Koyata'),
    ('Mahou', 'Mahou'),
    ('Malinké', 'Malinké'),
    ('Mangoro', 'Mangoro'),
    ('Nomou', 'Nomou'),
    ('Toura', 'Toura'),
    ('Wan', 'Wan'),
    ('Yacouba', 'Yacouba'),
    # KROU Group
    ('Bakwe', 'Bakwe'),
    ('Bété', 'Bété'),
    ('Dida', 'Dida'),
    ('Gagou', 'Gagou'),
    ('Godié', 'Godié'),
    ('Guéré', 'Guéré'),
    ('Kouzié', 'Kouzié'),
    ('Kroumen', 'Kroumen'),
    ('Neyo', 'Neyo'),
    ('Niaboua', 'Niaboua'),
    ('Wini', 'Wini'),
    ('Wobè', 'Wobè')
]
MotifRendezVous = [
    ('Aucun', 'Aucun'),
    ('Suivi médical', 'Suivi médical'),
    ('Consultation de routine', 'Consultation de routine'),
    ('Bilan de santé', 'Bilan de santé'),
    ('Consultation spécialisée', 'Consultation spécialisée'),
    ('Suivi postopératoire', 'Suivi postopératoire'),
    ('Suivi prénatal', 'Suivi prénatal'),
    ('Suivi postnatal', 'Suivi postnatal'),
    ('Planification familiale', 'Planification familiale'),
    ('Évaluation psychologique', 'Évaluation psychologique'),
    ('Rééducation', 'Rééducation'),
    ('Examen d’imagerie', 'Examen d’imagerie'),
    ('Examen de laboratoire', 'Examen de laboratoire'),
    ('Renouvellement d’ordonnance', 'Renouvellement d’ordonnance'),
    ('Consultation nutritionnelle', 'Consultation nutritionnelle'),
    ('Contrôle hypertension', 'Contrôle hypertension'),
    ('Suivi maladies chroniques', 'Suivi maladies chroniques'),
    ('Prévention et conseils santé', 'Prévention et conseils santé'),
    ('Conseils en bien-être', 'Conseils en bien-être'),
    ('Évaluation gériatrique', 'Évaluation gériatrique'),
    ('Évaluation de fertilité', 'Évaluation de fertilité'),
    ('Suivi pédiatrique', 'Suivi pédiatrique'),
    ('Accompagnement social', 'Accompagnement social'),
    ('Consultation pour douleur chronique', 'Consultation pour douleur chronique'),
    ('Examen préventif', 'Examen préventif'),
    ('Entretien de santé mentale', 'Entretien de santé mentale'),
    ('Évaluation orthopédique', 'Évaluation orthopédique'),
    ('Suivi orthopédique', 'Suivi orthopédique'),
    ('Dépistage', 'Dépistage'),
    ('Test allergologique', 'Test allergologique'),
    ('Test fonction respiratoire', 'Test fonction respiratoire'),
    ('Examen cardio-vasculaire', 'Examen cardio-vasculaire'),
    ('Consultation pour réadaptation', 'Consultation pour réadaptation'),
    ('Autre', 'Autre'),
]


class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter une classe CSS personnalisée pour le champ de mot de passe
        self.fields['password'].widget.attrs.update({'class': 'form-control password-field'})


class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['activite', 'patient', 'constante', 'symptomes', 'antecedentsMedicaux', 'examens', 'allergies',
                  'services', 'doctor', 'consultation_date', 'reason', 'diagnosis', 'commentaires', 'suivi', 'status',
                  'hospitalised', 'requested_at', 'motifrejet', 'validated_at']


class PatientCreateForm(forms.ModelForm):
    nom = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'nom', }))
    prenoms = forms.CharField(required=True,
                              widget=forms.TextInput(
                                  attrs={'class': 'form-control form-control-lg form-control-outlined',
                                         'placeholder': 'prenom', }))

    contact = forms.CharField(required=True,
                              widget=forms.TextInput(
                                  attrs={'type': 'tel', 'class': 'form-control form-control-lg form-control-outlined',
                                         'placeholder': '0701020304', 'id': 'phone'}))

    situation_matrimoniale = forms.ChoiceField(required=True, choices=situation_matrimoniales_choices,
                                               widget=forms.Select(
                                                   attrs={
                                                       'class': 'form-control form-control-lg form-control-outlined select2 form-select ',
                                                       'data-search': 'on', 'id': 'situation_matrimoniale'}))
    lieu_naissance = forms.ChoiceField(required=True, choices=villes_choices, widget=forms.Select(
        attrs={'class': 'form-control form-control-lg form-control-outlined select2 form-select ', 'data-search': 'on',
               'id': 'outlined'}))
    date_naissance = forms.DateField(required=True,
                                     widget=forms.DateInput(
                                         attrs={'class': 'form-control form-control-lg form-control-outlined',
                                                'id': 'outlined',
                                                'type': 'date'}))
    genre = forms.ChoiceField(required=True, choices=Sexe_choices,
                              widget=forms.Select(
                                  attrs={'class': 'form-control form-control-lg form-control-outlined', }))
    nationalite = forms.ChoiceField(required=True, choices=nationalite_choices,
                                    widget=forms.Select(
                                        attrs={
                                            'class': 'form-control form-control-lg form-control-outlined select2 form-select ',
                                            'data-search': 'on', 'id': 'nationalite'}))
    ethnie = forms.ChoiceField(required=False, choices=ethnic_groups, widget=forms.Select(
        attrs={'class': 'form-control form-control-lg form-control-outlined select2 form-select ',
               'data-search': 'on', 'id': 'ethnie'}))
    profession = forms.ChoiceField(required=False, choices=professions_choices, widget=forms.Select(
        attrs={'class': 'form-control form-control-lg form-control-outlined select2 form-select ', 'data-search': 'on',
               'id': 'profession'}))

    nbr_enfants = forms.IntegerField(required=False, widget=forms.NumberInput(
        attrs={'class': 'form-control form-control-lg number-spinner', 'value': '0', 'type': 'number'}))

    groupe_sanguin = forms.ChoiceField(required=False, choices=Goupe_sanguin_choices, widget=forms.Select(
        attrs={'class': 'form-control form-control-lg form-control-outlined select2 form-select ', 'data-search': 'on',
               'id': 'groupe_sanguin'}))
    niveau_etude = forms.ChoiceField(required=False, choices=school_level,
                                     widget=forms.Select(
                                         attrs={'class': 'form-control  form-control-lg form-control-outlined',
                                                'id': 'outlined', }))
    employeur = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Fonction Publique', }))

    localite = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-lg form-control-outlined select2 form-select ',
                                   'data-search': 'on', })
    )

    code_vih = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Code VIH', }))

    cmu = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Numero CMU', }))

    class Meta:
        model = Patient
        fields = [
            'nom', 'prenoms', 'contact', 'situation_matrimoniale',
            'lieu_naissance', 'date_naissance', 'genre', 'nationalite',
            'profession', 'nbr_enfants', 'groupe_sanguin', 'niveau_etude',
            'employeur', 'localite', 'code_vih', 'cmu'
        ]
        widgets = {'date_naissance': forms.DateInput(attrs={'type': 'date'}), }

    def clean_contact(self):
        contact = self.cleaned_data.get('contact')
        try:
            parsed_number = phonenumbers.parse(contact, 'CI')
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValidationError("Invalid phone number format.")
        except phonenumbers.phonenumberutil.NumberParseException:
            raise ValidationError("Invalid phone number.")
        return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)

    def clean_date_naissance(self):
        date_naissance = self.cleaned_data.get('date_naissance')
        today = datetime.today().date()

        # Calculate the maximum and minimum valid birth dates
        min_date_naissance = today - timedelta(days=365.25)  # Approximately 1 year ago
        max_date_naissance = today - timedelta(days=365.25 * 120)  # Approximately 120 years ago

        # Check if the date is outside the allowed range
        if date_naissance > min_date_naissance:
            raise ValidationError("La date de naissance doit être supérieure à 1 an.")
        elif date_naissance < max_date_naissance:
            raise ValidationError("La date de naissance doit être inférieure à 120 ans.")

        return date_naissance


class PatientUpdateForm(forms.ModelForm):
    nom = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Nom'}))

    prenoms = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Prénom'}))

    contact = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'type': 'tel', 'class': 'form-control', 'placeholder': '0701020304', 'id': 'phone'}))

    situation_matrimoniale = forms.ChoiceField(required=True, choices=situation_matrimoniales_choices,
                                               widget=forms.Select(attrs={'class': 'form-control'}))

    lieu_naissance = forms.ChoiceField(required=True, choices=villes_choices,
                                       widget=forms.Select(attrs={'class': 'form-control'}))

    date_naissance = forms.DateField(required=True,
                                     widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    genre = forms.ChoiceField(required=True, choices=Sexe_choices, widget=forms.Select(attrs={'class': 'form-control'}))

    nationalite = forms.ChoiceField(required=True, choices=nationalite_choices,
                                    widget=forms.Select(attrs={
                                        'class': 'form-control form-control-lg form-control-outlined select2 form-select ',
                                        'data-search': 'on', }))

    ethnie = forms.ChoiceField(required=False, choices=ethnic_groups,
                               widget=forms.Select(attrs={
                                   'class': 'form-control form-control-lg form-control-outlined select2 form-select ',
                                   'data-search': 'on', }))

    profession = forms.ChoiceField(required=False, choices=professions_choices,
                                   widget=forms.Select(attrs={
                                       'class': 'form-control form-control-lg form-control-outlined select2 form-select ',
                                       'data-search': 'on', }))

    nbr_enfants = forms.IntegerField(required=False,
                                     widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}))

    groupe_sanguin = forms.ChoiceField(required=False, choices=Goupe_sanguin_choices,
                                       widget=forms.Select(attrs={'class': 'form-control'}))

    niveau_etude = forms.ChoiceField(required=False, choices=school_level,
                                     widget=forms.Select(attrs={'class': 'form-control'}))

    employeur = forms.CharField(required=False,
                                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Employeur'}))

    localite = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-lg form-control-outlined select2 form-select ',
                                   'data-search': 'on', })
    )

    code_vih = forms.CharField(required=False,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code VIH'}))

    cmu = forms.CharField(required=False,
                          widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro CMU'}))

    class Meta:
        model = Patient
        fields = [
            'nom', 'prenoms', 'contact', 'situation_matrimoniale',
            'lieu_naissance', 'date_naissance', 'genre', 'nationalite',
            'profession', 'nbr_enfants', 'groupe_sanguin', 'niveau_etude',
            'employeur', 'localite', 'code_vih', 'cmu'
        ]

    def clean_contact(self):
        contact = self.cleaned_data.get('contact')
        try:
            parsed_number = phonenumbers.parse(contact, 'CI')  # Code pays Côte d'Ivoire
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValidationError("Format de numéro de téléphone invalide.")
        except phonenumbers.phonenumberutil.NumberParseException:
            raise ValidationError("Numéro de téléphone invalide.")
        return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)

    def clean_date_naissance(self):
        date_naissance = self.cleaned_data.get('date_naissance')
        today = datetime.today().date()
        min_date_naissance = today - timedelta(days=365.25)  # Minimum 1 an d'âge
        max_date_naissance = today - timedelta(days=365.25 * 120)  # Maximum 120 ans d'âge

        if date_naissance > min_date_naissance:
            raise ValidationError("La date de naissance doit être supérieure à 1 an.")
        elif date_naissance < max_date_naissance:
            raise ValidationError("La date de naissance doit être inférieure à 120 ans.")

        return date_naissance

    def __init__(self, *args, **kwargs):
        super(PatientUpdateForm, self).__init__(*args, **kwargs)

        # ✅ Assurez-vous que la date est bien affichée au format 'YYYY-MM-DD'
        if self.instance and self.instance.date_naissance:
            self.initial['date_naissance'] = self.instance.date_naissance.strftime('%Y-%m-%d')


class AppointmentForm(forms.ModelForm):
    patient = forms.ModelChoiceField(queryset=Patient.objects.all(), widget=forms.Select(
        attrs={'class': 'form-control form-control-xl select2 form-select ', 'data-search': 'on',
               'id': 'patient'}))
    service = forms.ModelChoiceField(queryset=Service.objects.all(), widget=forms.Select(
        attrs={'class': 'form-control form-control-lg  select2 form-select ', 'data-search': 'on',
               'id': 'service'}))

    doctor = forms.ModelChoiceField(queryset=Employee.objects.all(), label='Docteur', widget=forms.Select(
        attrs={'class': 'form-control form-control-lg  select2 form-select ', 'data-search': 'on',
               'id': 'outlined'}))

    date = forms.DateField(label='Date du rendez-vous', widget=forms.DateInput(
        attrs={'class': 'form-control form-control-lg', 'type': 'date', 'data-date-format': 'dd/mm/yyyy'}))

    time = forms.TimeField(label='Heure du rendez-vous', widget=forms.TimeInput(
        attrs={'class': 'form-control form-control-lg ', 'type': 'time'}))

    reason = forms.ChoiceField(choices=MotifRendezVous, required=False, label='Objet', widget=forms.Select(
        attrs={'class': 'form-control form-control-lg  select2 form-select ', 'data-search': 'on'}))

    class Meta:
        model = Appointment
        fields = ['patient', 'service', 'doctor', 'date', 'time', 'reason']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }


class AppointmentUpdateForm(forms.ModelForm):
    # patient = forms.ModelChoiceField(queryset=Patient.objects.all(), widget=forms.Select(
    #     attrs={'class': 'form-control form-control-xl select2 form-select ', 'data-search': 'on',
    #            'id': 'patient'}))
    service = forms.ModelChoiceField(queryset=Service.objects.all(), widget=forms.Select(
        attrs={'class': 'form-control form-control-lg  select2 form-select ', 'data-search': 'on',
               'id': 'service'}))

    doctor = forms.ModelChoiceField(queryset=Employee.objects.all(), label='Docteur', widget=forms.Select(
        attrs={'class': 'form-control form-control-lg  select2 form-select ', 'data-search': 'on',
               'id': 'outlined'}))

    date = forms.DateField(label='Date du rendez-vous', widget=forms.DateInput(
        attrs={'class': 'form-control form-control-lg', 'data-date-format': 'dd/mm/yyyy'}))

    time = forms.TimeField(label='Heure du rendez-vous', widget=forms.TimeInput(
        attrs={'class': 'form-control form-control-lg ', 'type': 'time'}))

    reason = forms.ChoiceField(choices=MotifRendezVous, required=False, label='Objet', widget=forms.Select(
        attrs={'class': 'form-control form-control-lg  select2 form-select ', 'data-search': 'on'}))

    class Meta:
        model = Appointment
        fields = ['service', 'doctor', 'date', 'time', 'reason']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }


class HospitalizationForm(forms.ModelForm):
    reason_for_admission = forms.CharField(label='Raison de l\'hospitalisation', widget=TinyMCE(
        attrs={'cols': 5, 'rows': 5, 'class': 'tinymce-basic form-control', 'type': 'textarea'}))
    status = forms.ChoiceField(choices=Patient_statut_choices, label='Status du Patient', widget=forms.Select(
        attrs={'class': 'form-control statid form-control-xl select2 form-select ', 'data-search': 'on',
               'id': 'statid'}))

    class Meta:
        model = Hospitalization
        fields = ['reason_for_admission', 'status']
        widgets = {
            'admission_date': forms.DateInput(attrs={'type': 'date'}),
            'discharge_date': forms.DateInput(attrs={'type': 'date'}),
        }


class ConstantesForm(forms.ModelForm):
    tension_systolique = forms.IntegerField(required=True, widget=forms.NumberInput(
        attrs={'class': 'form-control form-control-lg ', 'placeholder': '120 mmHg '}))
    tension_diastolique = forms.IntegerField(required=True, widget=forms.NumberInput(
        attrs={'class': 'form-control form-control-lg ', 'placeholder': '80 mmHg'}))
    frequence_cardiaque = forms.IntegerField(required=True, widget=forms.NumberInput(
        attrs={'class': 'form-control form-control-lg ', 'placeholder': '72 bpm'}))
    frequence_respiratoire = forms.IntegerField(required=False, widget=forms.NumberInput(
        attrs={'class': 'form-control form-control-lg ', 'placeholder': '16'}))
    temperature = forms.FloatField(required=True,
                                   widget=forms.NumberInput(
                                       attrs={'class': 'form-control form-control-lg ', 'placeholder': '37.3'}))
    saturation_oxygene = forms.IntegerField(required=False, widget=forms.NumberInput(
        attrs={'class': 'form-control form-control-lg ', 'placeholder': '98% SpO2'}))
    glycemie = forms.FloatField(required=False,
                                widget=forms.NumberInput(
                                    attrs={'class': 'form-control form-control-lg ', 'placeholder': '5.8 mmol/L'}))
    poids = forms.FloatField(required=True,
                             widget=forms.NumberInput(
                                 attrs={'class': 'form-control form-control-lg ', 'placeholder': '70.0 kg'}))
    taille = forms.FloatField(required=True,
                              widget=forms.NumberInput(
                                  attrs={'class': 'form-control form-control-lg ', 'placeholder': '175 cm'}))
    pouls = forms.FloatField(required=False, widget=forms.NumberInput(
        attrs={'class': 'form-control form-control-lg ', 'placeholder': '50 bpm'}))
    pb = forms.FloatField(required=False, label='Périmètre brachial', widget=forms.NumberInput(
        attrs={'class': 'form-control form-control-lg ', 'placeholder': '39 cm'}))
    po = forms.FloatField(required=False, label='Périmètre ombilical', widget=forms.NumberInput(
        attrs={'class': 'form-control form-control-lg ', 'placeholder': '10 cm'}))

    # imc = forms.FloatField(widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg ', 'placeholder': 'glycemie'}))

    class Meta:
        model = Constante
        fields = '__all__'
        exclude = ('patient', 'created_by', 'created_at', 'updated_at', 'imc', 'hospitalisation')


class ConsultationSendForm(forms.ModelForm):
    service = forms.ModelChoiceField(queryset=Service.objects.all(), widget=forms.Select(
        attrs={'class': 'form-control form-control-lg  select2 form-select ', 'data-search': 'on', 'id': 'service'}))

    class Meta:
        model = Consultation
        fields = ['service']


class SuiviSendForm(forms.ModelForm):
    class Meta:
        model = Suivi
        fields = [
            'statut_patient', 'adherence_traitement',
            'poids', 'cd4', 'charge_virale', 'observations',
        ]


class HospitalizationreservedForm(forms.ModelForm):
    patient = forms.ModelChoiceField(queryset=Patient.objects.all(), label='Selectionnez le patien à affecter',
                                     widget=forms.Select(
                                         attrs={'class': 'form-control patid form-control-xl select2 form-select ',
                                                'data-search': 'on', 'id': 'patid'}))

    class Meta:
        model = Hospitalization
        fields = ['patient']


class HospitalizationSendForm(forms.ModelForm):
    bed = forms.ModelChoiceField(queryset=LitHospitalisation.objects.filter(occuper=False), required=True,
                                 widget=forms.Select(
                                     attrs={'class': 'form-control bedid form-control-xl select2 form-select ',
                                            'data-search': 'on', 'id': 'bedid'}))

    class Meta:
        model = Hospitalization
        fields = ['bed']

    # def __init__(self, *args, **kwargs):
    #     # Si un ID est passé dans kwargs, utilisez-le. Sinon, générez un ID par défaut.
    #     bed_id = kwargs.pop('bed_id', 'default_bed_id' + str(datetime.now().microsecond))
    #     super().__init__(*args, **kwargs)
    #
    #     # Ajouter l'ID dynamique au champ 'bed'
    #     if 'bed' in self.fields:
    #         self.fields['bed'].widget.attrs.update({
    #             'id': bed_id
    #         })


class ConsultationCreateForm(forms.ModelForm):
    # reason = forms.CharField(widget=forms.TextInput(
    #     attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'nom', }))
    diagnosis = forms.CharField(widget=TinyMCE(attrs={'cols': 5, 'rows': 5, 'class': 'tinymce-basic form-control', }))
    treatment = forms.CharField(widget=TinyMCE(attrs={'cols': 5, 'rows': 5, 'class': 'tinymce-basic form-control ', }))

    # status = forms.CharField(
    #     widget=forms.TextInput(
    #         attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'nom', }))

    class Meta:
        model = Consultation
        fields = ['diagnosis', 'treatment']


class SymptomesForm(forms.ModelForm):
    nom = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))
    date_debut = forms.DateField(required=False, label='date début', widget=forms.TextInput(
        attrs={'class': 'form-control form-control-lg ', 'type': 'date'}))

    class Meta:
        model = Symptomes
        fields = ['nom', 'date_debut']


class AllergiesForm(forms.ModelForm):
    titre = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))

    class Meta:
        model = Allergies
        fields = ['titre']


class EnqueteVihForm(forms.ModelForm):
    antecedents = forms.ModelMultipleChoiceField(
        required=False,
        queryset=MaladieOpportuniste.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                'class': 'form-control  form-control-xl select2 form-select',
                'data-search': 'on', 'id': 'antecedents'
            }
        )
    )
    prophylaxie_antiretrovirale = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-control', 'id': 'prophylaxie_antiretrovirale'})
    )
    prophylaxie_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'prophylaxie_type'})
    )
    traitement_antiretrovirale = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-control', 'id': 'traitement_antiretrovirale'})
    )
    traitement_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'traitement_type'})
    )
    dernier_regime_antiretrovirale = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-control', 'id': 'dernier_regime_antiretrovirale'})
    )
    dernier_regime_antiretrovirale_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'dernier_regime_antiretrovirale_type'})
    )
    score_karnofsky = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'type': 'number', 'id': 'score_karnofsky'})
    )
    traitement_prophylactique_cotrimoxazole = forms.BooleanField(label='Prophylactique cotrimoxazole',
                                                                 required=False,
                                                                 widget=forms.CheckboxInput(
                                                                     attrs={'class': 'form-control',
                                                                            'id': 'traitement_prophylactique_cotrimoxazole'})
                                                                 )
    evolutif_cdc_1993 = forms.ChoiceField(choices=[('Adulte Stade A', 'Adulte Stade A'),
                                                   ('Adulte Stade B', 'Adulte Stade B'),
                                                   ('Adulte Stade C', 'Adulte Stade C'),

                                                   ('Enfant Stade N', 'Enfant Stade N'),
                                                   ('Enfant Stade A', 'Enfant Stade A'),
                                                   ('Enfant Stade B', 'Enfant Stade B'),
                                                   ('Enfant Stade C', 'Enfant Stade C')],
                                          required=False,
                                          widget=forms.Select(
                                              attrs={'class': 'form-control', 'id': 'evolutif_cdc_1993'})
                                          )
    infection_opportuniste = forms.ModelMultipleChoiceField(
        required=False,
        queryset=MaladieOpportuniste.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                'class': 'form-control  form-control-xl select2 form-select',
                'data-search': 'on',
                'id': 'infection_opportuniste'
            }
        )
    )
    sous_traitement = forms.BooleanField(
        label='Patient sous traitement ?',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-control', 'id': 'sous_traitement'})
    )

    class Meta:
        model = EnqueteVih
        fields = '__all__'
        exclude = ('patient', 'descriptif', 'consultation')


class AntecedentsMedicauxForm(forms.ModelForm):
    nom = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))
    descriptif = forms.CharField(required=False,
                                 widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))

    class Meta:
        model = AntecedentsMedicaux
        fields = ['nom', 'descriptif']


class TestRapideVIHForm(forms.ModelForm):
    test_type = forms.ChoiceField(choices=RAPID_HIV_TEST_TYPES, widget=forms.Select(
        attrs={'class': 'form-control form-control-lg form-control-outlined select2 form-select ', 'data-search': 'on',
               'id': 'test_type', 'required': 'true'}))

    class Meta:
        model = TestRapideVIH
        fields = ['resultat', 'commentaire']
        widgets = {
            # 'patient': forms.Select(attrs={'class': 'form-control'}),
            'resultat': forms.Select(attrs={'class': 'form-control', 'required': 'true'}),
            # 'laboratoire': forms.TextInput(attrs={'class': 'form-control'}),
            'commentaire': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ExamenForm(forms.ModelForm):
    analyses = forms.ModelChoiceField(queryset=Analyse.objects.all(), widget=forms.Select(
        attrs={'class': 'form-control examens form-control-xl select2 form-select ', 'data-search': 'on',
               'id': 'examens'}))
    descriptif = forms.CharField(required=False,
                                 widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))

    class Meta:
        model = Examen
        fields = ['analyses']


class EchantillonForm(forms.ModelForm):
    code_echantillon = forms.CharField(required=False,
                                       widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))
    type = forms.ModelChoiceField(queryset=TypeEchantillon.objects.all(), required=False,
                                  widget=forms.Select(attrs={'class': 'form-control form-control-lg '}))
    cathegorie = forms.ModelChoiceField(queryset=CathegorieEchantillon.objects.all(), required=False,
                                        widget=forms.Select(attrs={'class': 'form-control form-control-lg '}))

    date_collect = forms.DateField(required=False,
                                   widget=forms.DateInput(
                                       attrs={'class': 'form-control form-control-lg ', 'type': 'date'}))
    site_collect = forms.CharField(required=False,
                                   widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))

    status_echantillons = forms.CharField(required=False,
                                          widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))
    storage_information = forms.CharField(required=False,
                                          widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))
    storage_location = forms.CharField(required=False,
                                       widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))
    storage_temperature = forms.CharField(required=False,
                                          widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))
    volume = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))
    expiration_date = forms.DateField(required=False,
                                      widget=forms.DateInput(
                                          attrs={'class': 'form-control form-control-lg ', 'type': 'date'}))

    class Meta:
        model = Echantillon
        fields = [
            'code_echantillon', 'type', 'cathegorie', 'date_collect', 'site_collect',
            'status_echantillons', 'storage_information',
            'storage_location', 'storage_temperature', 'volume',
            'expiration_date'
        ]


class PrescriptionForm(forms.ModelForm):
    nom = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))
    descriptif = forms.CharField(required=False,
                                 widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))

    class Meta:
        model = Prescription
        fields = ['nom', 'descriptif']


class ConseilsForm(forms.ModelForm):
    commentaires = forms.CharField(required=False,
                                   widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))

    class Meta:
        model = Consultation
        fields = ['commentaires', ]


# class RendezvousForm(forms.ModelForm):
#     nom = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))
#     descriptif = forms.CharField(required=False,
#                                  widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))
#
#     class Meta:
#         model = Examen
#         fields = ['nom', 'descriptif']


class ProtocolesForm(forms.ModelForm):
    nom = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))
    descriptif = forms.CharField(required=False,
                                 widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))

    class Meta:
        model = Examen
        fields = ['nom', 'descriptif']


class ConstanteForm(forms.ModelForm):
    form_type = forms.CharField(initial="constante", widget=forms.HiddenInput())

    class Meta:
        model = Constante
        fields = ['tension_systolique', 'tension_diastolique', 'frequence_cardiaque', 'frequence_respiratoire',
                  'temperature', 'saturation_oxygene', 'glycemie', 'poids', 'taille', 'pouls']
        widgets = {
            'tension_systolique': forms.NumberInput(attrs={'class': 'form-control'}),
            'tension_diastolique': forms.NumberInput(attrs={'class': 'form-control'}),
            'frequence_cardiaque': forms.NumberInput(attrs={'class': 'form-control'}),
            'frequence_respiratoire': forms.NumberInput(attrs={'class': 'form-control'}),
            'temperature': forms.NumberInput(attrs={'class': 'form-control'}),
            'saturation_oxygene': forms.NumberInput(attrs={'class': 'form-control'}),
            'glycemie': forms.NumberInput(attrs={'class': 'form-control'}),
            'poids': forms.NumberInput(attrs={'class': 'form-control'}),
            'taille': forms.NumberInput(attrs={'class': 'form-control'}),
            'pouls': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class MedicationWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "nom__icontains",

    ]


class PrescriptionHospiForm(forms.ModelForm):
    form_type = forms.CharField(initial="prescription", widget=forms.HiddenInput())

    class Meta:
        model = Prescription
        fields = ['medication', 'quantity', 'posology', 'pendant', 'a_partir_de']
        labels = {
            'medication': 'Médicament',
            'quantity': 'Quantité',
            'posology': 'Posologie',
            'pendant': 'Pendant',
            'a_partir_de': 'À partir de'
        }
        widgets = {
            'medication': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Tapez un médicament (Ex: Nivaquine Comprimé 500 mg)',
                    'autocomplete': 'off',
                    'x-model': 'search',
                    'x-on:input': 'fetchMedications()',
                }
            ),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantité', 'min': '1'}),
            'posology': forms.Select(attrs={'class': 'form-control'}),
            'pendant': forms.Select(attrs={'class': 'form-control'}),
            'a_partir_de': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['posology'].empty_label = "Sélectionnez la posologie"
        self.fields['pendant'].empty_label = "Sélectionnez la durée"
        self.fields['a_partir_de'].empty_label = "Sélectionnez le début"


class SigneFonctionnelForm(forms.ModelForm):
    class Meta:
        model = SigneFonctionnel
        fields = ['nom', 'valeure']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'valeure': forms.Select(attrs={'class': 'form-control'}),
        }


class IndicateurBiologiqueForm(forms.ModelForm):
    form_type = forms.CharField(initial="indicateur_biologique", widget=forms.HiddenInput())

    class Meta:
        model = IndicateurBiologique
        fields = ['globules_blancs', 'hemoglobine', 'plaquettes', 'crp', 'glucose_sanguin']
        widgets = {
            'globules_blancs': forms.NumberInput(attrs={'class': 'form-control'}),
            'hemoglobine': forms.NumberInput(attrs={'class': 'form-control'}),
            'plaquettes': forms.NumberInput(attrs={'class': 'form-control'}),
            'crp': forms.NumberInput(attrs={'class': 'form-control'}),
            'glucose_sanguin': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class IndicateurFonctionnelForm(forms.ModelForm):
    form_type = forms.CharField(initial="indicateur_fonctionnel", widget=forms.HiddenInput())

    class Meta:
        model = IndicateurFonctionnel
        fields = ['mobilite', 'conscience', 'debit_urinaire']
        widgets = {
            'mobilite': forms.Select(attrs={'class': 'form-control'}),
            'conscience': forms.Select(attrs={'class': 'form-control'}),
            'debit_urinaire': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class IndicateurSubjectifForm(forms.ModelForm):
    class Meta:
        model = IndicateurSubjectif
        fields = ['bien_etre']
        widgets = {
            'bien_etre': forms.Select(attrs={'class': 'form-control'}),
        }


class HospitalizationIndicatorsForm(forms.ModelForm):
    form_type = forms.CharField(initial="complication", widget=forms.HiddenInput())

    # temperature = forms.FloatField(
    #     widget=forms.NumberInput(attrs={'class': 'form-control'}),
    #     label="Température (°C)",
    #     required=False
    # )
    # heart_rate = forms.IntegerField(
    #     widget=forms.NumberInput(attrs={'class': 'form-control'}),
    #     label="Fréquence cardiaque (bpm)",
    #     required=False
    # )
    # respiratory_rate = forms.IntegerField(
    #     widget=forms.NumberInput(attrs={'class': 'form-control'}),
    #     label="Fréquence respiratoire (rpm)",
    #     required=False
    # )
    # blood_pressure = forms.CharField(
    #     widget=forms.TextInput(attrs={'class': 'form-control'}),
    #     label="Tension artérielle (mmHg)",
    #     required=False
    # )
    pain_level = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'type': 'number'}),
        label="Niveau de douleur (1 à 10)",
        required=False
    )
    mental_state = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        choices=[('clair', 'Clair'), ('confusion', 'Confusion'), ('somnolent', 'Somnolent')],
        label="État de conscience",
        required=False
    )

    treatment_response = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Réponse au traitement",
        required=False
    )
    side_effects = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Effets secondaires",
        required=False
    )
    compliance = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-control'}),
        label="Observance du traitement",
        required=False
    )
    electrolytes_balance = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Équilibre électrolytique",
        required=False
    )
    renal_function = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Fonction rénale",
        required=False
    )
    hepatic_function = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Fonction hépatique",
        required=False
    )

    stable_vitals = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-control'}),
        label="Signes vitaux stables",
        required=False
    )
    pain_controlled = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-control'}),
        label="Douleur contrôlée",
        required=False
    )
    functional_ability = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-control'}),
        label="Capacité fonctionnelle",
        required=False
    )
    mental_stability = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-control'}),
        label="État mental stable",
        required=False
    )
    follow_up_plan = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Plan de suivi post-hospitalisation",
        required=False
    )

    class Meta:
        model = HospitalizationIndicators
        fields = '__all__'
        exclude = ('hospitalisation',
                   'temperature',
                   'heart_rate',
                   'respiratory_rate',
                   'blood_pressure',
                   )


class PrescriptionExecutionForm(forms.ModelForm):
    class Meta:
        model = PrescriptionExecution
        fields = ['executed_at', 'observations']
        widgets = {
            'executed_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# class HospitalizationIndicatorsForm(forms.Form):
#     # Indicateurs de Complications
#     temperature = forms.FloatField(
#         widget=forms.IntegerField(attrs={'class': 'form-control'}, label="Température (°C)", required=False))
#     heart_rate = forms.IntegerField(label="Fréquence cardiaque (bpm)", required=False)
#     respiratory_rate = forms.IntegerField(label="Fréquence respiratoire (rpm)", required=False)
#     blood_pressure = forms.CharField(label="Tension artérielle (mmHg)", required=False)
#     pain_level = forms.IntegerField(label="Niveau de douleur (1 à 10)", required=False)
#     mental_state = forms.ChoiceField(
#         label="État de conscience",
#         choices=[('clair', 'Clair'), ('confusion', 'Confusion'), ('somnolent', 'Somnolent')],
#         required=False
#     )
#
#     # Indicateurs de Traitement
#     treatment_response = forms.CharField(
#         label="Réponse au traitement",
#         widget=forms.Textarea(attrs={'rows': 3}),
#         required=False
#     )
#     side_effects = forms.CharField(
#         label="Effets secondaires",
#         widget=forms.Textarea(attrs={'rows': 3}),
#         required=False
#     )
#     compliance = forms.BooleanField(label="Observance du traitement", required=False)
#     electrolytes_balance = forms.CharField(label="Équilibre électrolytique", required=False)
#     renal_function = forms.CharField(label="Fonction rénale", required=False)
#     hepatic_function = forms.CharField(label="Fonction hépatique", required=False)
#
#     # Indicateurs de Sortie (Critères de décharge)
#     stable_vitals = forms.BooleanField(label="Signes vitaux stables", required=False)
#     pain_controlled = forms.BooleanField(label="Douleur contrôlée", required=False)
#     functional_ability = forms.BooleanField(label="Capacité fonctionnelle", required=False)
#     mental_stability = forms.BooleanField(label="État mental stable", required=False)
#     follow_up_plan = forms.CharField(
#         label="Plan de suivi post-hospitalisation",
#         widget=forms.Textarea(attrs={'rows': 3}),
#         required=False
#     )
#
#     class Meta:
#         model = HospitalizationIndicators
#         fields = '__All__'
#         widgets = {
#             'temperature': forms.NumberInput(attrs={'class': 'form-control'}),
#             'heart_rate': forms.NumberInput(attrs={'class': 'form-control'}),
#             'respiratory_rate': forms.NumberInput(attrs={'class': 'form-control'}),
#             'blood_pressure': forms.TextInput(attrs={'class': 'form-control'}),
#             'pain_level': forms.NumberInput(attrs={'class': 'form-control'}),
#             'mental_state': forms.Select(attrs={'class': 'form-control'}),
#             'treatment_response': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'side_effects': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'compliance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#             'electrolytes_balance': forms.TextInput(attrs={'class': 'form-control'}),
#             'renal_function': forms.TextInput(attrs={'class': 'form-control'}),
#             'hepatic_function': forms.TextInput(attrs={'class': 'form-control'}),
#             'stable_vitals': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#             'pain_controlled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#             'functional_ability': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#             'mental_stability': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#             'follow_up_plan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#         }

class AdminPasswordChangeForm(forms.Form):
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        strip=False,
    )
    new_password2 = forms.CharField(
        label="Confirmation du mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        strip=False,
    )

    def clean_new_password2(self):
        p1 = self.cleaned_data.get("new_password1")
        p2 = self.cleaned_data.get("new_password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("❌ Les mots de passe ne correspondent pas.")
        return p2


class RoleForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(queryset=Permission.objects.all(), widget=forms.CheckboxSelectMultiple,
                                                 required=False, label="Permissions disponibles", )
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrer le nom du rôle'}))

    class Meta:
        model = Group
        fields = ['name', 'permissions']
        labels = {'name': 'Nom du rôle', }

    def get_permissions_grouped_by_model(self):
        """Groupe les permissions par modèle (content_type)."""
        grouped_permissions = {}
        for permission in self.fields['permissions'].queryset:
            model_name = permission.content_type.model
            if model_name not in grouped_permissions:
                grouped_permissions[model_name] = []
            grouped_permissions[model_name].append(permission)
        return grouped_permissions


class AssignRoleForm(forms.Form):
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,
        label="Rôle",
    )


class EmployeeCreateForm(forms.ModelForm):
    # Champs pour l'utilisateur
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrer votre nom d\'utilisateur'}),
        max_length=150, label="Nom d'utilisateur")
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrer le nom'}), max_length=30,
        label="Prénom")
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrer le prenom'}), max_length=30,
        label="Nom")
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Entrer l\'adresse mail'}),
        label="Email")
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Entrer le mot de passe'}),
        label="Mot de passe")
    role = forms.ModelChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), queryset=Group.objects.all(),
                                  required=True, label="Rôle")

    gender = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), choices=Sexe_choices,
                               required=True, )
    situation_matrimoniale = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}),
                                               choices=situation_matrimoniales_choices, required=True, )

    phone = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrer le numeros de Téléphone'}),
        max_length=30, )

    job_title = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrer le numeros de Téléphone'}),
        max_length=30, )

    class Meta:
        model = Employee
        fields = [
            'username', 'first_name', 'last_name', 'email', 'password',
            'gender', 'situation_matrimoniale', 'phone', 'job_title', 'role'
        ]
        labels = {
            'gender': "Sexe",
            'situation_matrimoniale': "Situation matrimoniale",
            'phone': "Téléphone",
            'job_title': "Titre du poste",
            'role': "Rôle",
        }


class DiagnosticForm(forms.ModelForm):
    class Meta:
        model = Diagnostic
        fields = ['type_diagnostic', 'maladie', 'remarques']
        widgets = {
            'type_diagnostic': forms.Select(attrs={'class': 'form-control ', 'type': 'select2'}),
            'maladie': forms.Select(
                attrs={'class': 'form-control form-control-lg form-control-outlined form-select select2 ',
                       'data-search': 'on', 'id': 'maladie'}),
            'remarques': TinyMCE(attrs={'class': 'tinymce-basic', 'cols': 65, 'rows': 10}),
        }


class ObservationForm(forms.ModelForm):
    class Meta:
        model = Observation
        fields = ['details', 'statut']
        widgets = {
            # 'patient': forms.Select(attrs={'class': 'form-control'}),
            # 'medecin': forms.Select(attrs={'class': 'form-control'}),
            # 'hospitalisation': forms.Select(attrs={'class': 'form-control'}),
            'details': TinyMCE(attrs={'class': 'tinymce-obs', 'cols': 65, 'rows': 10}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            # 'patient': 'Patient',
            # 'medecin': 'Médecin',
            # 'hospitalisation': 'Hospitalisation',
            'details': 'Détails de l\'observation',
            'statut': 'Statut',
        }

    def clean_details(self):
        """Validation personnalisée pour le champ 'details'."""
        details = self.cleaned_data.get('details')
        if len(details) < 10:
            raise forms.ValidationError("Les détails doivent contenir au moins 10 caractères.")
        return details


class AvisMedicalForm(forms.ModelForm):
    class Meta:
        model = AvisMedical
        fields = ['titre', 'contenu']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'contenu': TinyMCE(attrs={'class': 'tinymce-avis', 'cols': 65, 'rows': 10}),

        }


class EffetIndesirableForm(forms.ModelForm):
    class Meta:
        model = EffetIndesirable
        fields = ['description', 'gravite', 'date_apparition', 'medicament_associe', 'observations']
        widgets = {
            'date_apparition': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gravite': forms.Select(attrs={'class': 'form-control'}),
            'medicament_associe': forms.Select(
                attrs={'class': 'form-control form-select select2', 'data-search': 'on'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'observations': TinyMCE(attrs={'class': 'tinymce-effet', 'cols': 65, 'rows': 10}),

        }


class HistoriqueMaladieForm(forms.ModelForm):
    class Meta:
        model = HistoriqueMaladie
        fields = ['description']
        widgets = {
            # 'patient': forms.Select(attrs={'class': 'form-control'}),
            # 'medecin': forms.Select(attrs={'class': 'form-control'}),
            # 'hospitalisation': forms.Select(attrs={'class': 'form-control'}),
            'description': TinyMCE(attrs={'class': 'tinymce-effet', 'cols': 65, 'rows': 10}),

        }
        labels = {
            'description': 'Details',
        }


class CommentaireInfirmierForm(forms.ModelForm):
    class Meta:
        model = CommentaireInfirmier
        fields = ['contenu']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Entrez votre commentaire ici...'
            }),
        }
        labels = {
            'contenu': 'Commentaire',
        }


class MedicamentForm(forms.ModelForm):
    class Meta:
        model = Medicament
        fields = [
            'codebarre', 'nom', 'dosage', 'unitdosage', 'dosage_form',
            'stock', 'date_expiration', 'categorie',
            'fournisseur', 'molecules', 'miniature'
        ]
        widgets = {
            'codebarre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code-barre'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du médicament'}),
            'dosage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Dosage'}),
            'unitdosage': forms.Select(attrs={'class': 'form-control'}),
            'dosage_form': forms.Select(attrs={'class': 'form-control form-select select2', 'data-search': 'on'}),
            # 'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description', 'rows': 3}),
            'stock': forms.NumberInput(
                attrs={'class': 'form-control number-spinner', 'placeholder': 'Quantité en stock'}),
            'date_expiration': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'categorie': forms.Select(attrs={'class': 'form-control form-select select2', 'data-search': 'on'}),
            'fournisseur': forms.Select(attrs={'class': 'form-control'}),
            'molecules': forms.SelectMultiple(attrs={'class': 'form-control form-select select2'}),
            'miniature': forms.FileInput(attrs={'class': 'form-control'}),
        }


class RescheduleAppointmentForm(forms.ModelForm):
    class Meta:
        model = RendezVous
        fields = ['date', 'time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }


class RendezVousForm(forms.ModelForm):
    class Meta:
        model = RendezVous
        fields = [
            'patient',
            # 'pharmacie',
            'medicaments',
            # 'service',
            # 'doctor',
            'date',
            'time',
            'reason',
            # 'status',
            'recurrence',
            'recurrence_end_date',
        ]

        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control form-select select2', 'data-search': 'on'}),
            # 'pharmacie': forms.Select(attrs={'class': 'form-control'}),
            'medicaments': forms.Select(attrs={'class': 'form-control form-select select2', 'data-search': 'on'}),
            # 'service': forms.Select(attrs={'class': 'form-control'}),
            # 'doctor': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
            # 'status': forms.Select(attrs={'class': 'form-control'}),
            'recurrence': forms.Select(attrs={'class': 'form-control'}),
            'recurrence_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

        labels = {
            'patient': 'Patient',
            'pharmacie': 'Pharmacie',
            'medicaments': 'Médicaments',
            # 'service': 'Service',
            'doctor': 'Docteur',
            'date': 'Date',
            'time': 'Heure',
            'reason': 'Motif',
            'status': 'Statut',
            'recurrence': 'Récurrence',
            'recurrence_end_date': 'Fin de la Récurrence',
        }

    def __init__(self, *args, **kwargs):
        # Capture the logged-in user from the view
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        recurrence = cleaned_data.get('recurrence')
        recurrence_end_date = cleaned_data.get('recurrence_end_date')

        # Ensure recurrence end date is after the appointment date
        if recurrence != 'None' and recurrence_end_date and recurrence_end_date <= date:
            self.add_error('recurrence_end_date',
                           "La date de fin de la récurrence doit être après la date du rendez-vous.")

        return cleaned_data

    def save(self, commit=True):
        # Retrieve the instance being saved
        instance = super().save(commit=False)

        # Automatically set the pharmacy and doctor based on the logged-in user
        if self.user and hasattr(self.user, 'employee'):
            instance.pharmacie = self.user.employee.pharmacie
            instance.doctor = self.user.employee

        # Automatically set the status to "Scheduled"
        if not instance.status:
            instance.status = 'Scheduled'

        if commit:
            instance.save()

        return instance


class PatientSearchForm(forms.Form):
    from core.models import Maladie
    maladie = forms.ModelChoiceField(
        queryset=Maladie.objects.all(),
        required=False,
        label="Maladie",
        widget=forms.Select(attrs={'class': 'form-control form-select select2', 'data-search': 'on',
                                   'placeholder': 'Sélectionner une maladie'})
    )
    unite = forms.ModelChoiceField(
        queryset=UniteHospitalisation.objects.all(),
        required=False,
        label="Unite",
        widget=forms.Select(attrs={'class': 'form-control form-select select2', 'data-search': 'on',
                                   'placeholder': 'Sélectionner une maladie'})
    )
    status = forms.ChoiceField(
        choices=[('', 'Tous')] + Patient_statut_choices,
        required=False,
        label="Statut du patient",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    nom_patient = forms.CharField(
        required=False,
        label="Nom du patient",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rechercher par nom'})
    )


class CommandeForm(forms.ModelForm):
    class Meta:
        model = Commande
        fields = ['numero', 'date_commande', 'statut']
        widgets = {
            'numero': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_commande': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
        }


class ArticleCommandeForm(forms.ModelForm):
    class Meta:
        model = ArticleCommande
        fields = ['medicament', 'quantite_commandee', 'fournisseur', 'statut']
        widgets = {
            'medicament': forms.Select(attrs={'class': 'form-control'}),
            'quantite_commandee': forms.NumberInput(attrs={'class': 'form-control'}),
            'fournisseur': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
        }


# Formset pour les articles
ArticleCommandeFormSet = modelformset_factory(ArticleCommande,
                                              form=ArticleCommandeForm,
                                              extra=1,
                                              # Nombre de formulaires supplémentaires pour les nouveaux articles
                                              )


class RdvSuiviForm(forms.ModelForm):
    class Meta:
        model = RendezVous
        fields = [
            'recurrence',
            'recurrence_end_date',
        ]

        widgets = {
            'recurrence': forms.Select(attrs={'class': 'form-control'}),
            'recurrence_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

        labels = {
            'recurrence': 'Récurrence',
            'recurrence_end_date': 'Fin de la Récurrence',
        }

    def __init__(self, *args, **kwargs):
        # Capture the logged-in user from the view
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        recurrence = cleaned_data.get('recurrence')
        recurrence_end_date = cleaned_data.get('recurrence_end_date')

        # Ensure recurrence end date is after the appointment date
        if recurrence != 'None' and recurrence_end_date and recurrence_end_date <= date:
            self.add_error('recurrence_end_date',
                           "La date de fin de la récurrence doit être après la date du rendez-vous.")

        return cleaned_data

    def save(self, commit=True):
        # Retrieve the instance being saved
        instance = super().save(commit=False)

        # Automatically set the pharmacy and doctor based on the logged-in user
        if self.user and hasattr(self.user, 'employee'):
            instance.pharmacie = self.user.employee.pharmacie
            instance.doctor = self.user.employee

        # Automatically set the status to "Scheduled"
        if not instance.status:
            instance.status = 'Scheduled'

        if commit:
            instance.save()

        return instance


class UrgencePatientForm(forms.ModelForm):
    nom = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'nom'}))
    prenoms = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'prenom'}))
    contact = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'type': 'tel', 'class': 'form-control form-control-lg form-control-outlined',
               'placeholder': '0701020304', 'id': 'phone'}))

    lieu_naissance = forms.ChoiceField(required=True, choices=villes_choices, widget=forms.Select(
        attrs={'class': 'form-control form-control-lg form-control-outlined select2 form-select ', 'data-search': 'on',
               'id': 'outlined'}))
    date_naissance = forms.DateField(required=True,
                                     widget=forms.DateInput(
                                         attrs={'class': 'form-control form-control-lg form-control-outlined',
                                                'id': 'outlined',
                                                'type': 'date'}))
    genre = forms.ChoiceField(required=True, choices=Sexe_choices,
                              widget=forms.Select(
                                  attrs={'class': 'form-control form-control-lg form-control-outlined', }))
    nationalite = forms.ChoiceField(required=True, choices=nationalite_choices,
                                    widget=forms.Select(
                                        attrs={
                                            'class': 'form-control form-control-lg form-control-outlined select2 form-select ',
                                            'data-search': 'on', 'id': 'nationalite'}))

    profession = forms.ChoiceField(required=False, choices=professions_choices, widget=forms.Select(
        attrs={'class': 'form-control form-control-lg form-control-outlined select2 form-select ', 'data-search': 'on',
               'id': 'profession'}))

    groupe_sanguin = forms.ChoiceField(required=False, choices=Goupe_sanguin_choices, widget=forms.Select(
        attrs={'class': 'form-control form-control-lg form-control-outlined select2 form-select ', 'data-search': 'on',
               'id': 'groupe_sanguin'}))
    niveau_etude = forms.ChoiceField(required=False, choices=school_level,
                                     widget=forms.Select(
                                         attrs={'class': 'form-control  form-control-lg form-control-outlined',
                                                'id': 'outlined', }))
    employeur = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Fonction Publique', }))

    commune = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-lg form-control-outlined select2 form-select ',
                                   'data-search': 'on', })
    )


    # ➕ “Autre commune”
    nouvelle_commune = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg form-control-outlined',
            'placeholder': 'Entrez la nouvelle commune'
        })
    )

    class Meta:
        model = Patient
        fields = [
            'nom', 'prenoms', 'contact',
            'lieu_naissance', 'date_naissance', 'genre', 'nationalite',
            'profession', 'groupe_sanguin', 'niveau_etude', 'commune', 'nouvelle_commune',
        ]
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def clean_contact(self):
        contact = (self.cleaned_data.get('contact') or '').strip()
        try:
            parsed_number = phonenumbers.parse(contact, 'CI')
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValidationError("Numéro de téléphone invalide.")
        except phonenumbers.phonenumberutil.NumberParseException:
            raise ValidationError("Numéro de téléphone invalide.")
        return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)

    def clean_date_naissance(self):
        date_naissance = self.cleaned_data.get('date_naissance')
        if not date_naissance:
            return date_naissance
        today = datetime.today().date()
        min_age = today - timedelta(days=365)  # ≥ 1 an
        max_age = today - timedelta(days=int(365.25 * 120))  # ≤ 120 ans
        if date_naissance > min_age:
            raise ValidationError("La date de naissance doit être supérieure à 1 an.")
        if date_naissance < max_age:
            raise ValidationError("La date de naissance doit être inférieure à 120 ans.")
        return date_naissance

    def clean(self):
        cleaned = super().clean()
        commune = cleaned.get('commune')
        nouvelle = (cleaned.get('nouvelle_commune') or '').strip()

        if not commune and not nouvelle:
            self.add_error('commune', "Sélectionnez une commune ou ajoutez-en une nouvelle.")
        if nouvelle:
            # crée/récupère Location par nom (case-insensitive)
            obj, _ = Location.objects.get_or_create(name__iexact=nouvelle, defaults={'name': nouvelle})
            cleaned['commune'] = obj
        return cleaned


class UrgenceHospitalizationStep2Form(forms.ModelForm):
    class Meta:
        model = Hospitalization
        fields = ['admission_date', 'bed', 'reason_for_admission', ]
        widgets = {
            'admission_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'reason_for_admission': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'bed': forms.Select(attrs={'class': 'form-control form-select select2', 'data-search': 'on'}),

        }

    def clean(self):
        cleaned = super().clean()
        # Exemple : vérifier que le lit n’est pas déjà occupé (si ta logique existe)
        # bed = cleaned.get('bed')
        # if bed and bed.occupe_actuellement():
        #     self.add_error('bed', "Ce lit est déjà occupé.")
        return cleaned


class HospitalizationDischargeForm(forms.ModelForm):
    discharge_date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }
        ),
        required=True,
        label="Date et heure de sortie"
    )

    class Meta:
        model = Hospitalization
        fields = ['discharge_date', 'status', 'discharge_reason']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'discharge_reason': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }


class HospitalizationUrgenceForm(forms.ModelForm):
    class Meta:
        model = Hospitalization
        fields = ['patient', 'admission_date',
                  'bed', 'reason_for_admission', ]
        widgets = {
            'admission_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            # 'discharge_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            # 'discharge_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'reason_for_admission': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            # 'room': forms.TextInput(attrs={'class': 'form-control'}),
            # 'status': forms.Select(attrs={'class': 'form-control'}),
            'patient': forms.Select(attrs={'class': 'form-control form-select select2', 'data-search': 'on'}),
            # 'activite': forms.Select(attrs={'class': 'form-control'}),
            # 'doctor': forms.Select(attrs={'class': 'form-control'}),
            'bed': forms.Select(attrs={'class': 'form-control form-select select2', 'data-search': 'on'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les patients urgents uniquement
        self.fields['patient'].queryset = Patient.objects.filter(urgence=True)
        # Rendre le champ bed obligatoire
        self.fields['bed'].required = True


class CasContactForm(forms.ModelForm):
    class Meta:
        model = CasContact
        fields = [
            'contact_person',
            'phone_number',
            'relationship',
            'contact_frequency',
            'date_contact',
            'location',
            'prevention_measures',
            'details'
        ]
        widgets = {
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'relationship': forms.Select(attrs={'class': 'form-control'}),
            'contact_frequency': forms.Select(attrs={'class': 'form-control'}),
            'date_contact': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'prevention_measures': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AntecedentsHospiForm(forms.ModelForm):
    class Meta:
        model = AntecedentsMedicaux
        fields = ['type', 'nom', 'descriptif', 'date_debut']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'descriptif': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'type': "Type d'antécédents (Médicaux)",
            'nom': 'Nom',
            'descriptif': 'Descriptif',
            'date_debut': 'Date de début',
        }


class ModeDeVieForm(forms.ModelForm):
    class Meta:
        model = ModeDeVie
        fields = ['categorie', 'description', 'frequence', 'niveau_impact']
        widgets = {
            'categorie': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'frequence': forms.Select(attrs={'class': 'form-control'}),
            'niveau_impact': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'categorie': 'Catégorie de mode de vie',
            'description': 'Détails',
            'frequence': 'Fréquence',
            'niveau_impact': 'Impact sur la santé',
        }


class AppareilForm(forms.ModelForm):
    class Meta:
        model = Appareil
        fields = ['type_appareil', 'nom', 'etat', 'observation']
        widgets = {
            'type_appareil': forms.Select(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de l\'appareil'}),
            'etat': forms.Select(attrs={'class': 'form-control'}),
            'observation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Détails'}),
        }
        labels = {
            'type_appareil': 'Type d\'Appareil',
            'nom': 'Nom de l\'Appareil',
            'etat': 'État de l\'Appareil',
            'observation': 'Observations Médicales',
        }


class ResumeSyndromiqueForm(forms.ModelForm):
    class Meta:
        model = ResumeSyndromique
        fields = ['description']
        widgets = {
            # 'patient': forms.Select(attrs={'class': 'form-control'}),
            # 'hospitalisation': forms.Select(attrs={'class': 'form-control'}),
            'description': TinyMCE(attrs={'class': 'tinymce-effet', 'cols': 65, 'rows': 10}),
            # 'created_by': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            # 'patient': "Patient",
            # 'hospitalisation': "Hospitalisation",
            'description': "Résumé Syndromique",
            # 'created_by': "Ajouté par",
        }


class ProblemePoseForm(forms.ModelForm):
    class Meta:
        model = ProblemePose
        fields = ['description']
        widgets = {
            # 'patient': forms.Select(attrs={'class': 'form-control'}),
            # 'hospitalisation': forms.Select(attrs={'class': 'form-control'}),
            'description': TinyMCE(attrs={'class': 'tinymce-effet', 'cols': 65, 'rows': 10}),
            # 'created_by': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            # 'patient': "Patient",
            # 'hospitalisation': "Hospitalisation",
            'description': "Problème posé",
            # 'created_by': "Ajouté par",
        }


class BilanParacliniqueMultiForm(forms.Form):
    # patient = forms.ModelChoiceField(queryset=Patient.objects.all(), label="Patient")
    # hospitalisation = forms.ModelChoiceField(queryset=Hospitalization.objects.all(), label="Hospitalisation")
    examens = forms.ModelMultipleChoiceField(
        queryset=ExamenStandard.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        required=True,
        label="Sélectionnez les examens"
    )


class ImagerieMedicaleForm(forms.ModelForm):
    class Meta:
        model = ImagerieMedicale
        fields = ["type_imagerie", "prescription", "image_file"]


class GroupedAntecedentsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Récupérer tous les types d'antécédents
        types = TypeAntecedent.objects.all()

        # Pour chaque type, ajouter dynamiquement les champs au formulaire
        for type_antecedent in types:
            self.fields[f"{type_antecedent.id}"] = forms.CharField(label=f"{type_antecedent.nom}", required=False,
                                                                   widget=forms.TextInput(
                                                                       attrs={"class": "form-control",
                                                                              "placeholder": "Nom"})

                                                                   )
            # self.fields[f"{type_antecedent.id}_descriptif"] = forms.CharField(
            #     label=f"{type_antecedent.nom} - Descriptif",
            #     required=False,
            #     widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Descriptif"})
            # )
            self.fields[f"{type_antecedent.id}"] = forms.DateField(
                label=f"{type_antecedent.nom} - Date de début",
                required=False,
                widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
            )


# 📌 Formulaire pour soumettre les résultats des examens
class BilanParacliniqueResultForm(forms.ModelForm):
    class Meta:
        model = BilanParaclinique
        fields = ["result", "result_date", "comment"]
        widgets = {
            "result": forms.TextInput(attrs={"class": "form-control", "placeholder": "Résultat"}),
            "result_date": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Commentaire"}),
        }


class TraitementARVForm(forms.ModelForm):
    class Meta:
        model = TraitementARV
        fields = [
            'nom', 'description', 'dosage', 'forme_pharmaceutique',
            'type_traitement', 'duree_traitement', 'posologie_details',
            'effet_secondaire_courant', 'interaction_medicamenteuse', 'efficacite'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'posologie_details': forms.Textarea(attrs={'rows': 3}),
            'effet_secondaire_courant': forms.Textarea(attrs={'rows': 3}),
            'interaction_medicamenteuse': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            existing_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing_class} form-control'.strip()


class ProtocoleForm(forms.ModelForm):
    class Meta:
        model = Protocole
        fields = [
            'nom', 'description', 'type_protocole', 'duree', 'frequence', 'date_debut',
            'molecules', 'medicament', 'maladies', 'examens'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'date_debut': forms.DateInput(attrs={'class': 'datetime', 'type': 'date'}),
            'molecules': forms.SelectMultiple(attrs={'class': 'select2'}),
            'medicament': forms.SelectMultiple(attrs={'class': 'select2'}),
            'examens': forms.SelectMultiple(attrs={'class': 'select2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget_class = field.widget.attrs.get('class', '')
            # Combine select2 et form-control pour les SelectMultiple
            if isinstance(field.widget, forms.SelectMultiple):
                field.widget.attrs['class'] = f'{widget_class} form-control'.strip()
            else:
                field.widget.attrs['class'] = f'{widget_class} form-control'.strip()


class SuiviProtocoleForm(forms.ModelForm):
    class Meta:
        model = SuiviProtocole
        fields = ['protocole', 'nom', 'description', 'date_debut', 'date_fin']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = f"{field.widget.attrs.get('class', '')} form-control".strip()


class BilanParacliniqueForm(forms.ModelForm):
    class Meta:
        model = BilanParaclinique
        fields = ['examen', 'description', 'doctor', 'is_initial_vih', 'comment']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        patient = kwargs.pop('patient', None)
        super().__init__(*args, **kwargs)
        if patient:
            self.fields['examen'].queryset = ExamenStandard.objects.filter(
                is_active=True
            ).order_by('type_examen__nom', 'nom')
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = f"{field.widget.attrs.get('class', '')} form-control".strip()


class RendezVousSuiviForm(forms.ModelForm):
    class Meta:
        model = RendezVous
        fields = [

            'pharmacie',
            'medicaments',
            # 'service',
            'doctor',
            'date',
            'time',
            'reason',
            # 'status',
            'recurrence',
            'recurrence_end_date',
        ]

        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control form-select select2', 'data-search': 'on'}),
            # 'pharmacie': forms.Select(attrs={'class': 'form-control'}),
            'medicaments': forms.Select(attrs={'class': 'form-control form-select select2', 'data-search': 'on'}),
            # 'service': forms.Select(attrs={'class': 'form-control'}),
            # 'doctor': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
            # 'status': forms.Select(attrs={'class': 'form-control'}),
            'recurrence': forms.Select(attrs={'class': 'form-control'}),
            'recurrence_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

        labels = {
            'patient': 'Patient',
            'pharmacie': 'Pharmacie',
            'medicaments': 'Médicaments',
            # 'service': 'Service',
            'doctor': 'Docteur',
            'date': 'Date',
            'time': 'Heure',
            'reason': 'Motif',
            'status': 'Statut',
            'recurrence': 'Récurrence',
            'recurrence_end_date': 'Fin de la Récurrence',
        }

    def __init__(self, *args, **kwargs):
        # Capture the logged-in user from the view
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        recurrence = cleaned_data.get('recurrence')
        recurrence_end_date = cleaned_data.get('recurrence_end_date')

        # Ensure recurrence end date is after the appointment date
        if recurrence != 'None' and recurrence_end_date and recurrence_end_date <= date:
            self.add_error('recurrence_end_date',
                           "La date de fin de la récurrence doit être après la date du rendez-vous.")

        return cleaned_data

    def save(self, commit=True):
        # Retrieve the instance being saved
        instance = super().save(commit=False)

        # Automatically set the pharmacy and doctor based on the logged-in user
        if self.user and hasattr(self.user, 'employee'):
            instance.pharmacie = self.user.employee.pharmacie
            instance.doctor = self.user.employee

        # Automatically set the status to "Scheduled"
        if not instance.status:
            instance.status = 'Scheduled'

        if commit:
            instance.save()

        return instance


class MouvementStockForm(forms.ModelForm):
    patient = forms.ModelChoiceField(
        queryset=Patient.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-select select2', 'data-search': 'on'})
    )
    fournisseur = forms.ModelChoiceField(
        queryset=Fournisseur.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    commande = forms.ModelChoiceField(
        queryset=Commande.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-select select2', 'data-search': 'on'})
    )

    class Meta:
        model = MouvementStock
        fields = ['medicament', 'quantite', 'type_mouvement', 'patient', 'fournisseur', 'commande']
        widgets = {
            'medicament': forms.Select(attrs={'class': 'form-control form-select select2', 'data-search': 'on'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'type_mouvement': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Adaptation dynamique des champs selon le type de mouvement
        if 'type_mouvement' in self.data:
            mouvement_type = self.data.get('type_mouvement')
            self._adjust_fields_for_mouvement_type(mouvement_type)
        elif self.instance.pk:
            self._adjust_fields_for_mouvement_type(self.instance.type_mouvement)

    def _adjust_fields_for_mouvement_type(self, mouvement_type):
        """Adapte les champs requis selon le type de mouvement"""
        if mouvement_type == 'Entrée':
            self.fields['fournisseur'].required = True
            self.fields['commande'].required = True
            self.fields['patient'].required = False
        elif mouvement_type == 'Sortie':
            self.fields['patient'].required = True
            self.fields['fournisseur'].required = False
            self.fields['commande'].required = False

    def clean(self):
        cleaned_data = super().clean()
        mouvement_type = cleaned_data.get('type_mouvement')
        quantite = cleaned_data.get('quantite')
        medicament = cleaned_data.get('medicament')

        if mouvement_type and quantite and medicament:
            if mouvement_type == 'Sortie' and quantite > medicament.stock:
                raise forms.ValidationError(
                    f"Quantité en sortie ({quantite}) dépasse le stock disponible ({medicament.stock})"
                )

        return cleaned_data


class ResultatAnalyseForm(forms.ModelForm):
    class Meta:
        model = ResultatAnalyse
        fields = [
            'echantillon', 'valeur', 'unite', 'valeur_reference',
            'interpretation', 'fichier_resultat', 'status'
        ]
        widgets = {
            'echantillon': forms.Select(attrs={'class': 'form-select'}),
            'valeur': forms.TextInput(attrs={'class': 'form-control'}),
            'unite': forms.TextInput(attrs={'class': 'form-control'}),
            'valeur_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'interpretation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fichier_resultat': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limiter les choix d'échantillons selon les permissions
        if not self.instance.pk or self.instance.status == 'draft':
            self.fields['status'].choices = [
                ('draft', 'Brouillon'),
                ('pending', 'En attente de validation'),
            ]
        else:
            self.fields['status'].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        valeur = cleaned_data.get('valeur')
        unite = cleaned_data.get('unite')

        if valeur and not unite:
            raise ValidationError("Une unité doit être spécifiée pour les résultats numériques")

        return cleaned_data


class ResultatValidationForm(forms.ModelForm):
    commentaire = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Commentaire de validation"
    )

    class Meta:
        model = ResultatAnalyse
        fields = ['commentaire']
