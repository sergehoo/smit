from django import template

register = template.Library()


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
