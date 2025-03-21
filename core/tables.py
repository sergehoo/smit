import django_tables2 as tables

from smit.models import BilanParaclinique


class BilanParacliniqueTable(tables.Table):
    actions = tables.TemplateColumn(
        template_name="partials/exam_actions.html", orderable=False, verbose_name="Actions"
    )
    id = tables.Column(verbose_name="Code", orderable=True)
    patient = tables.Column(verbose_name="Patient", orderable=True)
    created_at = tables.DateTimeColumn(verbose_name="Date", format="d M Y", orderable=True)
    doctor = tables.Column(verbose_name="Médecin", orderable=True)
    examen = tables.Column(verbose_name="Examen", orderable=True)
    status = tables.Column(verbose_name="Résultat", orderable=True)

    class Meta:
        model = BilanParaclinique
        template_name = "django_tables2/bootstrap4.html"
        fields = ("id", "patient", "created_at", "doctor", "examen", "status")
        attrs = {"class": "table table-striped table-bordered"}

