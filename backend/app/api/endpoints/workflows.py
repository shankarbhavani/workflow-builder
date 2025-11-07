"""
Workflows API endpoints
"""
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.workflow import Workflow
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowListResponse,
    WorkflowExecuteRequest,
    WorkflowExecuteResponse
)
from app.services.temporal_service import TemporalService

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all workflows"""

    # Build query for active workflows only
    query = select(Workflow).where(Workflow.is_active == True).order_by(Workflow.updated_at.desc())

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    workflows = result.scalars().all()

    return WorkflowListResponse(
        workflows=[WorkflowResponse.model_validate(wf) for wf in workflows],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new workflow"""

    # TODO: Add validation for workflow graph (cycles, connections, etc.)

    # Create workflow
    workflow = Workflow(
        name=workflow_data.name,
        description=workflow_data.description,
        version=1,
        config=workflow_data.config.model_dump(),
        created_by=current_user.get("username", "admin")
    )

    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)

    return WorkflowResponse.model_validate(workflow)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a single workflow by ID"""

    query = select(Workflow).where(Workflow.id == workflow_id)
    result = await db.execute(query)
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return WorkflowResponse.model_validate(workflow)


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: UUID,
    workflow_data: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a workflow (creates new version)"""

    # Get existing workflow
    query = select(Workflow).where(Workflow.id == workflow_id)
    result = await db.execute(query)
    existing_workflow = result.scalar_one_or_none()

    if not existing_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Update fields
    if workflow_data.name is not None:
        existing_workflow.name = workflow_data.name
    if workflow_data.description is not None:
        existing_workflow.description = workflow_data.description
    if workflow_data.config is not None:
        existing_workflow.config = workflow_data.config.model_dump()

    # Increment version
    existing_workflow.version += 1

    await db.commit()
    await db.refresh(existing_workflow)

    return WorkflowResponse.model_validate(existing_workflow)


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Soft delete a workflow"""

    query = select(Workflow).where(Workflow.id == workflow_id)
    result = await db.execute(query)
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow.is_active = False
    await db.commit()

    return {"message": "Workflow deleted successfully"}


@router.post("/{workflow_id}/execute", response_model=WorkflowExecuteResponse)
async def execute_workflow(
    workflow_id: UUID,
    execute_request: WorkflowExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Execute a workflow on Temporal"""

    # Get workflow
    query = select(Workflow).where(Workflow.id == workflow_id)
    result = await db.execute(query)
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Start workflow on Temporal
    temporal_service = TemporalService()
    try:
        execution = await temporal_service.start_workflow(
            workflow_id=workflow_id,
            inputs=execute_request.inputs,
            db_session=db
        )

        return WorkflowExecuteResponse(
            execution_id=execution.id,
            temporal_workflow_id=execution.temporal_workflow_id,
            status=execution.status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")
