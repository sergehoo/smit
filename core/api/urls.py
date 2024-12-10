from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from core.api.views import search_medicaments, MedicamentFilterView

urlpatterns = [
                  path('medicamentsserach/', search_medicaments, name='medicamentsapi'),
                  path('medicaments', MedicamentFilterView.as_view(), name='medicament_filter'),

              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
