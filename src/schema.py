from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class CryptoMarketRecord(BaseModel):
    id: str
    symbol: str
    name: str
    current_price: float = Field(gt=0, description="Price must be positive")
    market_cap: Optional[float] = 0.0
    total_volume: Optional[float] = 0.0
    price_change_percentage_24h: Optional[float] = None
    last_updated: datetime