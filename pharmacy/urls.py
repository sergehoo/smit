from django.conf.urls.static import static
from django.urls import path

from pharmacy.views import PharmacyListView, MedicamentDetailView, MedicamentCreateView, MedicamentUpdateView, \
    MedicamentDeleteView, MouvementStockListView, MouvementStockDetailView, MouvementStockCreateView, \
    MouvementStockUpdateView, MouvementStockDeleteView, RendezVousListView, MedicamentListView, RendezVousCreateView, \
    RendezVousUpdateView, RendezVousDeleteView, complete_appointment, reschedule_appointment, search_rendezvous, \
    CommandeListView, CommandeDetailView, CommandeCreateView, CommandeUpdateView, CommandeDeleteView
from smitci import settings

urlpatterns = [
                  path('medicaments/', MedicamentListView.as_view(), name='medicaments'),
                  path('medicaments/details/<int:pk>/', MedicamentDetailView.as_view(), name='medicaments-detail'),
                  path('medicaments/create', MedicamentCreateView.as_view(), name='medicaments-create'),
                  path('medicaments/update', MedicamentUpdateView.as_view(), name='medicaments-update'),
                  path('medicaments/delete', MedicamentDeleteView.as_view(), name='medicaments-delete'),

                  path('mouvement/stock/', MouvementStockListView.as_view(), name='mouvement-stock'),
                  path('mouvement/stock/details<int:pk>', MouvementStockDetailView.as_view(), name='mouvement-detail'),
                  path('mouvement/stock/create', MouvementStockCreateView.as_view(), name='mouvement-create'),
                  path('mouvement/stock/update', MouvementStockUpdateView.as_view(), name='mouvement-update'),
                  path('mouvement/stock/delete<int:pk>', MouvementStockDeleteView.as_view(), name='mouvement-delete'),

                  path('rdv', RendezVousListView.as_view(), name='rendezvous_list'),
                  path('search_rendezvous/', search_rendezvous, name='search_rendezvous'),

                  path('rendezvous/create/', RendezVousCreateView.as_view(), name='rendezvous_create'),
                  path('rendezvous/<int:pk>/update/', RendezVousUpdateView.as_view(), name='rendezvous_update'),
                  path('rendezvous/<int:pk>/delete/', RendezVousDeleteView.as_view(), name='rendezvous_delete'),
                  path('rendezvous/<int:pk>/complete/', complete_appointment, name='complete_appointment'),
                  path('rendezvous/<int:pk>/reschedule/', reschedule_appointment, name='reschedule_appointment'),
                  path('rendez-vous/', RendezVousListView.as_view(), name='appointment_pharmacie'),

                  path('commandes', CommandeListView.as_view(), name='commandes-list'),
                  path('commandes/detail/<int:pk>', CommandeDetailView.as_view(), name='commandes-detail'),
                  path('commandes/create', CommandeCreateView.as_view(), name='commandes-create'),
                  path('commandes/upadate/<int:pk>', CommandeUpdateView.as_view(), name='commandes-update'),
                  path('commandes/delete/<int:pk>', CommandeDeleteView.as_view(), name='commandes-delete'),

              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
