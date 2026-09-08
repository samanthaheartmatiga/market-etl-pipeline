import logging

from .extract import fetch_top_crypto_markets
from .schema import CryptoMarketRecord
from .load import init_db, upsert_records
from .alerts import send_alert
from .quality import run_data_quality_checks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def run_pipeline():
    logging.info("Starting crypto market ETL run...")
    try:
        # 0. Ensure table exists
        init_db()

        # 1. Extract
        logging.info("Extracting data from CoinGecko API...")
        raw_data = fetch_top_crypto_markets(limit=25)

        # 2. Transform & Validate
        logging.info("Validating and parsing raw records...")
        valid_records = []
        skipped_count = 0

        for item in raw_data:
            try:
                record = CryptoMarketRecord(**item)
                valid_records.append(record)
            except Exception as validation_err:
                logging.warning(f"Validation failed for coin {item.get('id')}: {validation_err}")
                skipped_count += 1

        # 3. Data Quality Assertions
        logging.info("Running automated data quality checks...")
        is_healthy, issues = run_data_quality_checks(valid_records)

        if not is_healthy:
            for issue in issues:
                logging.warning(f"[DATA QUALITY WARNING] {issue}")
            # Alert on quality anomalies while continuing execution
            send_alert("DATA QUALITY WARNING", "\n".join(issues))
        else:
            logging.info("All data quality assertions passed.")

        # 4. Load
        logging.info("Loading records into PostgreSQL...")
        rows_written = upsert_records(valid_records)

        summary_msg = f"Successfully processed {rows_written} coins. (Skipped: {skipped_count})"
        logging.info(summary_msg)
        send_alert("SUCCESS", summary_msg)

    except Exception as err:
        error_msg = f"Pipeline failed unexpectedly: {err}"
        logging.error(error_msg)
        send_alert("CRITICAL FAILURE", error_msg)
        raise

if __name__ == "__main__":
    run_pipeline()