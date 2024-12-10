from django.conf.urls.static import static
from django.urls import path

from pharmacy.views import PharmacyListView, MedicamentDetailView, MedicamentCreateView, MedicamentUpdateView, \
    MedicamentDeleteView, MouvementStockListView, MouvementStockDetailView, MouvementStockCreateView, \
    MouvementStockUpdateView, MouvementStockDeleteView, RendezVousListView, MedicamentListView
from smitci import settings

urlpatterns = [
                  path('medicaments/', MedicamentListView.as_view(), name='medicaments'),
                  path('medicaments/details/<int:pk>/', MedicamentDetailView.as_view(), name='medicaments-detail'),
                  path('medicaments/create', MedicamentCreateView.as_view(), name='medicaments-create'),
                  path('medicaments/update', MedicamentUpdateView.as_view(), name='medicaments-update'),
                  path('medicaments/delete', MedicamentDeleteView.as_view(), name='medicaments-delete'),

                  path('mouvement/stock/', MouvementStockListView.as_view(), name='mouvement-stock'),
                  path('mouvement/stock/details', MouvementStockDetailView.as_view(), name='mouvement-detail'),
                  path('mouvement/stock/create', MouvementStockCreateView.as_view(), name='mouvement-create'),
                  path('mouvement/stock/update', MouvementStockUpdateView.as_view(), name='mouvement-update'),
                  path('mouvement/stock/delete', MouvementStockDeleteView.as_view(), name='mouvement-delete'),

                  path('rendez-vous/', RendezVousListView.as_view(), name='appointment_pharmacie'),


] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)