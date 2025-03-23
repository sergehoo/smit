from core.models import Employee


def get_employees_to_notify():
    """
    Retourne la liste des numéros de téléphone des employés à notifier (format international).
    """
    return [
        emp.phone for emp in Employee.objects.filter(notify_by_sms=True)
        if emp.phone
    ]