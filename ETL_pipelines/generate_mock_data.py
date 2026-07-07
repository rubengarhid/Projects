#!/usr/bin/env python3
"""
generate_mock_data.py
----------------------
Genera datos de ventas y clientes realistas pero "sucios" para demostrar
cómo el pipeline extrae, transforma, valida, pone en cuarentena y carga datos.

Suciedad introducida deliberadamente:
  * Emails inválidos o vacíos en clientes.
  * Precios negativos o nulos en ventas.
  * Fechas mal formateadas.
  * IDs de cliente en ventas que no existen en la tabla de clientes (se filtran en el join).
  * Filas duplicadas (mismo transaction_id).

Uso:
    python generate_mock_data.py --customers 200 --sales 1000
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

fake = Faker("es_ES")
random.seed(42)
Faker.seed(42)

OUT_DIR = Path("data/raw")

BAD_DATE_FORMATS = ["%d/%m/%Y", "%Y-%m-%d", "%m-%d-%Y", "not-a-date"]


def generate_customers(n: int) -> list[dict]:
    customers = []
    for i in range(1, n + 1):
        dirty_email = random.random() < 0.08
        if dirty_email:
            email = random.choice(["", "correo_invalido", "sin-arroba.com", "@dominio.com"])
        else:
            email = fake.email()

        customers.append(
            {
                "customer_id": i,
                "name": fake.name(),
                "email": email,
                "country": fake.country(),
                "signup_date": fake.date_between(start_date="-3y", end_date="today").isoformat(),
            }
        )
    return customers


def _random_bad_date() -> str:
    fmt = random.choice(BAD_DATE_FORMATS)
    if fmt == "not-a-date":
        return "31/13/2024-XX"
    d = fake.date_between(start_date="-2y", end_date="today")
    return d.strftime(fmt)


def generate_sales(n: int, num_customers: int) -> list[dict]:
    sales = []
    for i in range(1, n + 1):
        dirty_price = random.random() < 0.06
        if dirty_price:
            price = random.choice([-round(random.uniform(5, 200), 2), None, 0])
        else:
            price = round(random.uniform(5, 500), 2)

        dirty_date = random.random() < 0.05
        sale_date = _random_bad_date() if dirty_date else fake.date_between(start_date="-1y", end_date="today").isoformat()

        # Un pequeño porcentaje de ventas referencia clientes inexistentes (huérfanas).
        customer_id = random.randint(1, num_customers + 20)

        sales.append(
            {
                "transaction_id": i,
                "customer_id": customer_id,
                "product": fake.word().capitalize() + " " + random.choice(["Pro", "Lite", "Plus", "Max", ""]),
                "quantity": random.choice([1, 1, 1, 2, 3, 5, -1]),  # -1 es un dato sucio
                "price": price,
                "sale_date": sale_date,
            }
        )

    # Introducir duplicados exactos (mismo transaction_id) para probar el check 'unique'.
    duplicates = random.sample(sales, k=max(1, n // 100))
    sales.extend(duplicates)
    random.shuffle(sales)
    return sales


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generado: {path} ({len(rows)} filas)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera datos de prueba (sucios) para el pipeline de ventas.")
    parser.add_argument("--customers", type=int, default=200)
    parser.add_argument("--sales", type=int, default=1000)
    args = parser.parse_args()

    customers = generate_customers(args.customers)
    sales = generate_sales(args.sales, args.customers)

    write_csv(customers, OUT_DIR / "customers.csv")
    write_csv(sales, OUT_DIR / "sales.csv")


if __name__ == "__main__":
    main()
