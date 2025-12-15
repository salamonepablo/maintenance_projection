# Tarea: Script de Ingesta de Datos Históricos (ETL)

Actúa como Ingeniero de Datos Senior en Python/Django.
Tengo un archivo Excel con 3 hojas (exportadas a CSV) que contienen la historia clínica de la flota CSR. Necesito que generes un **Management Command de Django** (`import_legacy_data.py`) para poblar la base de datos inicial.

## 1. Archivos Fuente y Mapeo
Utiliza `pandas` para leer los datos. El orden de carga es CRÍTICO para respetar las Foreign Keys.

### A. Primero: Carga de Flota (`Modulos.csv`)
* **Contenido:** Inventario de unidades (Módulos 01-86).
* **Acción:** Crear instancias del modelo `FleetModule`.
* **Lógica:**
    * `id`: Tomar del CSV (ej: 01, 45).
    * `tipo_formacion`: Si ID <= 42 asignar 'CUADRUPLA', si ID >= 43 asignar 'TRIPLA'.
    * `fecha_puesta_servicio`: Parsear fecha del CSV.
    * `km_acumulado`: Inicializar en 0 (se actualizará con las lecturas).

### B. Segundo: Carga de Historial de Mantenimiento (`MantEvents.csv`)
* **Contenido:** Reparaciones pasadas (Anual, Bianual, etc.).
* **Acción:** Crear instancias del modelo `MaintenanceEvent`.
* **Lógica:**
    * Buscar el `FleetModule` correspondiente por ID.
    * `tipo_evento`: Mapear el texto del CSV (ej. "A", "B", "M1") a las constantes del modelo.
    * `fecha_evento`: Parsear fecha.
    * `km_al_evento`: Guardar el kilometraje que tenía la unidad en ese momento.

### C. Tercero: Carga de Odómetros (`LecturasDiariasKm.csv`)
* **Contenido:** Lecturas diarias o periódicas del odómetro.
* **Acción:** Crear instancias de `OdometerLog` y actualizar el estado actual del Módulo.
* **Lógica:**
    * Iterar cronológicamente (ordenar por fecha ascendente).
    * Para cada lectura:
        1. Crear registro en `OdometerLog` vinculado al `FleetModule`.
        2. Actualizar el campo `km_acumulado_total` en el objeto `FleetModule` con el valor más reciente.
        3. Calcular el promedio de uso diario (rolling average) de los últimos 60 días y guardarlo en el Módulo (para la proyección futura).

## 2. Requerimientos Técnicos
* Usa `pandas.read_csv()` o `pandas.read_excel()` según corresponda.
* Implementa manejo de errores: Si un Módulo no existe en el paso B o C, el script debe reportarlo (print warning) pero no detenerse.
* Usa `tqdm` si es posible para mostrar barra de progreso en la consola.
* Utiliza `transaction.atomic()` para asegurar que si falla la carga masiva, no queden datos a medias.

## 3. Salida Esperada
Genera el código completo del archivo `management/commands/import_legacy_data.py`.