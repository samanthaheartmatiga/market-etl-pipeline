import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"

class ExtractionError(Exception):
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=10),
    retry=retry_if_exception_type(ExtractionError),
    reraise=True
)
def fetch_top_crypto_markets(vs_currency: str = "usd", limit: int = 20) -> list[dict]:
    params = {
        "vs_currency": vs_currency,
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": False
    }

    response = requests.get(COINGECKO_URL, params=params, timeout=10)

    if response.status_code == 429:
        raise ExtractionError("Rate limited by CoinGecko API. Retrying...")

    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    data = fetch_top_crypto_markets(limit=5)
    print(f"Extracted {len(data)} coins successfully. Top coin: {data[0]['name']}")