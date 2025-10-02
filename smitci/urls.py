"""
URL configuration for smitci project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import path, include

from core.views import RoleListView, RoleCreateView, RoleDeleteView, AssignRoleView, EmployeeListView, \
    EmployeeCreateView, EmployeeDeleteView, EmployeeUpdateView, send_sms_view, employee_profile, AdminPasswordResetView
from hospitalisation.views import HospitalizationUrgenceCreateView, SuivieSoinsListView, SuivieSoinsDetailView, \
    search_medications, add_prescription
from smit import views
from smit.views import HomePageView, PatientListView, PatientCreateView, RendezVousListView, RendezVousDetailView, \
    PatientDetailView, SalleAttenteListView, ServiceContentDetailView, consultation_send_create, \
    ConsultationSidaDetailView, ConsultationSidaListView, create_symptome_and_update_consultation, Antecedents_create, \
    Allergies_create, Examens_create, Conseils_add, Rendezvous_create, Protocoles_create, symptome_delete, \
    ActiviteListView, Constantes_create, hospitalisation_send_create, patient_list_view, \
    mark_consultation_as_hospitalised, test_rapide_vih_create, enquete_create, create_consultation_pdf, \
    ConsultationListView, ConsultationDetailView, ConsultationUpdateView, ConsultationDeleteView, \
    delete_test_rapide_vih, delete_examen, ConstanteUpdateView, consultation_delete, PatientUpdateView, \
    RendezVousConsultationUpdateView, PatientRecuListView, suivi_send_create, SuiviListView, SuiviDetailView, \
    create_rdv, UrgenceListView, UrgenceCreateView, test_rapide_consultation_generale_create, \
    delete_test_rapide_consultation_generale, Examens_Consultation_generale_create, AppointmentDeleteView, \
    hospitalization_chart_data, BilanListView, BilanCreateView, BilanDetailView, BilanUpdateView, BilanDeleteView, \
    CompleteBilanView, create_bilan_initial, suivi_send_from_bilan, add_traitement_arv, add_suivi_protocole, add_bilan, \
    add_rdv, Landing, UrgencePatientCreateAPI, HospitalizationCreateAPI


def healthz(_):
    # ⚡ rapide : sans requête DB
    return JsonResponse({"status": "ok"})


urlpatterns = [
                  path("healthz", healthz),
                  path('admin/', admin.site.urls),
                  path('accounts/', include('allauth.urls')),
                  path('accounts/signup/', lambda request: redirect('/')),
                  path('schedule/', include('schedule.urls')),
                  path("unicorn/", include("django_unicorn.urls")),
                  path('patients/', patient_list_view, name='patient-list'),
                  path('pharmacy/', include('pharmacy.urls')),
                  path('hospitalisation/', include('hospitalisation.urls')),
                  path('laboratoire/', include('laboratory.urls')),
                  path('api/', include('core.api.urls')),
                  path('tinymce/', include('tinymce.urls')),
                  path("select2/", include("django_select2.urls")),
                  path('api/hospitalization_chart_data/', hospitalization_chart_data,
                       name='hospitalization_chart_data'),
                  path('', include('django_prometheus.urls')),

                  path('api/medicaments/', search_medications, name='search_medications'),
                  path('api/prescription/add/', add_prescription, name='add_prescription'),

                  path('user_role/', RoleListView.as_view(), name='user_role'),
                  path("roles/create/", RoleCreateView.as_view(), name="role_create"),
                  path("roles/delete/<int:pk>", RoleDeleteView.as_view(), name="role_delete"),

                  path("profile/", employee_profile, name="employee_profile"),

                  path("employees/", EmployeeListView.as_view(), name="employee_list"),
                  path("employees/create/", EmployeeCreateView.as_view(), name="employee_create"),
                  path("employees/<int:pk>/update/", EmployeeUpdateView.as_view(), name="employee_update"),
                  path("employees/<int:pk>/delete/", EmployeeDeleteView.as_view(), name="employee_delete"),
                  path('employee/role/assignment', AssignRoleView.as_view(), name='employee_role_assign'),

                  path('employees/<int:pk>/reset-password/', AdminPasswordResetView.as_view(),
                       name='admin_password_reset'),

                  path('', HomePageView.as_view(), name='home'),
                  path('landing', Landing.as_view(), name='landingview'),
                  path('listePatient/', PatientListView.as_view(), name='global_search'),
                  path('modifierPatient/<int:pk>', PatientUpdateView.as_view(), name='update_patient'),
                  path('detailPatient/<int:pk>', PatientDetailView.as_view(), name='detail_patient'),

                  # path('patient/<int:patient_id>/service/<int:service_id>/', service_detail_view, name='service_detail'),

                  path('Patientadd/', PatientCreateView.as_view(), name='add_patient'),

                  path('salle_attente/', SalleAttenteListView.as_view(), name='attente'),

                  path('rendez-vous/', RendezVousListView.as_view(), name='appointment_list'),
                  path('patient_recu/', PatientRecuListView.as_view(), name='appointment_over'),
                  path('rendez-vous/detail/<int:pk>', RendezVousDetailView.as_view(), name='appointment_detail'),
                  path('rendez-vous/update/<int:pk>', RendezVousConsultationUpdateView.as_view(),
                       name='appointment_update'),
                  path('appointments/<int:pk>/delete/', views.appointment_delete, name='appointment_delete'),

                  # Consultation VIH
                  path('test_rapide/<int:consultation_id>', test_rapide_consultation_generale_create,
                       name='test_depistage_generale_create'),
                  path('consultation_delete/<int:consultation_id>', consultation_delete, name='delete_consult'),
                  path('test-rapide-vih/<int:test_id>/delete/<int:consultation_id>',
                       delete_test_rapide_consultation_generale, name='delete_test_rapide_generale'),

                  #Consultation generale
                  path('test_rapide/<int:consultation_id>', test_rapide_vih_create, name='test_depistage-Rapide'),
                  path('consultation_delete/<int:consultation_id>', consultation_delete, name='delete_consult'),
                  path('test-rapide-vih/<int:test_id>/delete/<int:consultation_id>', delete_test_rapide_vih,
                       name='delete_test_rapide_vih'),

                  #Hospitalisation
                  path('hospitalisation/<int:consultation_id>/<int:patient_id>', mark_consultation_as_hospitalised,
                       name='mark_hospitalisation'),

                  path('hospitalized/<int:consultations_id>/<int:patient_id>', hospitalisation_send_create,
                       name='send_hospitalisation'),

                  path('consultation/<int:patient_id>/<int:rdv_id>', consultation_send_create,
                       name='send_consultation'),

                  path('suivi/<int:patient_id>/<int:consultationsvih_id>', suivi_send_create, name='send_to_suivie'),

                  path('suivi/<int:patient_id>/<int:consultation_id>', suivi_send_from_bilan,
                       name='suivi_send_from_bilan'),

                  path('consultationdetail/<int:pk>', ConsultationSidaDetailView.as_view(), name='detail_consultation'),
                  path('consultation/vih', ConsultationSidaListView.as_view(), name='consultation_vih_list'),

                  path('consultations/', ConsultationListView.as_view(), name='consultation_list'),

                  path('Suivi/', SuiviListView.as_view(), name='suivi_list'),
                  path('Suivi/detail<int:pk>', SuiviDetailView.as_view(), name='suivis-detail'),

                  path('Suivi/rdv/create<int:suivi_id>', create_rdv, name='suivis-rdv-create'),

                  path('consultations/<int:pk>/', ConsultationDetailView.as_view(), name='consultation_detail'),

                  path('consultations/<int:pk>/modifier/', ConsultationUpdateView.as_view(),
                       name='consultation_update'),
                  path('consultations/<int:pk>/supprimer/', ConsultationDeleteView.as_view(),
                       name='consultation_delete'),

                  path('service/<str:serv>/<str:acty>/<int:acty_id>', ActiviteListView.as_view(),
                       name='service_activity_list'),

                  path('symptomes/create/<int:consultation_id>', create_symptome_and_update_consultation,
                       name='create_symptomes'),
                  path('Antecedents_create/create/<int:consultation_id>', Antecedents_create,
                       name='Antecedents_create'),

                  path('enquete_create/<int:consultation_id>', enquete_create, name='enquete_create'),
                  path('Allergies_create/create/<int:consultation_id>', Allergies_create, name='Allergies_create'),

                  path('Examens_create/create/<int:consultation_id>', Examens_create, name='Examens_create'),
                  path('delete_examen/<int:examen_id>/create/<int:consultation_id>', delete_examen,
                       name='Examens_delete'),

                  path('Examens_generale_create/create/<int:consultation_id>', Examens_Consultation_generale_create,
                       name='Examens_generale_create'),

                  path('Conseils_add/create/<int:consultation_id>', Conseils_add, name='Conseils_add'),
                  path('Rendezvous_create/create/<int:consultation_id>', Rendezvous_create, name='Rendezvous_create'),
                  path('rendez-vous/<int:pk>/delete/', AppointmentDeleteView.as_view(), name='appointment_delete'),

                  path('Protocoles_create/create/<int:consultation_id>', Protocoles_create, name='Protocoles_create'),

                  path('symptome_delete/<int:consultation_id>/<int:symp>', symptome_delete, name='symptome_delete'),

                  path('constantes/<int:patient_id>', Constantes_create, name='ajouter_constantes'),

                  path('consultation_print/<int:patient_id> <int:consultation_id>', create_consultation_pdf,
                       name='telecharger_bilaninitial'),
                  # path('constantes/<int:patient_id>', ConstanteCreateView.as_view(), name='ajouter_constantes'),

                  path('appointments/new/', views.appointment_create, name='appointment_create'),

                  # path('appointments/new/', views.appointment_create, name='appointment_create'),

                  # path('appointments/<int:pk>/edit/', views.appointment_update, name='appointment_update'),

                  # path('service/<int:pk>/contents/', ServiceContentDetailView.as_view(), name='service_content_detail'),
                  path('service/<str:serv>/<str:acty>/<int:pk>/', ServiceContentDetailView.as_view(),
                       name='service_content_detail'
                       ),
                  path('constantes/<int:pk>/update', ConstanteUpdateView.as_view(), name='constantesupdate'),

                  path('api/get-patient-name/<int:appointment_id>/', views.get_patient_name, name='get_patient_name'),
                  path('api/get-patient-all-name/<int:patient_id>/', views.get_patient_all_name,
                       name='get_patient_all_name'),
                  path('urgence/liste', UrgenceListView.as_view(), name='urgences_list'),
                  path('urgence/create/', UrgenceCreateView.as_view(), name='urgence_create'),
                  path('api/urgences/patient/', UrgencePatientCreateAPI.as_view(), name='urgence_patient_api'),
                  path('api/urgences/<int:patient_id>/hospitalisation/', HospitalizationCreateAPI.as_view(),
                       name='urgence_hosp_api'),

                  path('hospitalization/create/', HospitalizationUrgenceCreateView.as_view(),
                       name='hospitalization_urgence_create'),
                  path('send_employee_sms/<int:employee_id>', send_sms_view, name='send_sms_view'),
                  path('suivie_soins', SuivieSoinsListView.as_view(), name='suivie_soins_list'),
                  path('suivie_soins/detail<int:pk>', SuivieSoinsDetailView.as_view(), name='suivie_soins_detail'),

                  path('bilan_initial', BilanListView.as_view(), name='bilan_list'),
                  path('create/', BilanCreateView.as_view(), name='bilan_create'),
                  path('<int:pk>/', BilanDetailView.as_view(), name='bilan_detail'),
                  path('<int:pk>/update/', BilanUpdateView.as_view(), name='bilan_update'),
                  path('<int:pk>/delete/', BilanDeleteView.as_view(), name='bilan_delete'),
                  path('<int:pk>/complete/', CompleteBilanView.as_view(), name='bilan_complete'),
                  path('create-bilan-initial/<int:consultation_id>/<int:patient_id>/', create_bilan_initial,
                       name='create_bilan_initial'),

                  path('suivi/<int:suivi_id>/add-traitement/', add_traitement_arv, name='add_traitement'),
                  path('suivi/<int:suivi_id>/add-protocole/', add_suivi_protocole, name='add_protocole'),
                  path('suivi/<int:suivi_id>/add-bilan/', add_bilan, name='add_bilan'),
                  path('suivi/<int:suivi_id>/add-rdv/', add_rdv, name='add_rdv'),

              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
