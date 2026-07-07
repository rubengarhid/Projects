# Pipeline ETL Definitivo

Pipeline ETL modular y configurable en Python, construido con **Polars** (transformación
en memoria de alto rendimiento) y **DuckDB** (motor SQL local, warehouse y auditoría).
Incluye validación de datos con cuarentena de registros erróneos, historial de
ejecuciones y un dashboard interactivo en Streamlit.

## 1. Instalación (en VSCode / terminal)

```bash
# 1. Crea y activa un entorno virtual (recomendado)
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate

# 2. Instala las dependencias
pip install -r requirements.txt
```

## 2. Generar datos de prueba (sucios a propósito)

```bash
python generate_mock_data.py --customers 200 --sales 1000
```

Esto crea `data/raw/customers.csv` y `data/raw/sales.csv`, con nulos, precios
negativos, emails inválidos, fechas mal formateadas y duplicados — para que
puedas ver la cuarentena en acción.

## 3. Ejecutar el pipeline por CLI

```bash
python run_pipeline.py --config config/sales_pipeline.yaml
```

Salida esperada: logs enriquecidos por consola, un archivo CSV de cuarentena en
`data/quarantine/`, la tabla `sales_fact` cargada en
`data/warehouse/sales_warehouse.duckdb`, y el historial/las métricas guardadas
en `data/warehouse/audit.duckdb`.

El código de salida es `0` si tuvo éxito y `1` si falló (útil para CI/CD).

## 4. Lanzar el dashboard interactivo

```bash
streamlit run dashboard/app.py
```

Se abrirá en `http://localhost:8501` con:
- Historial de ejecuciones y tasa de éxito.
- Diagrama de flujo del pipeline.
- Métricas de calidad (gráficos de filas válidas vs. cuarentena, por regla).
- Explorador de registros en cuarentena con filtros.
- Vista previa de la tabla del data warehouse.
- Botón para lanzar el pipeline con un clic.

## 5. Estructura del proyecto

```
etl_pipeline/
├── config/
│   └── sales_pipeline.yaml     # Configuración de ejemplo (editable)
├── dashboard/
│   └── app.py                  # Dashboard Streamlit
├── data/
│   ├── raw/                    # CSVs de entrada
│   ├── quarantine/              # Registros rechazados
│   └── warehouse/               # DuckDB: warehouse + auditoría
├── src/
│   ├── core/
│   │   ├── config.py           # Modelos Pydantic de configuración
│   │   ├── logger.py           # Logging (rich + JSON)
│   │   └── pipeline.py         # Orquestador Extract→Transform→Validate→Load
│   ├── extract/extractor.py    # CSV, JSON, Parquet, DuckDB, API REST (retries)
│   ├── transform/transformer.py# rename, cast, clean, filter, join, aggregate, SQL
│   ├── validate/validator.py   # Reglas de calidad + cuarentena con motivo exacto
│   ├── load/loader.py          # overwrite / append / upsert a parquet/csv/duckdb
│   └── utils/db.py             # Base de datos de auditoría (DuckDB)
├── generate_mock_data.py       # Genera datos de prueba "sucios"
├── run_pipeline.py             # CLI: python run_pipeline.py --config ...
└── requirements.txt
```

## 6. Crear tu propio pipeline

Duplica `config/sales_pipeline.yaml` y ajusta:
- `sources`: define tus orígenes (csv/json/parquet/api/duckdb).
- `primary_source`: la fuente por la que empiezan las transformaciones.
- `transforms`: lista ordenada de pasos (`cast`, `join`, `filter`, `derive`,
  `rename`, `clean_strings`, `aggregate`, `sql`).
- `validations`: reglas de calidad (`not_null`, `min_value`, `max_value`,
  `regex`, `unique`, `allowed_values`, `dtype`), con `severity: error` (va a
  cuarentena) o `warning` (solo se registra).
- `destination`: `parquet`, `csv` o `duckdb`, con modo `overwrite`, `append` o
  `upsert` (requiere `upsert_keys`).

Después ejecútalo igual que el de ejemplo:
```bash
python run_pipeline.py --config config/mi_pipeline.yaml
```

## Notas técnicas

- **Extracción de APIs**: usa reintentos automáticos con backoff exponencial
  (`tenacity`) configurables por fuente (`max_retries`, `timeout_seconds`).
- **Validación**: cada regla con `severity: error` que falle envía la fila
  completa a cuarentena con el motivo exacto (columna + tipo de check).
- **Auditoría**: cada ejecución queda registrada en `pipeline_runs`,
  `quarantine_records` y `quality_metrics` dentro de `audit.duckdb`.
