from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from core.api.views import fetch_medicaments, categories_api, molecules_api, api_mouvement_stock_list

urlpatterns = [
                  # path('medicamentsserach/', search_medicaments, name='medicamentsapi'),
                  # path('medicaments', MedicamentFilterView.as_view(), name='medicament_filter'),
                  path('list/medicaments/', fetch_medicaments, name='fetch_medicaments'),
                  path('list/categorie/', categories_api, name='fetch_categories'),
                  path('list/molecule/', molecules_api, name='fetch_molecules'),
                  path('list/mouvements/', api_mouvement_stock_list, name='api_mouvement_stock_list'),

              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
