import django_filters
from django.forms import Select, TextInput

from core.models import situation_matrimoniales_choices, Sexe_choices, Goupe_sanguin_choices, Patient, pays_choices, \
    professions_choices


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
