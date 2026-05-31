from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Filtro para obtener un valor de un diccionario en Django templates.
    Uso: {{ diccionario|get_item:clave }}
    """
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(key)
