# tasks.py
import os

from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML
from smit.models import BilanInitial


@shared_task
def generate_bilan_pdf(bilan_id):
    """
    Génère le PDF du BilanInitial et l'enregistre dans report_file
    """
    bilan = BilanInitial.objects.get(pk=bilan_id)
    html_string = render_to_string('pages/pdf/bilan_initial_detail.html', {'bilan': bilan})

    html = HTML(string=html_string, base_url=settings.BASE_DIR)
    pdf_file = html.write_pdf()

    # Crée un chemin unique
    filename = f'bilan_{bilan_id}.pdf'
    output_dir = os.path.join(settings.MEDIA_ROOT, 'bilans', 'reports', str(bilan.created_at.year), str(bilan.created_at.month))
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, filename)
    with open(file_path, 'wb') as f:
        f.write(pdf_file)

    bilan.report_file = os.path.relpath(file_path, settings.MEDIA_ROOT)
    bilan.save()


    return bilan.report_file