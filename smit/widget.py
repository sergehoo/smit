from django_select2.forms import ModelSelect2Widget
from .models import Medicament
import re


class MedicationWidget(ModelSelect2Widget):
    """ Widget Django-Select2 pour la sélection dynamique des médicaments """

    model = Medicament
    search_fields = ["nom__icontains"]  # ✅ Permet la recherche dynamique

    def create_object(self, text):
        """ Crée un médicament s'il n'existe pas """
        pattern = r"(?P<nom>.+?)\s+(?P<dosage>\d+)\s*(?P<unitdosage>mg|ml|g|mcg)?\s*(?P<dosage_form>comprime|gellule|suspension|sirop|injectable)?"
        match = re.search(pattern, text.strip(), re.IGNORECASE)

        if match:
            nom = match.group('nom').strip()
            dosage = int(match.group('dosage')) if match.group('dosage') else None
            unitdosage = match.group('unitdosage') if match.group('unitdosage') else None
            dosage_form = match.group('dosage_form') if match.group('dosage_form') else None
        else:
            nom = text.strip()
            dosage = None
            unitdosage = None
            dosage_form = None

        medicament, created = Medicament.objects.get_or_create(
            nom=nom,
            defaults={'dosage': dosage, 'unitdosage': unitdosage, 'dosage_form': dosage_form}
        )
        return medicament