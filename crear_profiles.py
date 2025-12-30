"""
Crea los 6 perfiles de mantenimiento según normativa CNRT.

Este script crea los MaintenanceProfile en la base de datos Django
(PostgreSQL/SQLite), NO modifica la base de datos Access.

Basado en: context/MAINTENANCE_CYCLE.md
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from maintenance.models import MaintenanceProfile

print("="*80)
print("CREANDO PERFILES DE MANTENIMIENTO")
print("="*80)
print()

# Borrar perfiles existentes (opcional, para evitar duplicados)
existing = MaintenanceProfile.objects.all().count()
if existing > 0:
    print(f"⚠ Ya existen {existing} perfiles. ¿Borrarlos? (s/n): ", end='')
    respuesta = input().lower()
    if respuesta == 's':
        MaintenanceProfile.objects.all().delete()
        print("✓ Perfiles anteriores borrados")
    print()

# Crear los 6 perfiles
profiles = [
    {
        'maintenance_type': 'IQ',
        'km_interval': 6250,
        'time_interval_days': 15,
        'description': 'Mantenimiento Quincenal'
    },
    {
        'maintenance_type': 'B',
        'km_interval': 25000,
        'time_interval_days': 60,
        'description': 'Mantenimiento Bimestral'
    },
    {
        'maintenance_type': 'A',
        'km_interval': 187500,
        'time_interval_days': 457,  # 15 meses
        'description': 'Mantenimiento Anual'
    },
    {
        'maintenance_type': 'BI',
        'km_interval': 375000,
        'time_interval_days': 913,  # 2.5 años
        'description': 'Mantenimiento Bianual'
    },
    {
        'maintenance_type': 'P',
        'km_interval': 750000,
        'time_interval_days': 1826,  # 5 años
        'description': 'Mantenimiento Pentanual'
    },
    {
        'maintenance_type': 'DE',
        'km_interval': 1500000,
        'time_interval_days': 3652,  # 10 años
        'description': 'Mantenimiento Decanual'
    },
]

print("Creando perfiles...")
print()

for profile_data in profiles:
    profile, created = MaintenanceProfile.objects.get_or_create(
        maintenance_type=profile_data['maintenance_type'],
        defaults={
            'km_interval': profile_data['km_interval'],
            'time_interval_days': profile_data['time_interval_days'],
        }
    )
    
    status = "✓ Creado" if created else "○ Ya existía"
    print(f"{status}: {profile_data['maintenance_type']:<3} - "
          f"{profile_data['description']:<25} - "
          f"{profile_data['km_interval']:>9,} km / "
          f"{profile_data['time_interval_days']:>4} días")

print()
print("="*80)
print(f"✓ Total de perfiles: {MaintenanceProfile.objects.count()}")
print("="*80)
print()
print("Siguiente paso: python manage.py sync_from_access")
