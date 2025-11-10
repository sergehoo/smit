from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.urls import path

from laboratory.views import AnalyseListView, AnalyseDetailView, AnalyseCreateView, AnalyseDeleteView, \
    AnalyseUpdateView, ExamenListView, ExamenDetailView, ExamenCreateView, ExamenUpdateView, ExamenDeleteView, \
    ExamenResultatsListView, create_echantillon, delete_echantillon, EchantillonListView, \
    create_echantillon_consultation_generale, delete_echantillon_consultation_generale, ExamenDoneListView, \
    update_examen_result, export_examens_done, examens_by_type_paginated, EchantillonCreateView, request_serologie_vih, \
    validate_serologie_vih_request, EchantillonDetailView, update_echantillon_result, ResultatAnalyseListView, \
    ResultatAnalyseCreateView, ResultatAnalyseDetailView, ResultatAnalyseUpdateView, ResultatAnalyseDeleteView, \
    ResultatAnalyseValidateView, ResultatAnalyseCorrigerView, validate_resultat_ajax, ExamenDoneDetailView, \
    update_examen_results_bulk, ExamenTypePartialView
from smitci import settings

urlpatterns = [
                  # URLS pour Analyse
                  path('analyses/', AnalyseListView.as_view(), name='analyse_list'),
                  path('analyses/<int:pk>/', AnalyseDetailView.as_view(), name='analyse_detail'),

                  path('analyses/create/', AnalyseCreateView.as_view(), name='analyse_create'),

                  path('analyses/<int:pk>/update/', AnalyseUpdateView.as_view(), name='analyse_update'),
                  path('analyses/<int:pk>/delete/', AnalyseDeleteView.as_view(), name='analyse_delete'),

                  # URLS pour echantillon

                  path('validate_serologie_vih_request/<int:preleve_id>/', validate_serologie_vih_request,
                       name='validate_serologie_vih_request'),
                  path('prelevements/', EchantillonListView.as_view(), name='echantillons_list'),
                  path('echantillons/<int:pk>/', EchantillonDetailView.as_view(), name='echantillon_detail'),
                  path('echantillon/<int:pk>/update-result/', update_echantillon_result,
                       name='update_echantillon_result'),

                  path('echantillons/nouveau/', EchantillonCreateView.as_view(), name='echantillon_create'),

                  path('request_serologie_vih', request_serologie_vih, name='request_serologie_vih'),

                  path('update_examen/<int:examen_id>/', update_examen_result, name='update_examen_result'),

                  # URLS pour echantillon
                  # path('examens/', EchantillonListView.as_view(), name='echantillons_list'),

                  # URLS pour Examen
                  path('examens/', ExamenResultatsListView.as_view(), name='resultatsexam'),
                  path('examens/resultats', ExamenListView.as_view(), name='examen_list'),

                  path("examens/bulk-update/", update_examen_results_bulk, name="update_examen_results_bulk"),

                  path(
                      "laboratoire/examens/resultats/type/<slug:type_slug>/",
                      ExamenTypePartialView.as_view(),
                      name="examen_type_partial",
                  ),

                  path('examens_effectues/', ExamenDoneListView.as_view(), name='examen_done_list'),
                  path('examens_effectues/<int:pk>', ExamenDoneDetailView.as_view(), name='examen_done_detail'),

                  path('examens-done/export/<str:format>/', export_examens_done, name='export_examens_done'),

                  path("examens-done/type/<str:type_slug>/", examens_by_type_paginated,
                       name="examens_by_type_paginated"),

                  path('examens/<int:pk>/', ExamenDetailView.as_view(), name='examen_detail'),
                  path('examens/create/', ExamenCreateView.as_view(), name='examen_create'),
                  path('examens/<int:pk>/update/', ExamenUpdateView.as_view(), name='examen_update'),
                  path('examens/<int:pk>/delete/', ExamenDeleteView.as_view(), name='examen_delete'),

                  path('examen/<int:consultation_id>/echantillon/create/', create_echantillon,
                       name='create_echantillon'),
                  path('examen/<int:consultation_id>/echantillon/<int:echantillon_id>/delete/', delete_echantillon,
                       name='delete_echantillon'),

                  path('examen/<int:consultation_id>/echantillon/create/', create_echantillon_consultation_generale,
                       name='create_echantillon_consultation_generale'),
                  path('examen/<int:consultation_id>/echantillon/<int:echantillon_id>/delete/',
                       delete_echantillon_consultation_generale,
                       name='delete_echantillon_consultation_generale'),
                  path(
                      'resultatanalyse_list',
                      login_required(ResultatAnalyseListView.as_view()),
                      name='resultatanalyse_list'
                  ),

                  # Création
                  path('nouveau/resultatanalyse_create', login_required(ResultatAnalyseCreateView.as_view()),
                       name='resultatanalyse_create'
                       ),
                  path(
                      'echantillon/<int:echantillon_id>/nouveau/', login_required(ResultatAnalyseCreateView.as_view()),
                      name='resultatanalyse_create_for_echantillon'
                  ),

                  # Détail
                  path(
                      'resultatanalyse_detail/<int:pk>/',
                      login_required(ResultatAnalyseDetailView.as_view()),
                      name='resultatanalyse_detail'
                  ),

                  # Modification
                  path(
                      'resultatanalyse_update/<int:pk>/modifier/',
                      login_required(ResultatAnalyseUpdateView.as_view()),
                      name='resultatanalyse_update'
                  ),

                  # Suppression
                  path(
                      '<int:pk>/supprimer/',
                      login_required(ResultatAnalyseDeleteView.as_view()),
                      name='resultatanalyse_delete'
                  ),

                  # Validation
                  path(
                      'resultatanalyse_validate/<int:pk>/valider/',
                      login_required(ResultatAnalyseValidateView.as_view()),
                      name='resultatanalyse_validate'
                  ),

                  # Correction
                  path(
                      'resultatanalyse_correct/<int:pk>/corriger/',
                      login_required(ResultatAnalyseCorrigerView.as_view()),
                      name='resultatanalyse_correct'
                  ),

                  # Validation AJAX
                  path(
                      'resultatanalyse_validate_ajax/api/<int:pk>/valider/',
                      login_required(validate_resultat_ajax),
                      name='resultatanalyse_validate_ajax'
                  ),


              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
