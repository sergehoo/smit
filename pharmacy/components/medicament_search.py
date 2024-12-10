from django_unicorn.components import UnicornView

from pharmacy.models import Medicament, Molecule, CathegorieMolecule


class MedicamentSearchView(UnicornView):
    search = ""
    selected_categorie = ""
    selected_molecule = ""
    categories = []
    molecules = []
    medicaments = []

    def mount(self):
        """Initialise les données au montage de la vue."""
        self.categories = CathegorieMolecule.objects.all()
        self.molecules = Molecule.objects.none()
        self.medicaments = Medicament.objects.select_related('categorie', 'fournisseur').prefetch_related('molecules')

    def updated(self, name, value):
        """Met à jour les filtres et recherche les médicaments lorsque les champs changent."""
        if name == "selected_categorie":
            self.molecules = self.get_molecules()
            self.selected_molecule = ""  # Réinitialise la molécule si la catégorie change

        self.search_medicaments()

    def get_molecules(self):
        """Retourne les molécules liées à une catégorie."""
        if self.selected_categorie:
            return Molecule.objects.filter(cathegorie_id=self.selected_categorie)
        return Molecule.objects.all()

    def search_medicaments(self):
        """Filtre les médicaments selon les critères définis."""
        query = Medicament.objects.select_related('categorie', 'fournisseur').prefetch_related('molecules')

        if self.search:
            query = query.filter(nom__icontains=self.search)

        if self.selected_categorie:
            query = query.filter(categorie_id=self.selected_categorie)

        if self.selected_molecule:
            query = query.filter(molecules__id=self.selected_molecule)

        self.medicaments = query.distinct()
