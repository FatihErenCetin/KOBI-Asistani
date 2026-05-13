import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import coordinator
from app.api.deps import get_db
from app.core import identity, stt
from app.core.config import settings
from app.db.session import SessionLocal
from app.integrations.telegram_client import telegram_client
from app.schemas.telegram import TelegramUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


def _format_tr_amount(amount: float) -> str:
    formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} TL"


@router.post("/webhooks/telegram")
async def telegram_inbound(
    update: TelegramUpdate,
    bg: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid secret")

    if update.callback_query:
        bg.add_task(
            _process_callback,
            update.callback_query.model_dump(by_alias=True),
        )
        return {"ok": True}

    msg = update.message
    if not msg or not msg.from_user:
        return {"ok": True}

    tg_user_id = msg.from_user.id

    if msg.contact:
        bg.add_task(
            _process_contact,
            tg_user_id,
            msg.contact.phone_number,
            msg.from_user.first_name or "Musteri",
        )
        return {"ok": True}

    if msg.voice:
        transcriber = stt.get_transcriber()
        try:
            audio_url = await telegram_client.get_file_url(msg.voice.file_id)
            text = await transcriber.transcribe(audio_url, lang="tr")
            logger.info("STT transkripti: %s", text[:120])
        except stt.STTDisabledError:
            await telegram_client.send_message(
                tg_user_id,
                "Sesli mesaj desteği yakında geliyor. Yazılı olarak iletebilir misiniz?",
            )
            return {"ok": True}
        except stt.STTFailedError as e:
            logger.warning("STT failed: %s", e)
            await telegram_client.send_message(
                tg_user_id,
                "Sesli mesajı çözemedim, yazılı olarak iletebilir misiniz?",
            )
            return {"ok": True}
    else:
        text = msg.text or ""

    if not text.strip():
        return {"ok": True}

    bg.add_task(_process_text, tg_user_id, text)
    return {"ok": True}


async def _process_contact(tg_user_id: int, phone: str, first_name: str):
    async with SessionLocal() as db:
        customer = await identity.link_telegram_to_phone(
            db, tg_user_id, phone, fallback_name=first_name
        )
    try:
        await telegram_client.send_message(
            tg_user_id,
            f"Tesekkurler {customer.name}, hesabinizi esledim. "
            "Size nasil yardimci olabilirim?",
        )
    except Exception:
        logger.exception("send_message failed in _process_contact")


async def _check_complaint_risk(tg_user_id: int, customer_id: int | None, text: str):
    """Fire-and-forget: regex tarsa LLM'ye sor, 0.7+ ise complaint kaydet."""
    from app.db.crud import complaints as complaints_crud
    from app.services import risk_classifier

    try:
        score, signals = await risk_classifier.classify_risk(text)
        if score >= 0.7:
            async with SessionLocal() as db:
                await complaints_crud.create(
                    db,
                    customer_id=customer_id,
                    telegram_user_id=tg_user_id,
                    message_text=text,
                    risk_score=score,
                    signals=signals,
                )
                await db.commit()
                logger.info(
                    "Complaint logged: tg=%s score=%.2f signals=%s",
                    tg_user_id, score, signals,
                )
    except Exception:
        logger.exception("complaint risk check failed")


async def _process_text(tg_user_id: int, text: str):
    import asyncio

    async with SessionLocal() as db:
        customer = await identity.resolve_by_telegram(db, tg_user_id)
        # Paralel: sikayet riski tara (fire-and-forget)
        asyncio.create_task(
            _check_complaint_risk(
                tg_user_id, customer.id if customer else None, text
            )
        )
        if customer is None:
            try:
                await telegram_client.send_message(
                    tg_user_id,
                    "Merhaba! Sizi tanimak icin telefon numaranizi paylasir misiniz?",
                    reply_markup={
                        "keyboard": [
                            [{"text": "Numaramı paylaş", "request_contact": True}]
                        ],
                        "one_time_keyboard": True,
                        "resize_keyboard": True,
                    },
                )
            except Exception:
                logger.exception("send onboarding failed")
            return
        try:
            await telegram_client.send_chat_action(tg_user_id, "typing")
        except Exception:
            logger.debug("send_chat_action failed", exc_info=True)
        try:
            resp = await coordinator.handle_telegram_message(
                customer=customer,
                text=text,
                telegram_user_id=tg_user_id,
                db=db,
            )
        except Exception:
            logger.exception("Agent error")
            try:
                await telegram_client.send_message(
                    tg_user_id, "Uzgunum, bir hata olustu. Tekrar dener misiniz?"
                )
            except Exception:
                logger.exception("send error fallback failed")
            return

    try:
        if resp.draft_id and resp.draft_summary:
            markup = _draft_confirm_keyboard(resp.draft_id)
            await telegram_client.send_message(tg_user_id, resp.text, reply_markup=markup)
        else:
            await telegram_client.send_message(tg_user_id, resp.text)
    except Exception:
        logger.exception("send response failed")


async def _process_callback(callback_dict: dict):
    callback_id = callback_dict["id"]
    tg_user_id = callback_dict["from"]["id"]
    data = callback_dict.get("data", "")
    async with SessionLocal() as db:
        customer = await identity.resolve_by_telegram(db, tg_user_id)
        if customer is None:
            await telegram_client.answer_callback_query(
                callback_id, "Once hesabinizi esleyin."
            )
            return
        try:
            result = await coordinator.handle_telegram_callback(
                customer=customer,
                callback_data=data,
                telegram_user_id=tg_user_id,
                db=db,
            )
        except Exception:
            logger.exception("Callback error")
            await telegram_client.answer_callback_query(callback_id, "Hata olustu.")
            return

    try:
        await telegram_client.answer_callback_query(callback_id)
        if "order_id" in result:
            await telegram_client.send_message(
                tg_user_id,
                f"Siparisiniz alindi.\nSiparis no: #{result['order_id']}\n"
                f"Tutar: {_format_tr_amount(result['total'])}\n"
                "Durum: hazirlanmaya alindi.",
            )
        elif result.get("cancelled"):
            await telegram_client.send_message(tg_user_id, "Siparis iptal edildi.")
        elif "error" in result:
            await telegram_client.send_message(tg_user_id, result["error"])
    except Exception:
        logger.exception("callback response send failed")


def _draft_confirm_keyboard(draft_id: str) -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "Evet, ac", "callback_data": f"confirm:{draft_id}"},
                {"text": "Vazgec", "callback_data": "cancel"},
            ]
        ]
    }
