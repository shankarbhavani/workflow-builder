"""
Executions API endpoints
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.execution import Execution, ExecutionLog
from app.schemas.execution import (
    ExecutionResponse,
    ExecutionListItemResponse,
    ExecutionListResponse,
    ExecutionCancelResponse
)
from app.services.temporal_service import TemporalService

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("", response_model=ExecutionListResponse)
async def list_executions(
    workflow_id: Optional[UUID] = Query(None, description="Filter by workflow ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all executions with optional filtering"""

    # Build query
    query = select(Execution).order_by(Execution.started_at.desc())

    # Apply filters
    if workflow_id:
        query = query.where(Execution.workflow_id == workflow_id)

    if status:
        query = query.where(Execution.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query (without logs for list view)
    result = await db.execute(query)
    executions = result.scalars().all()

    return ExecutionListResponse(
        executions=[
            ExecutionListItemResponse.model_validate(execution)
            for execution in executions
        ],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a single execution with logs"""

    # Query with logs eagerly loaded
    query = (
        select(Execution)
        .where(Execution.id == execution_id)
        .options(selectinload(Execution.logs))
    )

    result = await db.execute(query)
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return ExecutionResponse.model_validate(execution)


@router.post("/{execution_id}/cancel", response_model=ExecutionCancelResponse)
async def cancel_execution(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Cancel a running execution"""

    # Get execution
    query = select(Execution).where(Execution.id == execution_id)
    result = await db.execute(query)
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    if execution.status != "RUNNING":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel execution with status {execution.status}"
        )

    # Cancel workflow on Temporal
    temporal_service = TemporalService()
    try:
        await temporal_service.cancel_workflow(execution_id, db)

        return ExecutionCancelResponse(
            execution_id=execution_id,
            status="CANCELLED"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel execution: {str(e)}")
