from django import template

register = template.Library()

@register.filter
def filter_by_status(queryset, status):
    """Filtre un queryset par statut"""
    if hasattr(queryset, 'filter'):
        return queryset.filter(status=status)
    return []

@register.filter
def filter_by_result(queryset, result):
    """Filtre un queryset par résultat"""
    if hasattr(queryset, 'filter'):
        return queryset.filter(resultat=result)
    return []

@register.filter
def get_item(dictionary, key):
    """Récupère un élément d'un dictionnaire"""
    return dictionary.get(key)

@register.filter
def multiply(value, arg):
    """Multiplie value par arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divise value par arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def percentage(value, total):
    """Calcule le pourcentage"""
    try:
        if total == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def status_color(status):
    """Retourne la couleur CSS selon le statut"""
    colors = {
        'completed': 'success',
        'confirmed': 'success',
        'active': 'primary',
        'in_progress': 'primary',
        'discharged': 'info',
        'pending': 'warning',
        'cancelled': 'danger',
        'transferred': 'secondary',
    }
    return colors.get(status, 'secondary')

@register.filter
def urgency_color(is_urgent):
    """Retourne la couleur selon l'urgence"""
    return 'danger' if is_urgent else 'secondary'

@register.filter
def age_range(age):
    """Retourne la tranche d'âge"""
    if age < 18:
        return 'enfant'
    elif age < 30:
        return 'jeune adulte'
    elif age < 60:
        return 'adulte'
    else:
        return 'senior'
@register.filter
def get_etat_count(appareils_by_categories, etat):
    count = 0
    for categorie, appareils in appareils_by_categories.items():
        for appareil in appareils:
            if appareil.etat == etat:
                count += 1
    return count


@register.filter
def get_execution_for_day(prescription, date):
    """Récupère les exécutions d'une prescription pour une date donnée"""
    return prescription.executions.filter(
        scheduled_time__date=date
    )


@register.filter
def get_execution_for_time(executions, time_slot):
    """Récupère l'exécution pour un créneau horaire donné"""
    time_mapping = {
        'morning': (6, 12),  # 6h-12h
        'noon': (12, 14),  # 12h-14h
        'evening': (18, 23)  # 18h-23h
    }

    if time_slot in time_mapping:
        start_hour, end_hour = time_mapping[time_slot]
        for execution in executions:
            if start_hour <= execution.scheduled_time.hour < end_hour:
                return execution
    return None


@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={'class': css_class})


@register.filter(name='attr')
def attr(field, attr):
    attr_name, attr_value = attr.split(':', 1)
    attrs = field.field.widget.attrs.copy()
    attrs[attr_name] = attr_value
    return field.as_widget(attrs=attrs)


@register.filter
def get_item(dictionary, key):
    """Retourne la valeur d'un dictionnaire pour une clé donnée"""
    return dictionary.get(key, 0)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')


@register.filter
def abs(value):
    try:
        return abs(value)
    except:
        return value


@register.filter
def calculate_weight_change(current_weight, patient):
    # Calcule la variation de poids par rapport au poids initial
    if not current_weight or not hasattr(patient, 'poids_initial') or not patient.poids_initial:
        return ""

    change = current_weight - patient.poids_initial
    if change > 0:
        return f"+{change:.1f} kg"
    elif change < 0:
        return f"{change:.1f} kg"
    else:
        return "stable"


@register.filter
def sub(value, arg):
    """Soustrait arg à value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def div(value, arg):
    """Divise value par arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def mul(value, arg):
    """Multiplie value par arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def abs_filter(value):
    """Retourne la valeur absolue"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value

@register.filter
def timesince_days(date):
    """Retourne le nombre de jours depuis une date"""
    from django.utils import timezone
    if not date:
        return None
    delta = timezone.now().date() - date
    return delta.days

@register.filter
def timeuntil_days(date):
    """Retourne le nombre de jours jusqu'à une date"""
    from django.utils import timezone
    if not date:
        return None
    delta = date - timezone.now().date()
    return delta.days if delta.days >= 0 else -delta.days

@register.filter
def get_item(dictionary, key):
    """Retourne un élément d'un dictionnaire"""
    return dictionary.get(key)

@register.filter
def multiply(value, arg):
    """Multiplie value par arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divise value par arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def safe_get(obj, attr_name):
    """
    Retourne getattr(obj, attr_name) si existe, sinon None.
    Marche aussi si obj est un dict.
    """
    if obj is None or not attr_name:
        return None

    # dict-like
    if isinstance(obj, dict):
        return obj.get(attr_name)

    # objet Django / python
    return getattr(obj, attr_name, None)
