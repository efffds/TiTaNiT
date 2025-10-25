# backend/app/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from ..db import get_async_session
from ..security import get_current_user_id
from ..models import Conversation, Message, Match
from ..schemas import (
    ChatOpenRequest, ChatOpenResponse,
    ConversationsListResponse, ConversationOut,
    MessageIn, MessageOut,
)

router = APIRouter(prefix="/chat", tags=["chat"])

@router.get("/conversations", response_model=ConversationsListResponse)
async def list_conversations(current_user_id: int = Depends(get_current_user_id),
                             db: AsyncSession = Depends(get_async_session)):
    res = await db.execute(
        select(Conversation).where(or_(Conversation.user1_id == current_user_id,
                                       Conversation.user2_id == current_user_id))
    )
    items = [ConversationOut.model_validate(c) for c in res.scalars().all()]
    return ConversationsListResponse(items=items)

@router.post("/open", response_model=ChatOpenResponse)
async def open_chat(payload: ChatOpenRequest,
                    current_user_id: int = Depends(get_current_user_id),
                    db: AsyncSession = Depends(get_async_session)):
    target_id = payload.target_user_id
    if target_id == current_user_id:
        raise HTTPException(status_code=400, detail="Нельзя открыть чат с собой")

    u1 = min(current_user_id, target_id)
    u2 = max(current_user_id, target_id)

    # Проверяем, что есть матч между пользователями
    match_res = await db.execute(select(Match).where(and_(Match.user1_id == u1, Match.user2_id == u2)))
    if match_res.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="Чат доступен только при взаимном лайке")

    # Ищем существующий разговор или создаём новый
    conv_res = await db.execute(select(Conversation).where(and_(Conversation.user1_id == u1,
                                                                Conversation.user2_id == u2)))
    conv = conv_res.scalar_one_or_none()
    if conv is None:
        conv = Conversation(user1_id=u1, user2_id=u2)
        db.add(conv)
        await db.commit()
        await db.refresh(conv)

    # Дополнительно проверим, что текущий пользователь участник беседы
    if current_user_id not in (conv.user1_id, conv.user2_id):
        raise HTTPException(status_code=403, detail="Нет доступа к чату")

    return ChatOpenResponse(conversation_id=conv.id)

async def _ensure_participant(db: AsyncSession, conversation_id: int, user_id: int) -> Conversation:
    conv_res = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = conv_res.scalar_one_or_none()
    if conv is None:
        raise HTTPException(status_code=404, detail="Чат не найден")
    if user_id not in (conv.user1_id, conv.user2_id):
        raise HTTPException(status_code=403, detail="Нет доступа к чату")
    return conv

@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def list_messages(conversation_id: int,
                        current_user_id: int = Depends(get_current_user_id),
                        db: AsyncSession = Depends(get_async_session)):
    await _ensure_participant(db, conversation_id, current_user_id)
    res = await db.execute(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()))
    return [MessageOut.model_validate(m) for m in res.scalars().all()]

@router.post("/{conversation_id}/messages", response_model=MessageOut)
async def send_message(conversation_id: int, payload: MessageIn,
                       current_user_id: int = Depends(get_current_user_id),
                       db: AsyncSession = Depends(get_async_session)):
    await _ensure_participant(db, conversation_id, current_user_id)
    if not payload.body or not payload.body.strip():
        raise HTTPException(status_code=422, detail="Текст сообщения пуст")
    msg = Message(conversation_id=conversation_id, sender_id=current_user_id, body=payload.body.strip())
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return MessageOut.model_validate(msg)
@router.delete("/{conversation_id}/messages/{message_id}", response_model=MessageOut)
async def delete_message(conversation_id: int, message_id: int, current_user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_async_session)):
    msg = await db.execute(select(Message).where(Message.id == message_id, Message.conversation_id == conversation_id))
    msg = msg.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if msg.sender_id != current_user_id:
        raise HTTPException(status_code=403, detail="You can't delete this message")
    await db.delete(msg)
    await db.commit()
    return MessageOut.model_validate(msg)
