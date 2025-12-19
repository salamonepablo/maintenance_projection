# Exportación de proyecciones a Excel

## Dependencias

La exportación a Excel usa **openpyxl**. Asegurate de instalar las dependencias:

```bash
python -m pip install -r requirements.txt
```

## Comando de exportación

Para generar un archivo Excel desde la línea de comandos:

```bash
python manage.py generate_projection --all --excel --output proyeccion.xlsx
```

Opcionalmente, podés exportar para un módulo específico:

```bash
python manage.py generate_projection --module 5 --excel --output proyeccion_modulo_5.xlsx
```
