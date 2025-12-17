"""
Configuración del Django Admin para gestión de mantenimiento.

Registra los modelos principales con interfaces personalizadas.
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import FleetModule, MaintenanceEvent, MaintenanceProfile, OdometerLog


@admin.register(MaintenanceProfile)
class MaintenanceProfileAdmin(admin.ModelAdmin):
    """Administración de perfiles de mantenimiento."""

    list_display = ['code', 'name', 'maintenance_type', 'km_interval', 'time_interval_days']
    list_filter = ['maintenance_type']
    search_fields = ['name', 'code']
    ordering = ['maintenance_type', 'km_interval']


@admin.register(FleetModule)
class FleetModuleAdmin(admin.ModelAdmin):
    """Administración de módulos de flota."""

    list_display = ['id', 'module_type', 'in_service_date', 'formatted_accumulated_km', 'last_reading_date']
    list_filter = ['module_type', 'in_service_date']
    search_fields = ['id']
    ordering = ['id']
    readonly_fields = ['total_accumulated_km', 'last_reading_date', 'last_reading_km']

    def formatted_accumulated_km(self, obj):
        """Formatea kilometraje con separador de miles."""
        return f"{obj.total_accumulated_km:,} km".replace(',', '.')
    formatted_accumulated_km.short_description = 'Km Acumulados'

    def last_reading_date(self, obj):
        """Retorna fecha de última lectura."""
        latest = obj.odometer_logs.order_by('-reading_date', '-id').first()
        return latest.reading_date if latest else '—'
    last_reading_date.short_description = 'Última Lectura'

    def last_reading_km(self, obj):
        """Retorna última lectura de odómetro."""
        latest = obj.odometer_logs.order_by('-reading_date', '-id').first()
        if latest:
            return f"{latest.odometer_reading:,} km".replace(',', '.')
        return '—'
    last_reading_km.short_description = 'Último Odómetro'


@admin.register(MaintenanceEvent)
class MaintenanceEventAdmin(admin.ModelAdmin):
    """Administración de eventos de mantenimiento."""

    list_display = ['id', 'fleet_module', 'profile', 'event_date', 'formatted_odometer', 'notes_preview']
    list_filter = ['profile__code', 'event_date', 'fleet_module__module_type']
    search_fields = ['fleet_module__id', 'notes']
    date_hierarchy = 'event_date'
    ordering = ['-event_date', 'fleet_module']
    autocomplete_fields = ['fleet_module', 'profile']

    def formatted_odometer(self, obj):
        """Formatea odómetro con separador de miles."""
        return f"{obj.odometer_km:,} km".replace(',', '.')
    formatted_odometer.short_description = 'Odómetro'

    def notes_preview(self, obj):
        """Muestra preview de notas."""
        if obj.notes:
            return obj.notes[:50] + '...' if len(obj.notes) > 50 else obj.notes
        return '—'
    notes_preview.short_description = 'Observaciones'


@admin.register(OdometerLog)
class OdometerLogAdmin(admin.ModelAdmin):
    """Administración de lecturas de odómetro."""

    list_display = ['id', 'fleet_module', 'reading_date', 'formatted_reading', 'formatted_delta']
    list_filter = ['reading_date', 'fleet_module__module_type']
    search_fields = ['fleet_module__id']
    date_hierarchy = 'reading_date'
    ordering = ['-reading_date', 'fleet_module']
    readonly_fields = ['daily_delta_km']

    def formatted_reading(self, obj):
        """Formatea lectura con separador de miles."""
        return f"{obj.odometer_reading:,} km".replace(',', '.')
    formatted_reading.short_description = 'Lectura'

    def formatted_delta(self, obj):
        """Formatea delta con color según valor."""
        if obj.daily_delta_km is None:
            return '—'
        
        # Colorear según si es normal (verde) o anómalo (naranja/rojo)
        delta = obj.daily_delta_km
        if delta < 0:
            color = 'red'
        elif delta > 5000:  # Más de 5000 km de variación
            color = 'orange'
        else:
            color = 'green'
        
        # Formatear número con separador de miles (punto)
        formatted_delta = f"{delta:+,}".replace(',', '.')
        
        return format_html(
            '<span style="color: {};">{} km</span>',
            color,
            formatted_delta
        )
    formatted_delta.short_description = 'Delta'
