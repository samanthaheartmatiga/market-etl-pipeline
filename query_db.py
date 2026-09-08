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

query = """
SELECT 
    symbol, 
    name, 
    current_price, 
    price_change_percentage_24h, 
    ingested_at 
FROM crypto_markets 
ORDER BY current_price DESC 
LIMIT 10;
"""

df = pd.read_sql(query, engine)

print("\n--- TOP 10 COINS IN DATABASE BY PRICE ---")
print(df.to_string(index=False))