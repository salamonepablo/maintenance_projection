"""
Script de correccion para recalcular todos los daily_delta_km.

IMPORTANTE: Este script modifica la base de datos.
Hacer backup antes de ejecutar.

Uso:
    python manage.py shell
    >>> exec(open('fix_corrupt_deltas_win.py', encoding='utf-8').read())
    >>> recalculate_all_deltas(dry_run=True)   # Simulacion
    >>> recalculate_all_deltas(dry_run=False)  # Aplicar cambios
"""

from maintenance.models import OdometerLog, FleetModule
from django.db import transaction

def recalculate_all_deltas(dry_run=True):
    """
    Recalcula todos los daily_delta_km para todos los modulos.
    
    Args:
        dry_run: Si True, solo muestra lo que haria sin modificar la BD
    """
    
    print("=" * 80)
    if dry_run:
        print("RECALCULO DE DELTAS - SIMULACION")
    else:
        print("RECALCULO DE DELTAS - EJECUCION REAL")
    print("=" * 80)
    
    if not dry_run:
        response = input("\nSeguro que deseas modificar la base de datos? (escribir 'SI'): ")
        if response != 'SI':
            print("[CANCELADO] Operacion cancelada")
            return
    
    modules = FleetModule.objects.all().order_by('id')
    
    total_updated = 0
    total_logs = 0
    errors = []
    
    print(f"\nProcesando {modules.count()} modulos...")
    
    for module in modules:
        # Obtener todas las lecturas del modulo ordenadas
        logs = list(
            OdometerLog.objects.filter(fleet_module=module)
            .order_by('reading_date', 'id')
        )
        
        if not logs:
            continue
        
        print(f"\nModulo {module.id:02d} - {len(logs)} lecturas")
        
        with transaction.atomic():
            previous_log = None
            
            for log in logs:
                total_logs += 1
                old_delta = log.daily_delta_km
                
                # Calcular nuevo delta
                if previous_log:
                    new_delta = log.odometer_reading - previous_log.odometer_reading
                else:
                    new_delta = None
                
                # Verificar si cambio
                if old_delta != new_delta:
                    total_updated += 1
                    
                    if old_delta is not None and new_delta is not None:
                        diff = new_delta - old_delta
                        print(f"   {log.reading_date}: {old_delta:>10,} -> {new_delta:>10,} (Delta: {diff:>10,})")
                    
                    if not dry_run:
                        log.daily_delta_km = new_delta
                        log.save(update_fields=['daily_delta_km'])
                
                # Validar que no sea excesivamente negativo
                if new_delta is not None and new_delta < -50000:
                    errors.append(f"Modulo {module.id:02d} - {log.reading_date}: Delta sospechoso {new_delta:,} km")
                
                previous_log = log
            
            # Actualizar kilometraje acumulado del modulo
            if logs:
                latest_km = logs[-1].odometer_reading
                if module.total_accumulated_km != latest_km:
                    print(f"   Acumulado: {module.total_accumulated_km:,} -> {latest_km:,}")
                    
                    if not dry_run:
                        module.total_accumulated_km = latest_km
                        module.save(update_fields=['total_accumulated_km'])
    
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print(f"Total lecturas procesadas: {total_logs:>10,}")
    print(f"Deltas actualizados:       {total_updated:>10,}")
    
    if errors:
        print(f"\n[WARN] Se encontraron {len(errors)} advertencias:")
        for error in errors[:10]:
            print(f"   - {error}")
        if len(errors) > 10:
            print(f"   ... y {len(errors) - 10} mas")
    
    if dry_run:
        print("\n[INFO] Esto fue una SIMULACION. Para aplicar cambios, ejecutar:")
        print("   recalculate_all_deltas(dry_run=False)")
    else:
        print("\n[OK] CAMBIOS APLICADOS A LA BASE DE DATOS")
    
    print("=" * 80)

def quick_fix_negatives():
    """
    Fix rapido: pone en 0 todos los deltas negativos sin recalcular.
    Util si hay pocos casos y no queremos recalcular todo.
    """
    
    print("FIX RAPIDO: Anular deltas negativos")
    
    negative_logs = OdometerLog.objects.filter(daily_delta_km__lt=0)
    count = negative_logs.count()
    
    if count == 0:
        print("[OK] No hay deltas negativos que corregir")
        return
    
    print(f"Se encontraron {count} deltas negativos")
    response = input("Poner todos en 0? (escribir 'SI'): ")
    
    if response == 'SI':
        updated = negative_logs.update(daily_delta_km=0)
        print(f"[OK] {updated} registros actualizados")
    else:
        print("[CANCELADO] Operacion cancelada")

print("\n" + "=" * 80)
print("OPCIONES DE CORRECCION")
print("=" * 80)
print("1. recalculate_all_deltas(dry_run=True)   - Simular recalculo completo")
print("2. recalculate_all_deltas(dry_run=False)  - Aplicar recalculo completo")
print("3. quick_fix_negatives()                   - Solo anular negativos")
print("=" * 80)
