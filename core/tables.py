import django_tables2 as tables

from smit.models import BilanParaclinique


class BilanParacliniqueTable(tables.Table):
    id = tables.Column(verbose_name="Code")
    patient = tables.Column(verbose_name="Patient")
    created_at = tables.DateColumn(verbose_name="Date", format="d M Y")
    doctor = tables.Column(verbose_name="Médecin")
    examen = tables.Column(verbose_name="Examen")
    status = tables.Column(verbose_name="Statut")
    actions = tables.TemplateColumn(
        template_name='partials/exam_actions.html',
        verbose_name='Actions',
        orderable=False
    )

    class Meta:
        model = BilanParaclinique
        template_name = "lab/custom_table.html"
        fields = ("id", "patient", "created_at", "doctor", "examen", "status")
        attrs = {"class": "table table-striped table-bordered"}
