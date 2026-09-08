import logging
import psycopg2
from typing import List, Tuple
from .schema import CryptoMarketRecord
from .load import get_db_connection

def check_record_completeness(records: List[CryptoMarketRecord], min_expected: int = 20) -> List[str]:
    """Ensures minimum batch size and valid prices across all records."""
    issues = []
    
    if len(records) < min_expected:
        issues.append(f"Low record count: Received {len(records)} records, expected >= {min_expected}")

    for r in records:
        if r.current_price is None or r.current_price <= 0:
            issues.append(f"Invalid price detected for {r.symbol}: {r.current_price}")
            
    return issues

def check_price_volatility_threshold(records: List[CryptoMarketRecord], threshold_pct: float = 10.0) -> List[str]:
    """Compares incoming prices with the most recent price in the database."""
    anomalies = []
    
    query = """
    SELECT symbol, current_price 
    FROM crypto_markets;
    """
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            
    if not rows:
        return anomalies  # First run has no baseline

    previous_prices = {row[0]: float(row[1]) for row in rows}

    for record in records:
        sym = record.symbol.upper()
        if sym in previous_prices:
            prev_price = previous_prices[sym]
            if prev_price <= 0:
                continue
            
            delta_pct = ((record.current_price - prev_price) / prev_price) * 100.0
            
            if abs(delta_pct) >= threshold_pct:
                direction = "surged" if delta_pct > 0 else "dropped"
                anomalies.append(
                    f"{sym} {direction} {abs(delta_pct):.2f}% (from ${prev_price:,.2f} to ${record.current_price:,.2f})"
                )

    return anomalies

def run_data_quality_checks(records: List[CryptoMarketRecord]) -> Tuple[bool, List[str]]:
    """Runs all assertions and returns (is_healthy, list_of_warnings)."""
    warnings = []
    warnings.extend(check_record_completeness(records))
    warnings.extend(check_price_volatility_threshold(records))
    
    is_healthy = len(warnings) == 0
    return is_healthy, warnings