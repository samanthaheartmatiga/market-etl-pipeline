# ⚡ Automated Crypto Market Telemetry & ETL Pipeline

[![Scheduled Crypto ETL Pipeline](https://github.com/samanthaheartmatiga/market-etl-pipeline/actions/workflows/etl.yml/badge.svg)](https://github.com/samanthaheartmatiga/market-etl-pipeline/actions/workflows/etl.yml)
![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/Database-Supabase%20Postgres-3ECF8E?logo=supabase&logoColor=white)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit%20Cloud-FF4B4B?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue.svg)

An end-to-end automated cryptocurrency ingestion engine and analytical telemetry dashboard. The system extracts top-market crypto data on a 10-minute cadence, runs schema and drift validation assertions, loads records idempotently into a cloud PostgreSQL data warehouse, computes rolling window analytics in SQL, and serves an interactive dashboard.

🔗 **Live Production Dashboard:** [crypto-telemetry-pipeline.streamlit.app](https://crypto-telemetry-pipeline.streamlit.app)
---

## 🏗 System Architecture

```text
               ┌───────────────────────┐
               │    CoinGecko API      │
               └───────────┬───────────┘
                           │ HTTP (REST)
                           ▼
               ┌───────────────────────┐
               │ GitHub Actions Runner │
               │   (Cron: */10 mins)   │
               └───────────┬───────────┘
                           │
       ┌───────────────────┴───────────────────┐
       ▼                                       ▼
┌──────────────┐                       ┌──────────────┐
│ Schema Check │                       │ Drift Guard  │
│  (Pydantic)  │                       │  (< 50% Δ)   │
└──────┬───────┘                       └──────┬───────┘
       └───────────────────┬───────────────────┘
                           │ Pooled SSL (psycopg2)
                           ▼
               ┌───────────────────────┐
               │  Supabase PostgreSQL  │
               ├───────────────────────┤
               │ • crypto_markets      │
               │ • crypto_price_history│
               │ • view_rolling_metrics│
               └───────────┬───────────┘
                           │ Query (SQLAlchemy)
                           ▼
               ┌───────────────────────┐
               │    Streamlit Cloud    │
               │  (Telemetry & Export) │
               └───────────────────────┘

```

---

## 🚀 Key Features

* **Continuous Automated Ingestion:** GitHub Actions orchestrator runs ingestion headlessly every 10 minutes on an automated cron schedule.
* **Idempotent Data Ingestion:** Database snapshot insertion implements `ON CONFLICT (symbol, recorded_at) DO NOTHING` to prevent primary key collisions when CoinGecko timestamps remain static.
* **Circuit Breakers & Data Quality:** Pydantic models validate incoming payloads; anomaly assertion rules stop execution if price drifts exceed 50% within a single window.
* **Database Window Aggregations:** SQL view (`view_crypto_rolling_metrics`) calculates 24-run moving averages, price volatility ($\sigma$), and volume-to-market-cap ratios directly in the warehouse.
* **Custom Production UI:** Built with a specialized dark theme (`#241C40` canvas, `#CDF27E` accents), real-time asset telemetry cards, Plotly historical charts, and native OpenPyXL formatted Excel reporting.

---

## 📂 Project Structure

```text
market-etl-pipeline/
├── .github/
│   └── workflows/
│       └── etl.yml            # Automated GitHub Actions cron runner
├── src/
│   ├── __init__.py
│   ├── alerts.py              # Fallback alerting utilities
│   ├── extract.py             # CoinGecko REST ingestion client
│   ├── load.py                # Supabase idempotent upsert logic
│   ├── main.py                # Pipeline execution controller
│   ├── quality.py             # Data quality & circuit breaker assertions
│   └── schema.py              # Pydantic data contract definitions
├── app.py                     # Streamlit telemetry dashboard & Excel exporter
├── create_views.py            # SQL analytical view migrations
├── requirements.txt           # Production dependencies
└── README.md

```

---

## 📊 Analytical View Definition

The pipeline aggregates data inside PostgreSQL using analytical window functions:

```sql
CREATE OR REPLACE VIEW view_crypto_rolling_metrics AS
WITH ranked_snapshots AS (
    SELECT 
        coin_id,
        symbol,
        price,
        total_volume,
        market_cap,
        recorded_at,
        ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY recorded_at DESC) as rn,
        AVG(price) OVER (
            PARTITION BY symbol 
            ORDER BY recorded_at DESC 
            ROWS BETWEEN CURRENT ROW AND 23 FOLLOWING
        ) as rolling_avg_price,
        STDDEV(price) OVER (
            PARTITION BY symbol 
            ORDER BY recorded_at DESC 
            ROWS BETWEEN CURRENT ROW AND 23 FOLLOWING
        ) as rolling_volatility
    FROM crypto_price_history
)
SELECT 
    coin_id,
    symbol,
    price AS latest_price,
    ROUND(rolling_avg_price, 4) AS rolling_avg_price,
    COALESCE(ROUND(rolling_volatility, 4), 0.0000) AS rolling_volatility,
    ROUND((total_volume / NULLIF(market_cap, 0)), 6) AS volume_to_mcap_ratio,
    recorded_at AS last_snapshot_time
FROM ranked_snapshots
WHERE rn = 1;

```

---

## ⚙️ Local Setup & Development

### 1. Clone the Repository

```bash
git clone [https://github.com/samanthaheartmatiga/market-etl-pipeline.git]
cd market-etl-pipeline

```

### 2. Configure Environment

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

```

Install project dependencies:

```powershell
pip install -r requirements.txt

```

### 3. Set Up Environment Variables

Create a `.env` file in the project root:

```env
DB_HOST=aws-0-ap-northeast-1.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.<your-supabase-project-id>
DB_PASSWORD=<your-supabase-password>

```

### 4. Run Locally

Execute an immediate ingestion cycle:

```powershell
python -m src.main

```

Launch the telemetry UI:

```powershell
streamlit run app.py

```

---

## 🔒 Security Configuration

Production secrets are handled using zero-trust configuration:

* **GitHub Actions:** Stored in **Settings $\rightarrow$ Secrets and variables $\rightarrow$ Actions** to power cloud executions.
* **Streamlit Cloud:** Configured via encrypted TOML within **Manage app $\rightarrow$ Settings $\rightarrow$ Secrets**.
* Local `.env` credentials and execution logs (`*.log`) are ignored via `.gitignore`.

```

```