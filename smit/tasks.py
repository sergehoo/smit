# tasks.py
import os
from functools import wraps

from celery import shared_task
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from django.template.loader import render_to_string
from django_redis import get_redis_connection
from weasyprint import HTML
from smit.models import BilanInitial, ImagerieMedicale, analyser_image


def task_lock(key_fn, ttl=300):
    """
    Empêche l'exécution concurrente/à répétition de la même "recette".
    key_fn(self, *args, **kwargs) -> str (clé unique)
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            r = get_redis_connection("default")
            key = key_fn(*args, **kwargs)
            # SETNX + TTL
            if not r.set(name=key, value="1", nx=True, ex=ttl):
                # déjà en cours -> on ignore proprement
                return {"status": "locked", "key": key}
            try:
                return fn(*args, **kwargs)
            finally:
                # libère le lock à la fin si tu veux; sinon laisse expirer
                r.delete(key)

        return wrapper

    return decorator


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
@task_lock(key_fn=lambda *a, **k: f"task:generate_bilan_pdf:{k.get('bilan_id')}", ttl=300)
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
    output_dir = os.path.join(settings.MEDIA_ROOT, 'bilans', 'reports', str(bilan.created_at.year),
                              str(bilan.created_at.month))
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, filename)
    with open(file_path, 'wb') as f:
        f.write(pdf_file)

    bilan.report_file = os.path.relpath(file_path, settings.MEDIA_ROOT)
    bilan.save()

    return bilan.report_file


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
@task_lock(key_fn=lambda *a, **k: f"task:generate_bilan_pdf:{k.get('bilan_id')}", ttl=300)
def lancer_analyse_imagerie(imagerie_id: int):
    obj = ImagerieMedicale.objects.get(pk=imagerie_id)
    if not obj.image_file:
        return
    path = default_storage.path(obj.image_file.name)
    result = analyser_image(path)  # ta fonction

    texte = (
        f"📌 Interprétation IA : {result['categorie']}\n"
        f"⚠️ Probabilité d'anomalie : {result['probabilite']}%\n"
        f"🚦 Niveau de risque : {result['niveau_risque']}"
    )

    # Atomic update
    with transaction.atomic():
        obj.interpretation_ia = texte
        obj.detection_json = result.get("detection", {})
        obj.status = "completed"
        obj.save(update_fields=["interpretation_ia", "detection_json", "status"])
