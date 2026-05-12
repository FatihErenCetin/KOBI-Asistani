"""Gelen mesaji uygun ajana yonlendiren ince katman."""

from app.agents import customer_agent
from app.db.models import Customer


async def handle_telegram_message(
    *, customer: Customer, text: str, telegram_user_id: int, db
):
    return await customer_agent.handle_message(
        customer=customer,
        message=text,
        db=db,
        telegram_user_id=telegram_user_id,
    )


async def handle_telegram_callback(
    *, customer: Customer, callback_data: str, telegram_user_id: int, db
):
    if callback_data.startswith("confirm:"):
        draft_id = callback_data.split(":", 1)[1]
        return await customer_agent.handle_callback_confirm(
            customer=customer,
            draft_id=draft_id,
            db=db,
            telegram_user_id=telegram_user_id,
        )
    if callback_data == "cancel":
        return await customer_agent.handle_callback_cancel(
            customer=customer, db=db, telegram_user_id=telegram_user_id
        )
    return {"error": f"Bilinmeyen callback: {callback_data}"}
