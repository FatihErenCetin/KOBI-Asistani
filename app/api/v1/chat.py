from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import panel_agent
from app.core.config import settings
from app.integrations.gmail_client import send_email
from app.api.deps import get_db, require_admin
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/panel", tags=["panel"], dependencies=[Depends(require_admin)])


@router.post("/chat", response_model=ChatResponse)
async def panel_chat(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    resp = await panel_agent.handle(payload.message, db=db, history=payload.history)
    return ChatResponse(text=resp.text, data=resp.data)


class SupplierMailRequest(BaseModel):
    subject: str
    body: str


@router.post("/supplier-mail")
async def send_supplier_mail(payload: SupplierMailRequest):
    """Panelde hazirlanan tedarikci mailini onaydan sonra Gmail ile gonderir."""
    supplier_email = (settings.SUPPLIER_EMAIL or "").strip()
    if not supplier_email:
        raise HTTPException(
            status_code=400,
            detail="SUPPLIER_EMAIL .env icinde tanimli degil.",
        )

    subject = payload.subject.strip() or "Tedarik Talebi"
    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=400, detail="Mail govdesi bos olamaz.")

    try:
        result = send_email(to=supplier_email, subject=subject, body=body)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Mail gonderilemedi: {exc}") from exc

    return {
        "ok": True,
        "to": supplier_email,
        "subject": subject,
        "message_id": result.get("id"),
    }
