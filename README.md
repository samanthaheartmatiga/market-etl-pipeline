# ⚡ Real-Time Crypto Market Telemetry & ETL Pipeline

An end-to-end automated crypto ingestion pipeline and real-time analytical dashboard built with Python, Supabase PostgreSQL, GitHub Actions, and Streamlit.

🔗 **Live App:** [View Telemetry Dashboard](https://<YOUR-CUSTOM-URL>.streamlit.app)

---

## 🛠 Tech Stack & Architecture

* **Extraction:** CoinGecko Public API (Top market capitalization tokens).
* **Validation & Quality:** Pydantic schema validation with circuit breakers preventing drastic anomalous drifts (> 50% price delta tolerance).
* **Target Data Warehouse:** Supabase PostgreSQL with pooled connections, indexed time-series snapshots, and SQL window analytical views (`view_crypto_rolling_metrics`).
* **Automation & Orchestration:** GitHub Actions running on cron (`*/10 * * * *`) with idempotent inserts (`ON CONFLICT DO NOTHING`).
* **Visualization Layer:** Streamlit Community Cloud styled with a custom dark-mode design system, Plotly interactive telemetry, and OpenPyXL styled report exporter.

---

## ⚙ Pipeline Features

* **Zero-Downtime Cloud Ingestion:** Runs 24/7 in cloud compute without requiring local machines running.
* **Idempotent Ingestion:** Safe retry mechanics handling CoinGecko timestamp updates gracefully.
* **SQL Rolling Metrics:** Precomputes 24-period moving averages and price volatility ($\sigma$) via database window functions for fast dashboard reads.