import os
import django
from django.contrib.auth.models import User
from faker import Faker
import random

from pharmacy.models import Medicament, Molecule, CathegorieMolecule
from smit.models import Employee, Patient, Constante, Consultation, Symptomes, AntecedentsMedicaux, Allergies, \
    ServiceSubActivity, Service

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smitci.settings')
django.setup()
#
# fake = Faker()
#
#
# def create_fake_user():
#     user = User.objects.create_user(
#         username=fake.unique.user_name(),
#         email=fake.email(),
#         password='password123',
#         first_name=fake.first_name(),
#         last_name=fake.last_name()
#     )
#     return user
#
#
# def create_fake_employee():
#     user = create_fake_user()
#     return Employee.objects.create(
#         user=user,
#         # Remplissez les champs nécessaires pour Employee
#     )
#
#
# def create_fake_patient():
#     return Patient.objects.create(
#         user=None,
#         code_patient=fake.unique.bothify(text='???-#####'),
#         nom=fake.last_name(),
#         prenoms=fake.first_name(),
#         contact=fake.phone_number(),
#         situation_matrimoniale=random.choice(['Célibataire', 'Marié', 'Divorcé', 'Veuf']),
#         lieu_naissance=fake.city(),
#         date_naissance=fake.date_of_birth(minimum_age=18, maximum_age=90),
#         genre=random.choice(['Masculin', 'Féminin']),
#         nationalite=fake.country(),
#         profession=fake.job(),
#         nbr_enfants=random.randint(0, 5),
#         groupe_sanguin=random.choice(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']),
#         niveau_etude=fake.word(),
#         employeur=fake.company(),
#         created_by=create_fake_employee(),
#         avatar=None,
#         localite=None,
#         status=random.choice(['Actif', 'Inactif'])
#     )
#
#
# def create_fake_constante(patient):
#     return Constante.objects.create(
#         patient=patient,
#         tension_systolique=random.randint(90, 140),
#         tension_diastolique=random.randint(60, 90),
#         frequence_cardiaque=random.randint(60, 100),
#         frequence_respiratoire=random.randint(12, 20),
#         temperature=round(random.uniform(36.5, 37.5), 1),
#         saturation_oxygene=random.randint(90, 100),
#         glycemie=round(random.uniform(70, 140), 1),
#         poids=round(random.uniform(50, 100), 1),
#         taille=round(random.uniform(1.5, 2.0), 2),
#         pouls=round(random.uniform(60, 100), 1),
#         imc=round(random.uniform(18.5, 30.0), 1),
#         created_by=create_fake_employee()
#     )
#
#
# def create_fake_consultation(patient, constante):
#     consultation = Consultation.objects.create(
#         activite=ServiceSubActivity.objects.order_by('?').first(),
#         patient=patient,
#         constante=constante,
#         examens=None,
#         services=Service.objects.order_by('?').first(),
#         doctor=create_fake_employee(),
#         consultation_date=fake.date_time_this_year(),
#         reason=fake.text(),
#         diagnosis=fake.text(),
#         commentaires=fake.text(),
#         suivi=Service.objects.order_by('?').first(),
#         status=random.choice(['Scheduled', 'Completed', 'Cancelled']),
#         hospitalised=random.choice([True, False]),
#         created_by=create_fake_employee()
#     )
#     consultation.symptomes.set(Symptomes.objects.order_by('?')[:random.randint(1, 3)])
#     consultation.antecedentsMedicaux.set(AntecedentsMedicaux.objects.order_by('?')[:random.randint(1, 3)])
#     consultation.allergies.set(Allergies.objects.order_by('?')[:random.randint(1, 3)])
#     consultation.save()
#     return consultation
#
#
# def populate_services():
#     services = ['VIH-SIDA', 'TUBERCULOSE', 'COVID']
#     subactivities = ['Consultation', 'Hospitalisation', 'Suivi']
#
#     for service_name in services:
#         service = Service.objects.create(nom=service_name)
#         for subactivity_name in subactivities:
#             ServiceSubActivity.objects.create(service=service, nom=subactivity_name)
#
#
# def populate_data(n):
#     populate_services()
#     for _ in range(n):
#         patient = create_fake_patient()
#         constante = create_fake_constante(patient)
#         create_fake_consultation(patient, constante)
#
#
# def run():
#     populate_data(1000)  # Nombre de patients à créer

fake = Faker()


def create_fake_user():
    user = User.objects.create_user(
        username=fake.unique.user_name(),
        email=fake.email(),
        password='password123',
        first_name=fake.first_name(),
        last_name=fake.last_name()
    )
    return user


