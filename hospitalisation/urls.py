

from django.conf.urls.static import static
from django.urls import path

from hospitalisation.views import HospitalisationListView, HospitalisationUniteListView, HospitalisationDetailView, \
    export_constante_pdf, export_prescription_pdf, export_signe_fonctionnel_pdf, export_indicateur_biologique_pdf, \
    export_indicateur_fonctionnel_pdf, export_indicateur_subjectif_pdf, update_hospitalisation_discharge
from smitci import settings

urlpatterns = [
                  path('generale', HospitalisationListView.as_view(), name='hospitalisation'),
                  path('details/<int:pk>/hospi/', HospitalisationDetailView.as_view(), name='hospitalisationdetails'),
                  path('unites', HospitalisationUniteListView.as_view(), name='hospi_unites'),

                  path('hospitalisation/<int:hospitalisation_id>/export/constantes/', export_constante_pdf,
                       name='export_constante_pdf'),
                  path('hospitalisation/<int:hospitalisation_id>/export/prescriptions/', export_prescription_pdf,
                       name='export_prescription_pdf'),
                  path('hospitalisation/<int:hospitalisation_id>/export/signes-fonctionnels/',
                       export_signe_fonctionnel_pdf, name='export_signe_fonctionnel_pdf'),
                  path('hospitalisation/<int:hospitalisation_id>/export/indicateurs-biologiques/',
                       export_indicateur_biologique_pdf, name='export_indicateur_biologique_pdf'),
                  path('hospitalisation/<int:hospitalisation_id>/export/indicateurs-fonctionnels/',
                       export_indicateur_fonctionnel_pdf, name='export_indicateur_fonctionnel_pdf'),
                  path('hospitalisation/<int:hospitalisation_id>/export/indicateurs-subjectifs/',
                       export_indicateur_subjectif_pdf, name='export_indicateur_subjectif_pdf'),
                  path('hospitalisation/<int:hospitalisation_id>/discharge/', update_hospitalisation_discharge,
                       name='update_hospitalisation_discharge'),

              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)