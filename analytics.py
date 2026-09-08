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

def run_metrics_summary():
    # 1. Fetch entire historical dataset
    query = """
    SELECT symbol, price, market_cap, total_volume, recorded_at
    FROM crypto_price_history
    ORDER BY recorded_at ASC;
    """
    df = pd.read_sql(query, engine)

    if df.empty:
        print("No historical data found.")
        return

    # 2. Pandas transformations: Rolling metrics & liquidity ratio
    df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    df["vol_to_mcap_pct"] = (df["total_volume"] / df["market_cap"]) * 100

    # Calculate rolling metrics per symbol
    df["rolling_mean"] = df.groupby("symbol")["price"].transform(lambda s: s.rolling(window=5, min_periods=1).mean())
    df["price_volatility"] = df.groupby("symbol")["price"].transform(lambda s: s.rolling(window=5, min_periods=1).std()).fillna(0)

    # 3. Pull latest snapshot per asset
    latest_metrics = df.sort_values("recorded_at").groupby("symbol").last().reset_index()

    display_cols = [
        "symbol", 
        "price", 
        "rolling_mean", 
        "price_volatility", 
        "vol_to_mcap_pct", 
        "recorded_at"
    ]
    summary_table = latest_metrics[display_cols].sort_values("price", ascending=False)

    print("\n--- LATEST ROLLING METRICS (PANDAS) ---")
    print(summary_table.to_string(index=False))

    # 4. Query PostgreSQL view directly
    print("\n--- VIEW QUERY: view_crypto_rolling_metrics ---")
    view_df = pd.read_sql("SELECT * FROM view_crypto_rolling_metrics ORDER BY latest_price DESC LIMIT 10;", engine)
    print(view_df.to_string(index=False))

if __name__ == "__main__":
    run_metrics_summary()