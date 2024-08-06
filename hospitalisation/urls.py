

from django.conf.urls.static import static
from django.urls import path

from hospitalisation.views import HospitalisationListView, HospitalisationUniteListView
from smitci import settings

urlpatterns = [
                  path('generale', HospitalisationListView.as_view(), name='hospitalisation'),
                  path('unites', HospitalisationUniteListView.as_view(), name='hospi_unites'),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)