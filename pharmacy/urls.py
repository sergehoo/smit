from django.conf.urls.static import static
from django.urls import path

from pharmacy.views import PharmacyListView
from smitci import settings

urlpatterns = [
                  path('medicaments/', PharmacyListView.as_view(), name='medicaments'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)