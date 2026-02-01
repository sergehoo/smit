from smit.models import InfectionOpportuniste, Comorbidite, ParaclinicalExam, DepistageVIH, TraitementARV, Suivi


@dataclass
class PatientActivityBundle:
    suivis: list
    traitements_arv: list
    exams: list
    depistages: list
    infections: list
    comorbidites: list

def get_patient_vih_activities(patient):
    suivis = (
        Suivi.objects.filter(patient=patient)
        .select_related("services", "activite")
        .order_by("-date_suivi", "-created_at")
    )

    traitements_arv = (
        TraitementARV.objects.filter(patient=patient)
        .select_related("suivi")
        .order_by("-date_mise_a_jour", "-date_creation")
    )

    exams = (
        ParaclinicalExam.objects.filter(patient=patient)
        .order_by("-performed_at", "-prescribed_at", "-created_at")
    )

    depistages = (
        DepistageVIH.objects.filter(patient=patient)
        .select_related("agent")
        .order_by("-date_test", "-created_at")
    )

    infections = (
        InfectionOpportuniste.objects.filter(patient=patient)
        .select_related("suivi")
        .order_by("-date_diagnostic", "-date_creation")
    )

    comorbidites = (
        Comorbidite.objects.filter(patient=patient)
        .select_related("suivi")
        .order_by("-date_diagnostic", "-date_creation")
    )

    return PatientActivityBundle(
        suivis=list(suivis),
        traitements_arv=list(traitements_arv),
        exams=list(exams),
        depistages=list(depistages),
        infections=list(infections),
        comorbidites=list(comorbidites),
    )