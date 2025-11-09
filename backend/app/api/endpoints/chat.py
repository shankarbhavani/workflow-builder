"""
Chat API endpoints for natural language workflow generation
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.conversation import ConversationSession
from app.models.action import Action
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    ConversationSessionResponse,
    ConversationListResponse
)
from app.services.workflow_agent import WorkflowAgent
from app.services.action_service_client import action_service_client

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Send a chat message for workflow generation

    If session_id is provided, continue existing conversation.
    Otherwise, create a new conversation session.
    """

    # Get or create conversation session
    if chat_request.session_id:
        # Load existing session
        query = select(ConversationSession).where(ConversationSession.id == chat_request.session_id)
        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Conversation session not found")
    else:
        # Create new session
        session = ConversationSession(
            messages=[],
            workflow_draft={},
            status="active"
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

    # Load action catalog
    actions_query = select(Action)
    actions_result = await db.execute(actions_query)
    actions = actions_result.scalars().all()

    action_catalog = [
        {
            "name": action.action_name,
            "description": action.description,
            "parameters": action.parameters
        }
        for action in actions
    ]

    # Process message with workflow agent
    agent = WorkflowAgent()

    conversation_state = {
        "messages": session.messages or [],
        "workflow_draft": session.workflow_draft or {}
    }

    try:
        updated_state = await agent.process_message(
            message=chat_request.message,
            conversation_state=conversation_state,
            action_catalog=action_catalog
        )

        # Update session
        session.messages = updated_state["messages"]
        session.workflow_draft = updated_state.get("workflow_draft", {})

        # Enrich workflow nodes with action metadata from external catalog
        if session.workflow_draft and session.workflow_draft.get("nodes"):
            # Fetch action lookup from external catalog
            action_lookup = await action_service_client.build_action_lookup()

            # Enrich each node with action_id, domain, and display_name
            for node in session.workflow_draft["nodes"]:
                if "data" in node and "action_name" in node["data"]:
                    action_name = node["data"]["action_name"]
                    matching_action = action_lookup.get(action_name)

                    if matching_action:
                        # Add action metadata to node data
                        node["data"]["action_id"] = str(matching_action["id"]) if matching_action.get("id") else None
                        node["data"]["domain"] = matching_action.get("domain")
                        node["data"]["label"] = matching_action.get("display_name") or node["data"].get("label", action_name)
                    else:
                        # Log warning if action not found in external catalog
                        print(f"Warning: Action '{action_name}' not found in external catalog")

        await db.commit()
        await db.refresh(session)

        # Convert messages to ChatMessage schema
        message_objects = [
            ChatMessage(
                role=msg.get("role", "user"),
                content=msg.get("content", ""),
                timestamp=msg.get("timestamp")
            )
            for msg in session.messages
        ]

        return ChatResponse(
            session_id=session.id,
            response=updated_state.get("response", ""),
            workflow_draft=session.workflow_draft,
            messages=message_objects
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.get("/sessions", response_model=ConversationListResponse)
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all conversation sessions"""

    # Build query for active sessions
    query = select(ConversationSession).where(
        ConversationSession.status == "active"
    ).order_by(ConversationSession.updated_at.desc())

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    sessions = result.scalars().all()

    return ConversationListResponse(
        sessions=[ConversationSessionResponse.model_validate(session) for session in sessions],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/sessions/{session_id}", response_model=ConversationSessionResponse)
async def get_conversation(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a single conversation session"""

    query = select(ConversationSession).where(ConversationSession.id == session_id)
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Conversation session not found")

    return ConversationSessionResponse.model_validate(session)


@router.delete("/sessions/{session_id}")
async def delete_conversation(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a conversation session"""

    query = select(ConversationSession).where(ConversationSession.id == session_id)
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Conversation session not found")

    session.status = "abandoned"
    await db.commit()

    return {"message": "Conversation session deleted successfully"}
