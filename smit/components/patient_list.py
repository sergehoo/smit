from django_unicorn.components import UnicornView

from smit.models import Patient


class PatientListView(UnicornView):
    search_query: str = ""
    patients = []

    def mount(self):
        self.patients = self.get_patients()

    def updated_search_query(self, value):
        self.patients = self.get_patients()

    def get_patients(self):
        if self.search_query:
            return Patient.objects.filter(nom__icontains=self.search_query)
        return Patient.objects.all()
