from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views import View

from pharmacy.models import Medicament


def search_medicaments(request):
    search = request.GET.get('search', '')
    categorie = request.GET.get('categorie', '')
    molecule = request.GET.get('molecule', '')
    page = int(request.GET.get('page', 1))

    medicaments = Medicament.objects.select_related('categorie', 'fournisseur').prefetch_related('molecules')

    if search:
        medicaments = medicaments.filter(nom__icontains=search)

    if categorie:
        medicaments = medicaments.filter(categorie_id=categorie)

    if molecule:
        medicaments = medicaments.filter(molecules__id=molecule)

    paginator = Paginator(medicaments.distinct(), 20)  # 20 médicaments par page
    paginated_medicaments = paginator.get_page(page)

    results = [
        {"id": med.id, "nom": med.nom, "description": med.description}
        for med in paginated_medicaments
    ]
    return JsonResponse({
        "medicaments": results,
        "has_next": paginated_medicaments.has_next(),
        "page": page,
    })


class MedicamentFilterView(View):
    def get(self, request):
        search = request.GET.get('search', '').strip()
        categorie_id = request.GET.get('categorie', '')
        molecule_id = request.GET.get('molecule', '')

        # Base query
        medicaments = Medicament.objects.select_related('categorie', 'fournisseur').prefetch_related('molecules')

        # Apply filters
        if search:
            medicaments = medicaments.filter(nom__icontains=search)

        if categorie_id:
            medicaments = medicaments.filter(categorie_id=categorie_id)

        if molecule_id:
            medicaments = medicaments.filter(molecules__id=molecule_id)

        medicament_list = [
            {
                'id': med.id,
                'nom': med.nom,
                'description': med.description,
                'stock': med.stock,
                'categorie': med.categorie.nom if med.categorie else None,
                'molecules': [m.nom for m in med.molecules.all()],
            }
            for med in medicaments
        ]

        return JsonResponse({'medicaments': medicament_list})