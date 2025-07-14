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
