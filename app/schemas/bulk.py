from pydantic import BaseModel, Field


class CsvImportResult(BaseModel):
    total_rows: int
    created: int
    updated: int
    skipped: list[dict] = Field(default_factory=list)


class BulkPriceUpdate(BaseModel):
    product_ids: list[int] | None = None  # None = filtre ile
    category: str | None = None
    name_pattern: str | None = None  # ILIKE pattern
    operation: str  # "percent_increase" | "percent_decrease" | "set_absolute"
    value: float
    target: str = "price"  # "price" | "cost"
    reason: str
