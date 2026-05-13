"""M14: Morning briefing — text generator."""

import pytest

from app.db.crud import products as products_crud
from app.db.models import StockMovementReason
from app.services.morning_briefing import build_briefing_text


@pytest.mark.asyncio
async def test_briefing_empty_state(db):
    """Hicbir veri yokken bile patlamamali."""
    text = await build_briefing_text(db)
    assert "Günaydın" in text
    assert "çalışmalar" in text


@pytest.mark.asyncio
async def test_briefing_has_revenue_line(db):
    text = await build_briefing_text(db)
    assert "Son 24 saat" in text
    assert "ciro" in text
