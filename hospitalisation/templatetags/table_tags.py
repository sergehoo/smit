from django import template

register = template.Library()


@register.filter
def table_page_range(page, paginator):
    """
    Custom filter to generate page range for tables
    """
    return paginator.get_elided_page_range(page.number, on_each_side=2, on_ends=1)
