from django import template

register = template.Library()


@register.filter
def to_percent(val):
    return f"{round(float(val) * 100, 2)}%"