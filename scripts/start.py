"""Initialize an empty Render database, then start the web application."""
from __future__ import annotations

import os
import subprocess

import psycopg

from scripts.pipeline import clean, generate, load


def ensure_seeded() -> None:
    url = os.environ["DATABASE_URL"]
    with psycopg.connect(url) as conn:
        exists = conn.execute("SELECT to_regclass('public.payments')").fetchone()[0]
        count = conn.execute("SELECT count(*) FROM payments").fetchone()[0] if exists else 0
    if count:
        return

    raw, customers = generate()
    cleaned, _, summary = clean(raw, {customer[0] for customer in customers})
    load(cleaned, customers, summary)


if __name__ == "__main__":
    ensure_seeded()
    port = os.environ.get("PORT", "10000")
    subprocess.run(
        ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", port],
        check=True,
    )
