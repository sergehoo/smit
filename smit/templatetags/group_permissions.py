from django import template
from itertools import groupby

register = template.Library()


@register.filter
def group_by_content_type(permissions):
    grouped = {}
    for perm in permissions:
        model_name = perm.content_type.model
        if model_name not in grouped:
            grouped[model_name] = []
        grouped[model_name].append(perm)
    return grouped.items()
