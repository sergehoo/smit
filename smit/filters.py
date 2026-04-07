import django_filters
from django import forms
from django.forms import Select, TextInput

from core.models import situation_matrimoniales_choices, Sexe_choices, Goupe_sanguin_choices, Patient, pays_choices, \
    professions_choices, Employee
from smit.models import BilanParaclinique, TypeBilanParaclinique


class PatientFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(
        field_name="nom",
        lookup_expr="icontains",
        label="Nom"
    )
    prenoms = django_filters.CharFilter(
        field_name="prenoms",
        lookup_expr="icontains",
        label="Prénoms"
    )
    code_patient = django_filters.CharFilter(
        field_name="code_patient",
        lookup_expr="icontains",
        label="Code patient"
    )
    contact = django_filters.CharFilter(
        field_name="contact",
        lookup_expr="icontains",
        label="Contact"
    )
    genre = django_filters.ChoiceFilter(
        field_name="genre",
        choices=Patient._meta.get_field("genre").choices,
        label="Sexe",
        widget = forms.Select(attrs={"class": "form-control"})
    )

    # période d'enregistrement patient
    created_at_after = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__gte",
        label="Enregistré du",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    created_at_before = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__lte",
        label="Enregistré au",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )

    # période consultation
    consultation_after = django_filters.DateFilter(
        method="filter_consultation_after",
        label="Consultation du",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    consultation_before = django_filters.DateFilter(
        method="filter_consultation_before",
        label="Consultation au",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )

    # période hospitalisation
    hospitalization_after = django_filters.DateFilter(
        method="filter_hospitalization_after",
        label="Hospitalisation du",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    hospitalization_before = django_filters.DateFilter(
        method="filter_hospitalization_before",
        label="Hospitalisation au",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )

    # type de parcours
    passage_type = django_filters.ChoiceFilter(
        method="filter_passage_type",
        label="Passage",
        choices=[
            ("", "Tous"),
            ("consultation", "Consultation"),
            ("hospitalisation", "Hospitalisation"),
            ("both", "Consultation + Hospitalisation"),
        ],
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = Patient
        fields = [
            "nom",
            "prenoms",
            "code_patient",
            "contact",
            "genre",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # classes bootstrap/dashlite
        for name, field in self.form.fields.items():
            if not isinstance(field.widget, (forms.DateInput, forms.Select)):
                field.widget.attrs["class"] = "form-control"

    def filter_consultation_after(self, queryset, name, value):
        return queryset.filter(consultation__consultation_date__date__gte=value).distinct()

    def filter_consultation_before(self, queryset, name, value):
        return queryset.filter(consultation__consultation_date__date__lte=value).distinct()

    def filter_hospitalization_after(self, queryset, name, value):
        return queryset.filter(hospitalized__admission_date__date__gte=value).distinct()

    def filter_hospitalization_before(self, queryset, name, value):
        return queryset.filter(hospitalized__admission_date__date__lte=value).distinct()

    def filter_passage_type(self, queryset, name, value):
        if value == "consultation":
            return queryset.filter(consultation__isnull=False).distinct()

        if value == "hospitalisation":
            return queryset.filter(hospitalized__isnull=False).distinct()

        if value == "both":
            return queryset.filter(
                consultation__isnull=False,
                hospitalized__isnull=False
            ).distinct()

        return queryset


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


