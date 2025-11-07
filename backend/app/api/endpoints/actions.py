"""
Actions API endpoints
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.action import Action
from app.schemas.action import ActionResponse, ActionListResponse

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("", response_model=ActionListResponse)
async def list_actions(
    category: Optional[str] = Query(None, description="Filter by category/domain"),
    search: Optional[str] = Query(None, description="Search in action_name or description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all actions with optional filtering"""

    # Build query
    query = select(Action).where(Action.is_active == True)

    # Apply filters
    if category:
        query = query.where(Action.category == category)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Action.action_name.ilike(search_pattern)) |
            (Action.description.ilike(search_pattern))
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    actions = result.scalars().all()

    return ActionListResponse(
        actions=[ActionResponse.model_validate(action) for action in actions],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{action_id}", response_model=ActionResponse)
async def get_action(
    action_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a single action by ID"""

    query = select(Action).where(Action.id == action_id)
    result = await db.execute(query)
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    return ActionResponse.model_validate(action)
