# core/management/commands/create_vih_profiles_from_codes.py

from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils import timezone

from core.models import Patient, VIHProfile  # ✅ adapte l'import si besoin


class Command(BaseCommand):
    help = (
        "Crée un VIHProfile pour tous les patients dont code_vih commence par "
        "BMI/AMI/BMP/BMU ou contient ces chaînes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulation: n'écrit rien en base, affiche seulement ce qui serait fait.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limiter le nombre de patients traités (debug).",
        )

    def _make_unique_profile_code(self, base_code: str) -> str:
        """
        VIHProfile.code_vih est unique. On tente base_code, sinon base_code-1, -2, etc.
        """
        base_code = (base_code or "").strip()
        if not base_code:
            # fallback: on laisse save() générer
            return ""

        if not VIHProfile.objects.filter(code_vih=base_code).exists():
            return base_code

        i = 1
        while True:
            candidate = f"{base_code}-{i}"
            if not VIHProfile.objects.filter(code_vih=candidate).exists():
                return candidate
            i += 1

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]

        prefixes = ["BMI", "AMI", "BMP", "BMU"]

        # startswith OU contains
        q = Q()
        for p in prefixes:
            q |= Q(code_vih__istartswith=p) | Q(code_vih__icontains=p)

        qs = (
            Patient.objects
            .filter(q)
            .exclude(code_vih__isnull=True)
            .exclude(code_vih__exact="")
            .select_related("vih_profile")  # ✅ pour éviter requêtes en boucle
        )

        if limit:
            qs = qs[:limit]

        total = qs.count()
        created = 0
        skipped_has_profile = 0
        skipped_invalid = 0
        errors = 0

        self.stdout.write(self.style.NOTICE(f"Patients trouvés: {total}"))
        if dry_run:
            self.stdout.write(self.style.WARNING("Mode DRY-RUN activé (aucune écriture)."))

        for patient in qs.iterator(chunk_size=500):
            try:
                # 1) Si déjà un profile -> skip
                if hasattr(patient, "vih_profile") and patient.vih_profile_id:
                    skipped_has_profile += 1
                    continue

                # 2) code_vih patient obligatoire (sinon skip)
                patient_code = (patient.code_vih or "").strip()
                if not patient_code:
                    skipped_invalid += 1
                    continue

                # 3) Construire un code VIHProfile unique
                profile_code = self._make_unique_profile_code(patient_code)

                if dry_run:
                    created += 1
                    continue

                # 4) Création atomique
                with transaction.atomic():
                    # Re-check en base au cas où (race condition)
                    if VIHProfile.objects.select_for_update().filter(patient=patient).exists():
                        skipped_has_profile += 1
                        continue

                    profile = VIHProfile(
                        patient=patient,
                        code_vih=profile_code,   # si "" => le save() générera
                        site_code=None,
                        numero_dossier_vih=None,
                        status=VIHProfile.VIHStatus.ACTIVE,
                        # dates clés: on ne met rien par défaut
                        created_at=timezone.now(),  # pas obligatoire (auto_now_add)
                        updated_at=timezone.now(),  # pas obligatoire (auto_now)
                    )
                    profile.save()
                    created += 1

            except IntegrityError as e:
                # collision unique ou autre contrainte
                errors += 1
                self.stdout.write(self.style.ERROR(
                    f"[IntegrityError] patient={patient.id} code_vih={patient.code_vih} => {e}"
                ))
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(
                    f"[Error] patient={patient.id} code_vih={patient.code_vih} => {e}"
                ))

        self.stdout.write("\n" + "-" * 60)
        self.stdout.write(self.style.SUCCESS(f"Créés: {created}"))
        self.stdout.write(self.style.WARNING(f"Déjà avec VIHProfile: {skipped_has_profile}"))
        self.stdout.write(self.style.WARNING(f"Code VIH vide/invalide: {skipped_invalid}"))
        self.stdout.write(self.style.ERROR(f"Erreurs: {errors}"))
        self.stdout.write("-" * 60 + "\n")