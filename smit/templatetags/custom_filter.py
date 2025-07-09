from django import template

register = template.Library()


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
