import uuid
from datetime import datetime, timedelta

import phonenumbers
from django import forms
from django.contrib.auth.models import Permission, Group
from django.core.exceptions import ValidationError
from django_countries.fields import CountryField
from tinymce.widgets import TinyMCE

from core.models import situation_matrimoniales_choices, villes_choices, Sexe_choices, pays_choices, \
    professions_choices, Goupe_sanguin_choices, communes_et_quartiers_choices, nationalite_choices, \
    Patient_statut_choices, Location, Maladie

from laboratory.models import Echantillon, TypeEchantillon, CathegorieEchantillon
from pharmacy.models import Medicament, RendezVous, ArticleCommande
from smit.models import Patient, Appointment, Service, Employee, Constante, \
    Hospitalization, Consultation, Symptomes, Allergies, AntecedentsMedicaux, Examen, Prescription, LitHospitalisation, \
    Analyse, TestRapideVIH, RAPID_HIV_TEST_TYPES, EnqueteVih, MaladieOpportuniste, SigneFonctionnel, \
    IndicateurBiologique, IndicateurFonctionnel, IndicateurSubjectif, HospitalizationIndicators, PrescriptionExecution, \
    Diagnostic, AvisMedical, EffetIndesirable, HistoriqueMaladie, Observation, CommentaireInfirmier

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

    commune = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-lg form-control-outlined select2 form-select ',
                                   'data-search': 'on', 'id': 'commune'})
    )

    code_vih = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Code VIH', }))

    class Meta:
        model = Patient
        fields = [
            'nom', 'prenoms', 'contact', 'situation_matrimoniale',
            'lieu_naissance', 'date_naissance', 'genre', 'nationalite',
            'profession', 'nbr_enfants', 'groupe_sanguin', 'niveau_etude',
            'employeur', 'commune', 'code_vih'
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

    def clean_commune(self):
        commune = self.cleaned_data.get('commune')
        nouvelle_commune = self.cleaned_data.get('nouvelle_commune')

        if not commune and not nouvelle_commune:
            raise ValidationError("Veuillez sélectionner une commune ou en ajouter une nouvelle.")

        if nouvelle_commune:
            # Si une nouvelle commune est renseignée, elle est prioritaire
            # Vous pouvez ajouter une logique pour enregistrer cette nouvelle commune dans votre base de données ici
            # Exemple :
            # Commune.objects.get_or_create(name=nouvelle_commune)
            return nouvelle_commune

        return commune

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
    pouls = forms.FloatField(required=False,
                             widget=forms.NumberInput(
                                 attrs={'class': 'form-control form-control-lg ', 'placeholder': '50 bpm'}))

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


class HospitalizationreservedForm(forms.ModelForm):
    patient = forms.ModelChoiceField(queryset=Patient.objects.all(), label='Selectionnez le patien à affecter',
                                     widget=forms.Select(
                                         attrs={'class': 'form-control patid form-control-xl select2 form-select ',
                                                'data-search': 'on', 'id': 'patid'}))

    class Meta:
        model = Hospitalization
        fields = ['patient']


class HospitalizationSendForm(forms.ModelForm):
    bed = forms.ModelChoiceField(queryset=LitHospitalisation.objects.filter(occuper=False), widget=forms.Select(
        attrs={'class': 'form-control bedid form-control-xl select2 form-select ', 'data-search': 'on', 'id': 'bedid'}))

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
               'id': 'test_type'}))

    class Meta:
        model = TestRapideVIH
        fields = ['resultat', 'commentaire']
        widgets = {
            # 'patient': forms.Select(attrs={'class': 'form-control'}),
            'resultat': forms.Select(attrs={'class': 'form-control'}),
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


class RendezvousForm(forms.ModelForm):
    nom = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))
    descriptif = forms.CharField(required=False,
                                 widget=forms.TextInput(attrs={'class': 'form-control form-control-lg '}))

    class Meta:
        model = Examen
        fields = ['nom', 'descriptif']


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


class PrescriptionHospiForm(forms.ModelForm):
    form_type = forms.CharField(initial="prescription", widget=forms.HiddenInput())

    class Meta:
        model = Prescription
        fields = ['medication', 'quantity', 'posology', 'pendant', 'a_partir_de']
        labels = {
            'medication': 'Médicament',
            'quantity': 'Quantité',
            'posology': 'Posologie',
        }
        widgets = {
            'medication': forms.Select(
                attrs={
                    'class': 'form-control form-control-lg form-control-outlined select2 form-select',
                    'data-search': 'on',
                    'id': 'medication',
                }
            ),
            'quantity': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'value': '0',
                    'placeholder': 'Entrez la quantité',
                    'type': 'number'
                }
            ),
            'posology': forms.Select(
                attrs={
                    'class': 'form-control form-control-lg form-control-outlined select2 form-select',
                    'data-search': 'on',
                    'id': 'posology'
                }
            ),

            'pendant': forms.Select(
                attrs={
                    'class': 'form-control form-control-lg form-control-outlined select2 form-select',
                    'data-search': 'on',
                    'id': 'pendant'
                }
            ),

            'a_partir_de': forms.Select(
                attrs={
                    'class': 'form-control form-control-lg form-control-outlined select2 form-select',
                    'data-search': 'on',
                    'id': 'a_partir_de'
                }
            ),
            'form_type': forms.CharField(initial="prescription", widget=forms.HiddenInput())
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add an empty label as a placeholder for Select fields
        self.fields['medication'].empty_label = "Sélectionnez un médicament"
        self.fields['posology'].empty_label = "Sélectionnez la posologie"


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
            'type_diagnostic': forms.Select(attrs={'class': 'form-control', 'type': 'select'}),
            'maladie': forms.Select(attrs={'class': 'form-control form-select select2', 'data-search': 'on'}),
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
        fields = ['description', 'antecedents', 'diagnostics_associes',
                  'traitements_precedents', 'observations']
        widgets = {
            # 'patient': forms.Select(attrs={'class': 'form-control'}),
            # 'medecin': forms.Select(attrs={'class': 'form-control'}),
            # 'hospitalisation': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Description de l\'évolution de la maladie'
            }),
            'antecedents': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Antécédents médicaux pertinents'
            }),
            'diagnostics_associes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Diagnostics associés'
            }),
            'traitements_precedents': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Traitements administrés par le passé'
            }),
            'observations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observations médicales'
            }),
        }
        labels = {
            'patient': 'Patient',
            'medecin': 'Médecin',
            'hospitalisation': 'Hospitalisation',
            'description': 'Description',
            'antecedents': 'Antécédents médicaux',
            'diagnostics_associes': 'Diagnostics associés',
            'traitements_precedents': 'Traitements précédents',
            'observations': 'Observations',
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
    maladie = forms.ModelChoiceField(
        queryset=Maladie.objects.all(),
        required=False,
        label="Maladie",
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
