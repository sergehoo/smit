from django.core.management.base import BaseCommand
from datetime import date, timedelta

from pharmacy.models import CathegorieMolecule, Molecule, Fournisseur, Medicament


class Command(BaseCommand):
    help = 'Add default medications for diseases: VIH, Tuberculose, COVID-19, and IST'

    def handle(self, *args, **kwargs):
        # Catégories et molécules d'exemple
        categorie_vih, _ = CathegorieMolecule.objects.get_or_create(nom="VIH")
        categorie_tb, _ = CathegorieMolecule.objects.get_or_create(nom="Tuberculose")
        categorie_covid, _ = CathegorieMolecule.objects.get_or_create(nom="COVID-19")
        categorie_ist, _ = CathegorieMolecule.objects.get_or_create(nom="IST")
        categorie_diabete, _ = CathegorieMolecule.objects.get_or_create(nom="diabete")
        categorie_hypertension, _ = CathegorieMolecule.objects.get_or_create(nom="hypertension")
        categorie_cardio, _ = CathegorieMolecule.objects.get_or_create(nom="cardio")
        categorie_asthme, _ = CathegorieMolecule.objects.get_or_create(nom="asthme")
        categorie_analgesique, _ = CathegorieMolecule.objects.get_or_create(nom="analgesique")
        categorie_antiinfectieux, _ = CathegorieMolecule.objects.get_or_create(nom="antiinfectieux")

        # Molécules d'exemple pour chaque maladie
        mol_vih, _ = Molecule.objects.get_or_create(nom="Lamivudine")
        mol_tb, _ = Molecule.objects.get_or_create(nom="Rifampicine")
        mol_covid, _ = Molecule.objects.get_or_create(nom="Dexamethasone")
        mol_ist, _ = Molecule.objects.get_or_create(nom="Azithromycine")
        mol_diabete, _ = Molecule.objects.get_or_create(nom="mol_diabete")
        mol_hypertension, _ = Molecule.objects.get_or_create(nom="mol_hypertension")
        mol_cardio, _ = Molecule.objects.get_or_create(nom="mol_cardio")
        mol_asthme, _ = Molecule.objects.get_or_create(nom="mol_asthme")
        mol_analgesique, _ = Molecule.objects.get_or_create(nom="mol_analgesique")
        mol_antiinfectieux, _ = Molecule.objects.get_or_create(nom="mol_antiinfectieux")


        # Fournisseur d'exemple
        fournisseur, _ = Fournisseur.objects.get_or_create(nom="PharmaProvider")

        # Liste des médicaments par catégorie
        medications = [
            # Médicaments pour le VIH
            {
                'nom': 'Lamivudine',
                'dosage': 150,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_vih,
                'molecules': [mol_vih],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            {
                'nom': 'Tenofovir',
                'dosage': 300,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_vih,
                'molecules': [mol_vih],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=730),
            },
            {
                'nom': 'Efavirenz',
                'dosage': 600,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_vih,
                'molecules': [mol_vih],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=730),
            },
            {
                'nom': 'Dolutegravir',
                'dosage': 50,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_vih,
                'molecules': [mol_vih],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            {
                'nom': 'Emtricitabine',
                'dosage': 200,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_vih,
                'molecules': [mol_vih],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            # Médicaments pour la Tuberculose
            {
                'nom': 'Isoniazide',
                'dosage': 300,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_tb,
                'molecules': [mol_tb],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            {
                'nom': 'Ethambutol',
                'dosage': 400,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_tb,
                'molecules': [mol_tb],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            {
                'nom': 'Pyrazinamide',
                'dosage': 500,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_tb,
                'molecules': [mol_tb],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            # Médicaments pour le COVID-19
            {
                'nom': 'Dexamethasone',
                'dosage': 6,
                'unitdosage': 'mg',
                'dosage_form': 'Injection',
                'categorie': categorie_covid,
                'molecules': [mol_covid],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=180),
            },
            {
                'nom': 'Remdesivir',
                'dosage': 100,
                'unitdosage': 'mg',
                'dosage_form': 'Injection',
                'categorie': categorie_covid,
                'molecules': [mol_covid],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            # Médicaments pour les IST
            {
                'nom': 'Azithromycine',
                'dosage': 500,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_ist,
                'molecules': [mol_ist],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=730),
            },
            {
                'nom': 'Doxycycline',
                'dosage': 100,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_ist,
                'molecules': [mol_ist],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            {
                'nom': 'Metronidazole',
                'dosage': 500,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_ist,
                'molecules': [mol_ist],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },

            # Médicaments pour le VIH
            {
                'nom': 'Lamivudine',
                'dosage': 150,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_vih,
                'molecules': [mol_vih],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            {
                'nom': 'Tenofovir',
                'dosage': 300,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_vih,
                'molecules': [mol_vih],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            {
                'nom': 'Efavirenz',
                'dosage': 600,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_vih,
                'molecules': [mol_vih],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            # Médicaments pour la Tuberculose
            {
                'nom': 'Isoniazide',
                'dosage': 300,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_tb,
                'molecules': [mol_tb],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            {
                'nom': 'Rifampicine',
                'dosage': 600,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_tb,
                'molecules': [mol_tb],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            # Médicaments pour le COVID-19
            {
                'nom': 'Dexaméthasone',
                'dosage': 6,
                'unitdosage': 'mg',
                'dosage_form': 'Injection',
                'categorie': categorie_covid,
                'molecules': [mol_covid],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            {
                'nom': 'Remdésivir',
                'dosage': 100,
                'unitdosage': 'mg',
                'dosage_form': 'Injection',
                'categorie': categorie_covid,
                'molecules': [mol_covid],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            # Médicaments pour les IST
            {
                'nom': 'Azithromycine',
                'dosage': 500,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_ist,
                'molecules': [mol_ist],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            {
                'nom': 'Doxycycline',
                'dosage': 100,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_ist,
                'molecules': [mol_ist],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            # Médicaments pour le Diabète
            {
                'nom': 'Metformine',
                'dosage': 500,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_diabete,
                'molecules': [mol_diabete],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            {
                'nom': 'Glibenclamide',
                'dosage': 5,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_diabete,
                'molecules': [mol_diabete],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            # Médicaments pour l'Hypertension
            {
                'nom': 'Amlodipine',
                'dosage': 5,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_hypertension,
                'molecules': [mol_hypertension],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            {
                'nom': 'Lisinopril',
                'dosage': 10,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_hypertension,
                'molecules': [mol_hypertension],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            # Médicaments pour les Maladies Cardiovasculaires
            {
                'nom': 'Aspirine',
                'dosage': 81,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_cardio,
                'molecules': [mol_cardio],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            {
                'nom': 'Clopidogrel',
                'dosage': 75,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_cardio,
                'molecules': [mol_cardio],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            # Médicaments pour l'Asthme et les Allergies
            {
                'nom': 'Salbutamol',
                'dosage': 100,
                'unitdosage': 'µg',
                'dosage_form': 'Inhalateur',
                'categorie': categorie_asthme,
                'molecules': [mol_asthme],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            {
                'nom': 'Fluticasone',
                'dosage': 125,
                'unitdosage': 'µg',
                'dosage_form': 'Inhalateur',
                'categorie': categorie_asthme,
                'molecules': [mol_asthme],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            # Médicaments Analgésiques et Anti-inflammatoires
            {
                'nom': 'Paracétamol',
                'dosage': 500,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_analgesique,
                'molecules': [mol_analgesique],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            {
                'nom': 'Ibuprofène',
                'dosage': 400,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_analgesique,
                'molecules': [mol_analgesique],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            # Médicaments Anti-infectieux Généraux
            {
                'nom': 'Amoxicilline',
                'dosage': 500,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_antiinfectieux,
                'molecules': [mol_antiinfectieux],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            {
                'nom': 'Ciprofloxacine',
                'dosage': 500,
                'unitdosage': 'mg',
                'dosage_form': 'Comprimé',
                'categorie': categorie_antiinfectieux,
                'molecules': [mol_antiinfectieux],
                'fournisseur': fournisseur,
                'date_expiration': date.today() + timedelta(days=365),
            },
            # Ajoutez plus de médicaments ici
        ]

        # Ajout de chaque médicament
        for med in medications:
            medication, created = Medicament.objects.get_or_create(
                nom=med['nom'],
                defaults={
                    'dosage': med['dosage'],
                    'unitdosage': med['unitdosage'],
                    'dosage_form': med['dosage_form'],
                    'categorie': med['categorie'],
                    'fournisseur': med['fournisseur'],
                    'date_expiration': med['date_expiration'],
                }
            )
            if created:
                medication.molecules.set(med['molecules'])
                medication.save()
                self.stdout.write(self.style.SUCCESS(f'Médicament ajouté: {med["nom"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Médicament existant: {med["nom"]}'))