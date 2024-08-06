from django_unicorn.components import UnicornView

from pharmacy.models import Medicament, Molecule, CathegorieMolecule


class MedicamentSearchView(UnicornView):
    search = ""
    selected_categorie = ""
    selected_molecule = ""

    categories = CathegorieMolecule.objects.all()
    molecules = []
    medicaments = Medicament.objects.none()

    def mount(self):
        self.medicaments = Medicament.objects.all()
        self.molecules = self.get_molecules()

    def get_molecules(self):
        if self.selected_categorie:
            return Molecule.objects.filter(cathegorie_id=self.selected_categorie)
        return Molecule.objects.all()

    def updated(self, name, value):
        if name == "selected_categorie":
            self.molecules = self.get_molecules()
        self.search_medicaments()

    def search_medicaments(self):
        self.medicaments = Medicament.objects.all()

        if self.search:
            self.medicaments = self.medicaments.filter(nom__icontains=self.search)

        if self.selected_categorie:
            self.medicaments = self.medicaments.filter(categorie_id=self.selected_categorie)

        if self.selected_molecule:
            self.medicaments = self.medicaments.filter(molecule__id=self.selected_molecule)
