"""
Filtros personalizados de template para mantenimiento.
"""
from django import template

register = template.Library()


@register.filter
def european_format(value):
    """
    Formatea números enteros con separador de miles en estilo europeo.
    Ejemplo: 333996 → 333.996
    """
    try:
        # Convertir a entero si es necesario
        if isinstance(value, str):
            value = int(value)
        elif isinstance(value, float):
            value = int(value)
        
        # Formatear con separador de miles (punto)
        return f"{value:,}".replace(",", ".")
    except (ValueError, TypeError):
        return value