def create_fake_employee():
    user = create_fake_user()
    return Employee.objects.create(
        user=user,
        # Remplissez les champs nécessaires pour Employee
    )


def create_fake_patient():
    return Patient.objects.create(
        user=None,
        code_patient=fake.unique.bothify(text='???-#####'),
        nom=fake.last_name(),
        prenoms=fake.first_name(),
        contact=fake.phone_number(),
        situation_matrimoniale=random.choice(['Célibataire', 'Marié', 'Divorcé', 'Veuf']),
        lieu_naissance=fake.city(),
        date_naissance=fake.date_of_birth(minimum_age=18, maximum_age=90),
        genre=random.choice(['Masculin', 'Féminin']),
        nationalite=fake.country(),
        profession=fake.job(),
        nbr_enfants=random.randint(0, 5),
        groupe_sanguin=random.choice(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']),
        niveau_etude=fake.word(),
        employeur=fake.company(),
        created_by=create_fake_employee(),
        avatar=None,
        localite=None,
        status=random.choice(['Actif', 'Inactif'])
    )


def create_fake_constante(patient):
    return Constante.objects.create(
        patient=patient,
        tension_systolique=random.randint(90, 140),
        tension_diastolique=random.randint(60, 90),
        frequence_cardiaque=random.randint(60, 100),
        frequence_respiratoire=random.randint(12, 20),
        temperature=round(random.uniform(36.5, 37.5), 1),
        saturation_oxygene=random.randint(90, 100),
        glycemie=round(random.uniform(70, 140), 1),
        poids=round(random.uniform(50, 100), 1),
        taille=round(random.uniform(1.5, 2.0), 2),
        pouls=round(random.uniform(60, 100), 1),
        imc=round(random.uniform(18.5, 30.0), 1),
        created_by=create_fake_employee()
    )


def create_fake_consultation(patient, constante):
    consultation = Consultation.objects.create(
        activite=ServiceSubActivity.objects.order_by('?').first(),
        patient=patient,
        constante=constante,
        examens=None,
        services=Service.objects.order_by('?').first(),
        doctor=create_fake_employee(),
        consultation_date=fake.date_time_this_year(),
        reason=fake.text(),
        diagnosis=fake.text(),
        commentaires=fake.text(),
        suivi=Service.objects.order_by('?').first(),
        status=random.choice(['Scheduled', 'Completed', 'Cancelled']),
        hospitalised=random.choice([True, False]),
        created_by=create_fake_employee()
    )
    consultation.symptomes.set(Symptomes.objects.order_by('?')[:random.randint(1, 3)])
    consultation.antecedentsMedicaux.set(AntecedentsMedicaux.objects.order_by('?')[:random.randint(1, 3)])
    consultation.allergies.set(Allergies.objects.order_by('?')[:random.randint(1, 3)])
    consultation.save()
    return consultation


def create_fake_categorie_molecule():
    return CathegorieMolecule.objects.create(
        nom=fake.word(),
        description=fake.text()
    )


def create_fake_molecule(categorie):
    return Molecule.objects.create(
        nom=fake.word(),
        description=fake.text(),
        cathegorie=categorie
    )


def create_fake_medicament(categorie):
    return Medicament.objects.create(
        nom=fake.word(),
        description=fake.text(),
        stock=random.randint(10, 500),
        date_expiration=fake.date_between(start_date='today', end_date='+2y'),
        categorie=categorie,
        fournisseur=None  # Ajoutez un fournisseur factice si nécessaire
    )


def populate_services():
    services = ['VIH-SIDA', 'TUBERCULOSE', 'COVID']
    subactivities = ['Consultation', 'Hospitalisation', 'Suivi']

    for service_name in services:
        service = Service.objects.create(nom=service_name)
        for subactivity_name in subactivities:
            ServiceSubActivity.objects.create(service=service, nom=subactivity_name)


def populate_pharmacy_data():
    for _ in range(10):  # Nombre de catégories de molécules
        categorie = create_fake_categorie_molecule()
        for _ in range(10):  # Nombre de molécules par catégorie
            molecule = create_fake_molecule(categorie)
        for _ in range(10):  # Nombre de médicaments par catégorie
            create_fake_medicament(categorie)


def populate_data(n):
    populate_services()
    populate_pharmacy_data()
    for _ in range(n):
        patient = create_fake_patient()
        constante = create_fake_constante(patient)
        create_fake_consultation(patient, constante)


def run():
    populate_data(1000)  # Nombre de patients à créer