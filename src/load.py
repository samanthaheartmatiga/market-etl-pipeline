import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

from .schema import CryptoMarketRecord

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "etl_password")
    )

def init_db():
    queries = [
        # Current state table (upsert target)
        """
        CREATE TABLE IF NOT EXISTS crypto_markets (
            coin_id VARCHAR(50) PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            name VARCHAR(100) NOT NULL,
            current_price NUMERIC(18, 8) NOT NULL,
            market_cap NUMERIC(24, 2),
            total_volume NUMERIC(24, 2),
            price_change_percentage_24h NUMERIC(8, 4),
            last_updated TIMESTAMPTZ NOT NULL,
            ingested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
        """,
        # Historical append-only table (time-series target)
        """
        CREATE TABLE IF NOT EXISTS crypto_price_history (
            id BIGSERIAL PRIMARY KEY,
            coin_id VARCHAR(50) NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            price NUMERIC(18, 8) NOT NULL,
            market_cap NUMERIC(24, 2),
            total_volume NUMERIC(24, 2),
            recorded_at TIMESTAMPTZ NOT NULL,
            ingested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_coin_snapshot UNIQUE (symbol, recorded_at)
        );
        """,
        # Index on historical table for fast time-series filtering
        """
        CREATE INDEX IF NOT EXISTS idx_history_coin_recorded 
        ON crypto_price_history (coin_id, recorded_at DESC);
        """
    ]
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for q in queries:
                cur.execute(q)
        conn.commit()

def upsert_records(records: list[CryptoMarketRecord]) -> int:
    if not records:
        return 0

    # 1. Upsert into current state table
    upsert_query = """
    INSERT INTO crypto_markets (
        coin_id, symbol, name, current_price, market_cap, 
        total_volume, price_change_percentage_24h, last_updated
    ) VALUES %s
    ON CONFLICT (coin_id) DO UPDATE SET
        current_price = EXCLUDED.current_price,
        market_cap = EXCLUDED.market_cap,
        total_volume = EXCLUDED.total_volume,
        price_change_percentage_24h = EXCLUDED.price_change_percentage_24h,
        last_updated = EXCLUDED.last_updated,
        ingested_at = CURRENT_TIMESTAMP;
    """

    upsert_data = [
        (
            r.id,
            r.symbol.upper(),
            r.name,
            r.current_price,
            r.market_cap,
            r.total_volume,
            r.price_change_percentage_24h,
            r.last_updated
        )
        for r in records
    ]

    # 2. Append into history table (ignoring exact snapshot duplicates)
    history_query = """
    INSERT INTO crypto_price_history (
        coin_id, symbol, price, market_cap, total_volume, recorded_at
    ) VALUES %s
    ON CONFLICT (symbol, recorded_at) DO NOTHING;
    """

    history_data = [
        (
            r.id,
            r.symbol.upper(),
            r.current_price,
            r.market_cap,
            r.total_volume,
            r.last_updated
        )
        for r in records
    ]

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            execute_values(cur, upsert_query, upsert_data)
            execute_values(cur, history_query, history_data)
        conn.commit()

    return len(records)