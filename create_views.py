import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def create_analytics_view():
    view_sql = """
    CREATE OR REPLACE VIEW view_crypto_rolling_metrics AS
    WITH latest_batch AS (
        -- Identify the most recent batch execution timestamp
        SELECT MAX(recorded_at) AS max_snapshot_time 
        FROM crypto_price_history
    ),
    ranked_snapshots AS (
        SELECT 
            coin_id,
            symbol,
            price,
            market_cap,
            total_volume,
            recorded_at,
            -- Rolling average price over the last 24 records per coin
            AVG(price) OVER (
                PARTITION BY coin_id 
                ORDER BY recorded_at 
                ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
            ) AS rolling_avg_price,
            
            -- Standard deviation over the last 24 records (volatility proxy)
            STDDEV(price) OVER (
                PARTITION BY coin_id 
                ORDER BY recorded_at 
                ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
            ) AS rolling_price_volatility,

            -- Liquidity proxy: volume to market cap ratio
            CASE 
                WHEN market_cap > 0 THEN ROUND((total_volume / market_cap)::numeric, 6)
                ELSE 0 
            END AS volume_to_mcap_ratio,

            -- Row ranking to grab latest state easily
            ROW_NUMBER() OVER (
                PARTITION BY coin_id 
                ORDER BY recorded_at DESC
            ) AS recency_rank
        FROM crypto_price_history
    )
    SELECT 
        r.coin_id,
        r.symbol,
        r.price AS latest_price,
        ROUND(r.rolling_avg_price::numeric, 4) AS rolling_avg_price,
        ROUND(COALESCE(r.rolling_price_volatility, 0)::numeric, 4) AS rolling_volatility,
        r.volume_to_mcap_ratio,
        r.recorded_at AS last_snapshot_time
    FROM ranked_snapshots r
    JOIN latest_batch b 
      ON r.recorded_at = b.max_snapshot_time
    WHERE r.recency_rank = 1;
    """

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "6543"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        sslmode="require" if os.getenv("DB_HOST") and "supabase.com" in os.getenv("DB_HOST") else "prefer"
    )

    with conn:
        with conn.cursor() as cur:
            cur.execute(view_sql)
    conn.close()
    print("Analytical view `view_crypto_rolling_metrics` created successfully.")

if __name__ == "__main__":
    create_analytics_view()