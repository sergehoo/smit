from django.conf.urls.static import static
from django.urls import path

from laboratory.views import AnalyseListView, AnalyseDetailView, AnalyseCreateView, AnalyseDeleteView, \
    AnalyseUpdateView, ExamenListView, ExamenDetailView, ExamenCreateView, ExamenUpdateView, ExamenDeleteView, \
    ExamenResultatsListView, create_echantillon, delete_echantillon, EchantillonListView
from smitci import settings

urlpatterns = [
                  # URLS pour Analyse
                  path('analyses/', AnalyseListView.as_view(), name='analyse_list'),
                  path('analyses/<int:pk>/', AnalyseDetailView.as_view(), name='analyse_detail'),
                  path('analyses/create/', AnalyseCreateView.as_view(), name='analyse_create'),
                  path('analyses/<int:pk>/update/', AnalyseUpdateView.as_view(), name='analyse_update'),
                  path('analyses/<int:pk>/delete/', AnalyseDeleteView.as_view(), name='analyse_delete'),

                  # URLS pour echantillon
                  path('prelevements/', EchantillonListView.as_view(), name='echantillons_list'),


                  # URLS pour echantillon
                  # path('examens/', EchantillonListView.as_view(), name='echantillons_list'),


                  # URLS pour Examen
                  path('examens/', ExamenResultatsListView.as_view(), name='resultatsexam'),
                  path('examens/resultats', ExamenListView.as_view(), name='examen_list'),
                  path('examens/<int:pk>/', ExamenDetailView.as_view(), name='examen_detail'),
                  path('examens/create/', ExamenCreateView.as_view(), name='examen_create'),
                  path('examens/<int:pk>/update/', ExamenUpdateView.as_view(), name='examen_update'),
                  path('examens/<int:pk>/delete/', ExamenDeleteView.as_view(), name='examen_delete'),

                  path('examen/<int:consultation_id>/echantillon/create/', create_echantillon, name='create_echantillon'),
                  path('examen/<int:consultation_id>/echantillon/<int:echantillon_id>/delete/', delete_echantillon, name='delete_echantillon'),

              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
