from django.conf.urls.static import static
from django.urls import path

from hospitalisation.views import HospitalisationListView, HospitalisationUniteListView, HospitalisationDetailView, \
    export_constante_pdf, export_prescription_pdf, export_signe_fonctionnel_pdf, export_indicateur_biologique_pdf, \
    export_indicateur_fonctionnel_pdf, export_indicateur_subjectif_pdf, update_hospitalisation_discharge, reserve_bed, \
    release_bed, mark_as_out_of_service, mark_as_cleaning, delete_bed, set_cleaning_false, hospitalisation_lit_reserved, \
    LitDetailView, mark_execution_taken, delete_prescription, add_diagnostic, add_avis_medical, add_effet_indesirable, \
    add_historique_maladie, add_observations, add_hospi_comment, ExportHospitalizationView, add_maladie, \
    add_hospi_suivie_comment, add_observations_suivi, generate_ordonnance_pdf, add_antecedents_hospi, \
    ajouter_mode_de_vie, add_examen_apareil, HospitalisedPatientListView, add_problemes_pose, add_resume_syndromique, \
    add_bilan_paraclinique, add_imagerie, update_execution_status, export_hospitalized_patients, \
    HospitalisationDeleteView
from smit.views import add_cas_contact
from smitci import settings

urlpatterns = [
                  path('generale/hospitalisation', HospitalisationListView.as_view(), name='hospitalisation'),
                  path('generale/hospitalised', HospitalisedPatientListView.as_view(), name='hospitalised_patient'),
                  path('hospitalisation/export/', ExportHospitalizationView.as_view(), name='export_hospitalizations'),

                  path('details/<int:pk>/hospi/', HospitalisationDetailView.as_view(), name='hospitalisationdetails'),
                  path('delete/<int:pk>/hospi/', HospitalisationDeleteView.as_view(), name='hospitalisationdelete'),

                  path('lit/detail<int:pk>/hospi/', LitDetailView.as_view(), name='litdetails'),
                  path('unites', HospitalisationUniteListView.as_view(), name='hospi_unites'),
                  path('set_cleaning_false/<int:lit_id>/', set_cleaning_false, name='set_cleaning_false'),

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

                  path('hospitalisation_reserved/<int:lit_id>', hospitalisation_lit_reserved,
                       name='hospitalisation_lit_reserved'),

                  path('lit/<int:bed_id>/reserve/', reserve_bed, name='reserve_bed'),
                  path('lit/<int:bed_id>/release/', release_bed, name='release_bed'),
                  path('lit/<int:bed_id>/out_of_service/', mark_as_out_of_service, name='mark_as_out_of_service'),
                  path('lit/<int:bed_id>/cleaning/', mark_as_cleaning, name='mark_as_cleaning'),
                  path('lit/<int:bed_id>/delete/', delete_bed, name='delete_bed'),
                  path('prescription/mark_taken/', mark_execution_taken, name='mark_execution_taken'),
                  path('prescription/delete/<int:prescription_id>/', delete_prescription, name='delete_prescription'),

                  path('add-diagnostic/<int:hospitalisation_id>', add_diagnostic, name='add_diagnostic'),

                  path('add-antecedents/<int:hospitalisation_id>', add_antecedents_hospi, name='add_antecedent_hospi'),

                  path('add_mode_de_vie/<int:hospitalisation_id>/', ajouter_mode_de_vie, name='ajouter_mode_de_vie'),

                  path('add_examen_apareil/<int:hospitalisation_id>/', add_examen_apareil, name='add_examen_apareil'),

                  path('add-observations/<int:hospitalisation_id>', add_observations, name='add_observations'),
                  path('add-observations-suivi/<int:hospitalisation_id>', add_observations_suivi,
                       name='add_observations_suivi'),
                  path('add-hospi-comment/<int:hospitalisation_id>', add_hospi_comment, name='add_coment'),
                  path('add-hospi-suivi-comment/<int:hospitalisation_id>', add_hospi_suivie_comment,
                       name='add_coment_suivi'),

                  path('add-avis-medical/<int:hospitalisation_id>', add_avis_medical, name='add_avis_medical'),
                  path('add-effet-indesirable/<int:hospitalisation_id>', add_effet_indesirable,
                       name='add_effet_indesirable'),
                  path('add-historique-maladie/<int:hospitalisation_id>', add_historique_maladie,
                       name='add_historique_maladie'),
                  path('add-maladie/', add_maladie, name='add_maladie'),
                  path('add-add_problemes_pose/<int:hospitalisation_id>', add_problemes_pose, name='add_problemes_pose'),
                  path('add_resume_syndromique/<int:hospitalisation_id>', add_resume_syndromique, name='add_resume_syndromique'),

                  path("hospitalisation/<int:hospitalisation_id>/add_bilan/", add_bilan_paraclinique,  name="add_bilan_paraclinique"),
                  path("add_imagerie/<int:hospitalisation_id>", add_imagerie,  name="add_imagerie"),

                  path('patient/<int:patient_id>/add-cas-contact/', add_cas_contact, name='add_cas_contact'),
                  path('ordonnance/<int:patient_id>/<int:hospitalisation_id>', generate_ordonnance_pdf,
                       name='generate_ordonnance_pdf'),

                  path("update-execution-status/", update_execution_status, name="update_execution_status"),

                  path('export/hospitalized/<str:age_group>/', export_hospitalized_patients,
                       name='export_hospitalized_patients'),

                  # path('hospitalisation/<int:hospitalisation_id>prescription/<int:prescription_id>/execute/', execute_prescription, name='nurse_execute'),

              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
