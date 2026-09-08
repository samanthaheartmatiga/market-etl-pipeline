import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

user = os.getenv("DB_USER", "postgres")
password = os.getenv("DB_PASSWORD", "etl_password")
host = os.getenv("DB_HOST", "localhost")
port = os.getenv("DB_PORT", "5432")
database = os.getenv("DB_NAME", "market_data")

engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{database}")

# Query latest 10 historical entries
query = """
SELECT 
    symbol,
    price,
    recorded_at,
    ingested_at
FROM crypto_price_history
ORDER BY recorded_at DESC, price DESC
LIMIT 10;
"""

df = pd.read_sql(query, engine)

print("\n--- RECENT ENTRIES IN crypto_price_history ---")
print(df.to_string(index=False))

# Count snapshots per coin
summary_query = """
SELECT 
    symbol, 
    COUNT(*) as snapshot_count,
    MIN(recorded_at) as earliest_snapshot,
    MAX(recorded_at) as latest_snapshot
FROM crypto_price_history
GROUP BY symbol
ORDER BY snapshot_count DESC, symbol ASC
LIMIT 5;
"""

df_summary = pd.read_sql(summary_query, engine)
print("\n--- SNAPSHOT COUNTS BY SYMBOL ---")
print(df_summary.to_string(index=False))