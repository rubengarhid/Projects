#!/usr/bin/env python3
"""
run_pipeline.py
---------------
Punto de entrada de línea de comandos.

Uso:
    python run_pipeline.py --config config/sales_pipeline.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Permite ejecutar el script desde cualquier ubicación dentro del proyecto.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.core.pipeline import Pipeline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecuta un pipeline ETL a partir de un archivo de configuración YAML.")
    parser.add_argument("--config", "-c", required=True, help="Ruta al archivo YAML de configuración del pipeline.")
    args = parser.parse_args()

    if not Path(args.config).exists():
        print(f"ERROR: no se encontró el archivo de configuración '{args.config}'")
        return 1

    pipeline = Pipeline(args.config)
    success = pipeline.run()
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
