import django_filters
from django import forms
from django.forms import Select, TextInput

from core.models import situation_matrimoniales_choices, Sexe_choices, Goupe_sanguin_choices, Patient, pays_choices, \
    professions_choices, Employee
from smit.models import BilanParaclinique, TypeBilanParaclinique


class PatientFilter(django_filters.FilterSet):
    code_patient = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Code patient',
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Rechercher par cod patient'})
    )

    nom = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Nom',
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Rechercher par nom'})
    )
    prenoms = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Prénoms',
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Rechercher par prénoms'})
    )
    contact = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Contact',
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Rechercher par contact'})
    )

    nationalite = django_filters.ChoiceFilter(
        choices=pays_choices,
        label='Nationalite',
        widget=Select(attrs={'class': 'form-select select2', 'data-search': 'on', })
    )

    profession = django_filters.ChoiceFilter(
        choices=professions_choices,
        label='Profession',
        widget=Select(attrs={'class': 'form-select select2 ', 'data-search': 'on', })
    )

    situation_matrimoniale = django_filters.ChoiceFilter(
        choices=situation_matrimoniales_choices,
        label='Situation Matrimoniale',
        widget=Select(attrs={'class': 'form-select'})
    )
    genre = django_filters.ChoiceFilter(
        choices=Sexe_choices,
        label='Genre',
        widget=Select(attrs={'class': 'form-select'})
    )
    groupe_sanguin = django_filters.ChoiceFilter(
        choices=Goupe_sanguin_choices,
        label='Groupe Sanguin',
        widget=Select(attrs={'class': 'form-select'})
    )

    # date_naissance = django_filters.DateFromToRangeFilter(
    #     label='Date de Naissance',
    #     widget=django_filters.widgets.RangeWidget(attrs={'class': 'form-control', 'type': 'date'})
    # )

    class Meta:
        model = Patient
        fields = ['code_patient', 'nom', 'prenoms', 'contact', 'nationalite', 'profession', 'situation_matrimoniale',
                  'genre', 'groupe_sanguin']


class ExamenFilter(django_filters.FilterSet):
    type_examen = django_filters.ModelChoiceFilter(
        field_name='examen__type_examen',
        queryset=TypeBilanParaclinique.objects.all(),
        label="Type de bilan",
        empty_label="Tous",
        widget=forms.Select(attrs={'class': 'form-select form-control Select2', 'data-search': 'on'})
    )

    doctor = django_filters.ModelChoiceFilter(
        field_name='doctor',
        queryset=Employee.objects.all(),
        label="Médecin",
        empty_label="Tous",
        widget=forms.Select(attrs={'class': 'form-select form-control Select2', 'data-search': 'on'})
    )

    patient = django_filters.ModelChoiceFilter(
        field_name='patient',
        queryset=Patient.objects.all(),
        label="Patient",
        empty_label="Tous",
        widget=forms.Select(attrs={'class': 'form-select form-control Select2', 'data-search': 'on'})
    )

    class Meta:
        model = BilanParaclinique
        fields = ['type_examen', 'doctor', 'patient']

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     for field in self.form.fields.values():
    #         field.widget.attrs.update({'class': 'form-control'})


class ExamenDoneFilter(django_filters.FilterSet):
    # type_examen = django_filters.CharFilter(field_name='examen__type_examen__nom', lookup_expr='icontains', label="Type de bilan")
    type_examen = django_filters.ModelChoiceFilter(
        field_name='examen__type_examen',
        queryset=TypeBilanParaclinique.objects.all(),
        label="Type de bilan",
        empty_label="Tous",
        widget=forms.Select(attrs={'class': 'form-select form-control Select2', 'data-search': 'on'})
    )

    doctor = django_filters.ModelChoiceFilter(
        field_name='doctor',
        queryset=Employee.objects.all(),
        label="Médecin",
        empty_label="Tous",
        widget=forms.Select(attrs={'class': 'form-select form-control Select2', 'data-search': 'on'})
    )

    patient = django_filters.ModelChoiceFilter(
        field_name='patient',
        queryset=Patient.objects.all(),
        label="Patient",
        empty_label="Tous",
        widget=forms.Select(attrs={'class': 'form-select form-control Select2', 'data-search': 'on'})
    )

    class Meta:
        model = BilanParaclinique
        fields = []

    def filter_patient(self, queryset, name, value):
        return queryset.filter(
            patient__nom__icontains=value
        ) | queryset.filter(
            patient__prenoms__icontains=value
        )

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     # ✅ Ajout de la classe Bootstrap "form-control"
    #     for field in self.form.fields.values():
    #         field.widget.attrs.update({
    #             'class': 'form-control',
    #             'placeholder': field.label
    #         })


