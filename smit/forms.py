import uuid
from datetime import datetime

import phonenumbers
from django import forms
from django.core.exceptions import ValidationError
from django_countries.fields import CountryField
from tinymce.widgets import TinyMCE

from core.models import situation_matrimoniales_choices, villes_choices, Sexe_choices, pays_choices, \
    professions_choices, Goupe_sanguin_choices, communes_et_quartiers_choices, nationalite_choices, \
    Patient_statut_choices
from laboratory.models import Echantillon, TypeEchantillon, CathegorieEchantillon
from smit.models import Patient, Appointment, Service, Employee, Constante, \
    Hospitalization, Consultation, Symptomes, Allergies, AntecedentsMedicaux, Examen, Prescription, LitHospitalisation, \
    Analyse, TestRapideVIH, RAPID_HIV_TEST_TYPES, EnqueteVih, MaladieOpportuniste, SigneFonctionnel, \
    IndicateurBiologique, IndicateurFonctionnel, IndicateurSubjectif, HospitalizationIndicators

school_level = [
    ('Inconnu', 'Inconnu'),
    ('Non-scolarisé', 'Non-scolarisé'),
    ('Primaire', 'Primaire'),
    ('Secondaire', 'Secondaire'),
    ('Universitaire', 'Universitaire'),

]
ethnic_groups = [
    # AKAN Group
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


class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['activite', 'patient', 'constante', 'symptomes', 'antecedentsMedicaux', 'examens', 'allergies',
                  'services', 'doctor', 'consultation_date', 'reason', 'diagnosis', 'commentaires', 'suivi', 'status',
                  'hospitalised', 'requested_at', 'motifrejet', 'validated_at']


class PatientCreateForm(forms.ModelForm):
    nom = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'nom', }))
    prenoms = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'prenom', }))

    contact = forms.CharField(
        widget=forms.TextInput(
            attrs={'type': 'tel', 'class': 'form-control form-control-lg form-control-outlined',
                   'placeholder': '0701020304', 'id': 'phone'}))

    situation_matrimoniale = forms.ChoiceField(choices=situation_matrimoniales_choices, widget=forms.Select(
        attrs={'class': 'form-control form-control-lg form-control-outlined select2 form-select ',
               'data-search': 'on', 'id': 'situation_matrimoniale'}))
    lieu_naissance = forms.ChoiceField(choices=villes_choices, widget=forms.Select(
        attrs={'class': 'form-control form-control-lg form-control-outlined select2 form-select ', 'data-search': 'on',
               'id': 'outlined'}))
    date_naissance = forms.DateField(
        widget=forms.DateInput(
            attrs={'class': 'form-control form-control-lg form-control-outlined', 'id': 'outlined',
                   'type': 'date'}))
    genre = forms.ChoiceField(choices=Sexe_choices,
                              widget=forms.Select(
                                  attrs={'class': 'form-control form-control-lg form-control-outlined', }))
    nationalite = forms.ChoiceField(choices=nationalite_choices,
                                    widget=forms.Select(
                                        attrs={
                                            'class': 'form-control form-control-lg form-control-outlined select2 form-select ',
                                            'data-search': 'on', 'id': 'nationalite'}))
    ethnie = forms.ChoiceField(choices=ethnic_groups,
                               widget=forms.Select(
                                   attrs={
                                       'class': 'form-control form-control-lg form-control-outlined select2 form-select ',
                                       'data-search': 'on', 'id': 'nationalite'}))
    profession = forms.ChoiceField(choices=professions_choices, widget=forms.Select(
        attrs={'class': 'form-control form-control-lg form-control-outlined select2 form-select ', 'data-search': 'on',
               'id': 'profession'}))

    nbr_enfants = forms.IntegerField(widget=forms.NumberInput(
        attrs={'class': 'form-control form-control-lg number-spinner', 'value': '0', 'type': 'number'}))

    groupe_sanguin = forms.ChoiceField(choices=Goupe_sanguin_choices, widget=forms.Select(
        attrs={'class': 'form-control form-control-lg form-control-outlined select2 form-select ', 'data-search': 'on',
               'id': 'groupe_sanguin'}))
    niveau_etude = forms.ChoiceField(choices=school_level,
                                     widget=forms.Select(
                                         attrs={'class': 'form-control  form-control-lg form-control-outlined',
                                                'id': 'outlined', }))
    employeur = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Fonction Publique', }))

    pays = CountryField().formfield(
        initial="CI",  # Set the default to Côte d'Ivoire
        widget=forms.Select(
            attrs={
                'class': 'form-control form-control-lg form-control-outlined select2 form-select',
                'data-search': 'on',
                'id': 'pays'}))

    commune = forms.ChoiceField(choices=communes_et_quartiers_choices, widget=forms.Select(
        attrs={'class': 'form-control form-control-lg form-control-outlined select2 form-select ', 'data-search': 'on',
               'id': 'commune'}))
    code_vih = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control form-control-lg form-control-outlined', 'placeholder': 'Code VIH', }))

    class Meta:
        model = Patient
        fields = [
            'nom', 'prenoms', 'contact', 'situation_matrimoniale',
            'lieu_naissance', 'date_naissance', 'genre', 'nationalite',
            'profession', 'nbr_enfants', 'groupe_sanguin', 'niveau_etude',
            'employeur', 'commune','code_vih'
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


class AppointmentForm(forms.ModelForm):
    patient = forms.ModelChoiceField(queryset=Patient.objects.all(), widget=forms.Select(
        attrs={'class': 'form-control form-control-xl select2 form-select ', 'data-search': 'on',
               'id': 'patient'}))
    service = forms.ModelChoiceField(queryset=Service.objects.all(), widget=forms.Select(
        attrs={'class': 'form-control form-control-lg  select2 form-select ', 'data-search': 'on',
               'id': 'service'}))

    doctor = forms.ModelChoiceField(queryset=Employee.objects.all(), widget=forms.Select(
        attrs={'class': 'form-control form-control-lg  select2 form-select ', 'data-search': 'on',
               'id': 'outlined'}))

    date = forms.DateField(label='Date du rendez-vous', widget=forms.DateInput(
        attrs={'class': 'form-control form-control-lg', 'type': 'date', 'data-date-format': 'dd/mm/yyyy'}))

    time = forms.TimeField(label='Heure du rendez-vous', widget=forms.TimeInput(
        attrs={'class': 'form-control form-control-lg ', 'type': 'time'}))

    reason = forms.CharField(required=False, label='Objet', widget=forms.TextInput(
        attrs={'class': 'form-control form-control-lg ', 'id': 'outlined', }))

    class Meta:
        model = Appointment
        fields = ['patient', 'service', 'doctor', 'date', 'time', 'reason']
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
    tension_systolique = forms.IntegerField(required=True,widget=forms.NumberInput(
        attrs={'class': 'form-control form-control-lg ', 'placeholder': '120 mmHg '}))
    tension_diastolique = forms.IntegerField(required=True,widget=forms.NumberInput(
        attrs={'class': 'form-control form-control-lg ', 'placeholder': '80 mmHg'}))
    frequence_cardiaque = forms.IntegerField(required=True,widget=forms.NumberInput(
        attrs={'class': 'form-control form-control-lg ', 'placeholder': '72 bpm'}))
    frequence_respiratoire = forms.IntegerField(required=False,widget=forms.NumberInput(
        attrs={'class': 'form-control form-control-lg ', 'placeholder': '16'}))
    temperature = forms.FloatField(required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg ', 'placeholder': '37.3'}))
    saturation_oxygene = forms.IntegerField(required=False,widget=forms.NumberInput(
        attrs={'class': 'form-control form-control-lg ', 'placeholder': '98% SpO2'}))
    glycemie = forms.FloatField(required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg ', 'placeholder': '5.8 mmol/L'}))
    poids = forms.FloatField(required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg ', 'placeholder': '70.0 kg'}))
    taille = forms.FloatField(required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg ', 'placeholder': '175 cm'}))
    pouls = forms.FloatField(required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg ', 'placeholder': '50 bpm'}))

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
    class Meta:
        model = Prescription
        fields = ['patient', 'doctor', 'medication', 'quantity', 'status']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'medication': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class SigneFonctionnelForm(forms.ModelForm):
    class Meta:
        model = SigneFonctionnel
        fields = ['nom', 'valeure']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'valeure': forms.Select(attrs={'class': 'form-control'}),
        }


class IndicateurBiologiqueForm(forms.ModelForm):
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
