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
from app.models.workflow import Workflow
from app.schemas.execution import (
    ExecutionResponse,
    ExecutionListItemResponse,
    ExecutionListResponse,
    ExecutionCancelResponse,
    ExecutionLogResponse
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

    # Build query with join to get workflow name
    query = (
        select(Execution, Workflow.name.label('workflow_name'))
        .join(Workflow, Execution.workflow_id == Workflow.id)
        .order_by(Execution.started_at.desc())
    )

    # Apply filters
    if workflow_id:
        query = query.where(Execution.workflow_id == workflow_id)

    if status:
        query = query.where(Execution.status == status)

    # Get total count
    count_query = select(func.count()).select_from(
        select(Execution)
        .join(Workflow, Execution.workflow_id == Workflow.id)
        .subquery()
    )
    if workflow_id:
        count_query = count_query.where(Execution.workflow_id == workflow_id)
    if status:
        count_query = count_query.where(Execution.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query (without logs for list view)
    result = await db.execute(query)
    rows = result.all()

    return ExecutionListResponse(
        executions=[
            ExecutionListItemResponse(
                id=execution.id,
                workflow_id=execution.workflow_id,
                workflow_name=workflow_name,
                temporal_workflow_id=execution.temporal_workflow_id,
                temporal_run_id=execution.temporal_run_id,
                status=execution.status,
                inputs=execution.inputs,
                outputs=execution.outputs,
                error=execution.error,
                started_at=execution.started_at,
                completed_at=execution.completed_at
            )
            for execution, workflow_name in rows
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

    # Query with logs eagerly loaded and workflow name
    query = (
        select(Execution, Workflow.name.label('workflow_name'))
        .join(Workflow, Execution.workflow_id == Workflow.id)
        .where(Execution.id == execution_id)
        .options(selectinload(Execution.logs))
    )

    result = await db.execute(query)
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Execution not found")

    execution, workflow_name = row

    return ExecutionResponse(
        id=execution.id,
        workflow_id=execution.workflow_id,
        workflow_name=workflow_name,
        temporal_workflow_id=execution.temporal_workflow_id,
        temporal_run_id=execution.temporal_run_id,
        status=execution.status,
        inputs=execution.inputs,
        outputs=execution.outputs,
        error=execution.error,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        logs=[ExecutionLogResponse.model_validate(log) for log in execution.logs]
    )


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


@router.post("/{execution_id}/sync", response_model=ExecutionResponse)
async def sync_execution_status(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Sync execution status from Temporal"""

    # Get execution with workflow name
    query = (
        select(Execution, Workflow.name.label('workflow_name'))
        .join(Workflow, Execution.workflow_id == Workflow.id)
        .where(Execution.id == execution_id)
        .options(selectinload(Execution.logs))
    )
    result = await db.execute(query)
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Execution not found")

    execution, workflow_name = row

    # Sync status from Temporal
    temporal_service = TemporalService()
    try:
        await temporal_service.get_workflow_status(execution_id, db)
        # Refresh execution to get updated status
        await db.refresh(execution)
    except Exception:
        # If temporal sync fails, continue with current database state
        pass

    return ExecutionResponse(
        id=execution.id,
        workflow_id=execution.workflow_id,
        workflow_name=workflow_name,
        temporal_workflow_id=execution.temporal_workflow_id,
        temporal_run_id=execution.temporal_run_id,
        status=execution.status,
        inputs=execution.inputs,
        outputs=execution.outputs,
        error=execution.error,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        logs=[ExecutionLogResponse.model_validate(log) for log in execution.logs]
    )
