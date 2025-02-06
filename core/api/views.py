from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views import View

from pharmacy.models import Medicament, CathegorieMolecule, Molecule, MouvementStock


def fetch_medicaments(request):
    query = request.GET.get('search', '').strip()
    categorie_id = request.GET.get('categorie', '')
    molecule_id = request.GET.get('molecule', '')
    page_number = request.GET.get('page', 1)  # Numéro de la page
    items_per_page = 12  # Nombre d'éléments par page

    # Filtrage des médicaments
    medicaments = Medicament.objects.all()

    if query:
        medicaments = medicaments.filter(nom__icontains=query)

    if categorie_id:
        medicaments = medicaments.filter(categorie_id=categorie_id)

    if molecule_id:
        medicaments = medicaments.filter(molecules__id=molecule_id)

    # Pagination
    paginator = Paginator(medicaments, items_per_page)
    page_obj = paginator.get_page(page_number)

    # Construire les résultats
    data = {
        "medicaments": [
            {
                "id": med.id,
                "nom": med.nom,
                "description": med.description or "Aucune description disponible",
                "categorie": med.categorie.nom if med.categorie else "Non spécifiée",
                "molecules": [molecule.nom for molecule in med.molecules.all()],
                "stock": med.stock if med.stock is not None else "Non spécifié",
                "miniature": med.miniature.url if med.miniature else None,  # Inclure la miniature
                "expiration": med.date_expiration.strftime("%d/%m/%Y") if med.date_expiration else "Non spécifiée",
                "dosage": med.dosage if med.dosage else "Non spécifié",
                "dosage_form": med.dosage_form if med.dosage_form else "Non spécifié",
                "unite_dosage": med.unitdosage or "Non spécifiée",  # Inclure l'unité de dosage
            }
            for med in page_obj
        ],
        "total_count": paginator.count,  # Nombre total d'éléments
        "num_pages": paginator.num_pages,  # Nombre total de pages
        "current_page": page_obj.number,  # Page actuelle
    }
    return JsonResponse(data)


def categories_api(request):
    categories = CathegorieMolecule.objects.all()
    data = [
        {
            "id": category.id,
            "nom": category.nom,
            "description": category.description or "Aucune description disponible",
        }
        for category in categories
    ]
    return JsonResponse(data, safe=False)


def molecules_api(request):
    molecules = Molecule.objects.all()
    data = [
        {
            "id": molecule.id,
            "nom": molecule.nom,
            "description": molecule.description or "Aucune description disponible",
            "cathegorie": molecule.cathegorie.nom if molecule.cathegorie else "Non spécifiée",
        }
        for molecule in molecules
    ]
    return JsonResponse(data, safe=False)


def api_mouvement_stock_list(request):
    search_query = request.GET.get('search[value]', '')  # Recherche
    start = int(request.GET.get('start', 0))  # Index de départ
    length = int(request.GET.get('length', 10))  # Nombre d'enregistrements par page

    # Filtrer les données en fonction de la recherche
    mouvements = MouvementStock.objects.all()
    if search_query:
        mouvements = mouvements.filter(
            medicament__nom__icontains=search_query
        )

    # Paginer les résultats
    total_count = mouvements.count()
    mouvements = mouvements[start:start+length]

    # Construire les données pour DataTables
    data = [
        {
            "id": mouvement.id,
            "medicament": mouvement.medicament.nom,
            "patient": mouvement.patient.nom if mouvement.patient else "Non spécifié",
            "quantite": mouvement.quantite,
            "type_mouvement": mouvement.type_mouvement,
            "date_mouvement": mouvement.date_mouvement.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for mouvement in mouvements
    ]

    return JsonResponse({
        "draw": int(request.GET.get('draw', 1)),  # Compteur pour les requêtes AJAX
        "recordsTotal": total_count,  # Nombre total d'enregistrements non filtrés
        "recordsFiltered": total_count,  # Nombre total d'enregistrements après filtrage
        "data": data,  # Données à afficher
    })