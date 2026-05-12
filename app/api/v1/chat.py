from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import panel_agent
from app.api.deps import get_db, require_admin
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/panel", tags=["panel"], dependencies=[Depends(require_admin)])


@router.post("/chat", response_model=ChatResponse)
async def panel_chat(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    resp = await panel_agent.handle(payload.message, db=db, history=payload.history)
    return ChatResponse(text=resp.text, data=resp.data)
