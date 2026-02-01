from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


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
def get_item(dictionary, key):
    return dictionary.get(key)


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