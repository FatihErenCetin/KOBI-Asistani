from datetime import datetime

from pydantic import BaseModel


class CustomerOut(BaseModel):
    id: int
    name: str
    phone: str | None
    telegram_user_id: int | None
    created_at: datetime
