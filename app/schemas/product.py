from pydantic import BaseModel


class ProductOut(BaseModel):
    id: int
    name: str
    aliases: str | None
    unit: str
    price: float
    stock: float
    low_stock_threshold: float
    description: str | None
    is_low: bool


class StockUpdate(BaseModel):
    stock: float
