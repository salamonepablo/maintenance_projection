"""
Script de diagnostico para detectar datos corruptos en lecturas de odometro.

Uso:
    python manage.py shell
    >>> exec(open('diagnose_data_win.py', encoding='utf-8').read())
"""

from maintenance.models import OdometerLog, FleetModule
from django.db.models import Sum, Count, Min, Max
from datetime import date

def diagnose_odometer_data():
    """Ejecuta multiples checks de integridad de datos."""
    
    print("=" * 80)
    print("DIAGNOSTICO DE DATOS DE ODOMETRO")
    print("=" * 80)
    
    # 1. Deltas negativos
    print("\n1. DELTAS NEGATIVOS (Lecturas que disminuyen)")
    print("-" * 80)
    
    corrupt_logs = OdometerLog.objects.filter(daily_delta_km__lt=0).select_related('fleet_module')
    count = corrupt_logs.count()
    
    if count == 0:
        print("[OK] No se encontraron deltas negativos")
    else:
        print(f"[ERROR] Se encontraron {count} registros con delta negativo:")
        print(f"{'Modulo':<10} {'Fecha':<12} {'Lectura':<15} {'Delta':<15}")
        print("-" * 80)
        
        for log in corrupt_logs[:20]:
            print(f"{log.fleet_module.id:02d}         {log.reading_date}  {log.odometer_reading:>12,}  {log.daily_delta_km:>12,}")
        
        if count > 20:
            print(f"\n... y {count - 20} mas")
    
    # 2. Deltas None
    print("\n2. DELTAS NULOS (Primera lectura sin referencia)")
    print("-" * 80)
    
    null_deltas = OdometerLog.objects.filter(daily_delta_km__isnull=True).select_related('fleet_module')
    count_null = null_deltas.count()
    
    print(f"[INFO] Se encontraron {count_null} registros con delta NULL")
    print("(Esto es normal para la primera lectura de cada modulo)")
    
    # Verificar que solo haya una por modulo
    modules_with_nulls = null_deltas.values('fleet_module').annotate(count=Count('id'))
    problematic = [m for m in modules_with_nulls if m['count'] > 1]
    
    if problematic:
        print(f"[WARN] {len(problematic)} modulos tienen multiples deltas NULL:")
        for m in problematic:
            print(f"   Modulo {m['fleet_module']:02d}: {m['count']} registros NULL")
    
    # 3. Lecturas duplicadas (misma fecha)
    print("\n3. LECTURAS DUPLICADAS (Mismo modulo + fecha)")
    print("-" * 80)
    
    duplicates = OdometerLog.objects.values('fleet_module', 'reading_date')\
        .annotate(count=Count('id')).filter(count__gt=1)
    
    if duplicates.count() == 0:
        print("[OK] No se encontraron lecturas duplicadas")
    else:
        print(f"[ERROR] Se encontraron {duplicates.count()} fechas con lecturas duplicadas")
    
    # 4. Estadisticas generales
    print("\n4. ESTADISTICAS GENERALES")
    print("-" * 80)
    
    total_logs = OdometerLog.objects.count()
    total_modules = FleetModule.objects.count()
    active_modules = FleetModule.objects.exclude(id__in=[47, 67]).count()
    
    print(f"Total lecturas:           {total_logs:>10,}")
    print(f"Modulos totales:          {total_modules:>10}")
    print(f"Modulos activos:          {active_modules:>10}")
    print(f"Promedio lecturas/modulo: {total_logs // total_modules:>10}")
    
    # 5. Rango de fechas
    print("\n5. RANGO DE FECHAS")
    print("-" * 80)
    
    date_range = OdometerLog.objects.aggregate(
        min_date=Min('reading_date'),
        max_date=Max('reading_date')
    )
    
    if date_range['min_date'] and date_range['max_date']:
        print(f"Primera lectura: {date_range['min_date']}")
        print(f"Ultima lectura:  {date_range['max_date']}")
        days = (date_range['max_date'] - date_range['min_date']).days
        print(f"Periodo:         {days} dias")
    
    # 6. Kilometraje del mes actual
    print("\n6. KILOMETRAJE DICIEMBRE 2025")
    print("-" * 80)
    
    today = date.today()
    first_of_month = date(today.year, today.month, 1)
    
    month_stats = OdometerLog.objects.filter(
        reading_date__gte=first_of_month
    ).aggregate(
        total_deltas=Sum('daily_delta_km'),
        count=Count('id')
    )
    
    total_month = month_stats['total_deltas'] or 0
    count_month = month_stats['count'] or 0
    
    print(f"Total deltas del mes:  {total_month:>15,} km")
    print(f"Cantidad de lecturas:  {count_month:>15,}")
    
    if total_month < 0:
        print("[ERROR] El total del mes es NEGATIVO")
        print("   Esto confirma que hay datos corruptos afectando las estadisticas")
    else:
        print("[OK] El total del mes es positivo")
    
    # 7. Top 5 modulos con mas deltas negativos
    print("\n7. TOP 5 MODULOS CON MAS DELTAS NEGATIVOS")
    print("-" * 80)
    
    top_corrupt = OdometerLog.objects.filter(daily_delta_km__lt=0)\
        .values('fleet_module')\
        .annotate(
            count=Count('id'),
            total_negative=Sum('daily_delta_km')
        )\
        .order_by('total_negative')[:5]
    
    if top_corrupt:
        print(f"{'Modulo':<10} {'Cant.':<10} {'Total Negativo':<20}")
        print("-" * 80)
        for item in top_corrupt:
            print(f"{item['fleet_module']:02d}         {item['count']:<10} {item['total_negative']:>15,} km")
    else:
        print("[OK] No hay modulos con deltas negativos")
    
    print("\n" + "=" * 80)
    print("DIAGNOSTICO COMPLETADO")
    print("=" * 80)

# Ejecutar diagnostico
if __name__ == '__main__':
    diagnose_odometer_data()
else:
    # Si se ejecuta con exec()
    diagnose_odometer_data()
