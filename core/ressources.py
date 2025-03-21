from import_export.resources import ModelResource

from smit.models import BilanParaclinique


class BilanParacliniqueResource(ModelResource):
    class Meta:
        model = BilanParaclinique
        fields = (
            'id',
            'patient__nom',
            'patient__prenoms',
            'doctor',
            'examen__nom',
            'examen__type_examen__nom',
            'result',
            'result_date',
            'created_at',
        )
        export_order = fields