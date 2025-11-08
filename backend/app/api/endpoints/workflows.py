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
    WorkflowExecuteResponse,
    WorkflowSuggestMetadataRequest,
    WorkflowSuggestMetadataResponse
)
from app.services.temporal_service import TemporalService
from app.services.azure_llm_service import AzureLLMService

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


@router.post("/suggest-metadata", response_model=WorkflowSuggestMetadataResponse)
async def suggest_workflow_metadata(
    request: WorkflowSuggestMetadataRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    AI-powered workflow title and description suggestion based on canvas structure

    Analyzes the workflow nodes, edges, and domains to generate meaningful
    title and description using Azure OpenAI.
    """

    if not request.nodes:
        raise HTTPException(status_code=400, detail="Workflow must have at least one node")

    try:
        # Extract workflow information
        node_count = len(request.nodes)
        edge_count = len(request.edges)

        # Get action names and domains
        action_names = []
        domains = set()

        for node in request.nodes:
            node_data = node.data
            if 'label' in node_data:
                action_names.append(node_data['label'])
            if 'action' in node_data and 'domain' in node_data['action']:
                domains.add(node_data['action']['domain'])

        # Build workflow sequence
        action_sequence = " → ".join(action_names) if action_names else "workflow"
        domain_list = ", ".join(sorted(domains)) if domains else "general"

        # Create AI prompt
        system_prompt = """You are a workflow naming expert. Generate a concise, descriptive title and detailed description for a workflow automation.

Title Guidelines:
- 3-6 words maximum
- Action-oriented (e.g., "Late Load Carrier Follow-up", "Multi-Level Escalation Workflow")
- Clear purpose
- Professional tone

Description Guidelines:
- 2-3 sentences
- Explain the workflow purpose and main steps
- Highlight the business value
- Be specific about what the workflow does

Return JSON format:
{
  "title": "...",
  "description": "..."
}"""

        user_message = f"""Analyze this workflow and suggest a title and description:

Workflow Structure:
- Number of nodes: {node_count}
- Number of connections: {edge_count}
- Domains: {domain_list}
- Action sequence: {action_sequence}

Generate a professional title and description that captures the workflow's purpose."""

        # Call Azure OpenAI
        llm_service = AzureLLMService()
        response = await llm_service.chat_with_structured_output(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt
        )

        # Extract title and description
        title = response.get("title", "Automated Workflow")
        description = response.get("description", "This workflow automates a business process using multiple action steps.")

        # Fallback to rule-based if AI fails
        if not title or title == "...":
            # Generate fallback title based on domains
            if "Carrier Follow Up" in domains:
                title = "Carrier Follow-up Workflow"
            elif "Escalation" in domains:
                title = "Escalation Management Workflow"
            elif "Shipment Update" in domains:
                title = "Shipment Update Workflow"
            else:
                title = f"Workflow with {node_count} Steps"

        if not description or description == "...":
            description = f"This workflow uses {node_count} action(s) to automate tasks in {domain_list}. " \
                         f"The workflow follows this sequence: {action_sequence}."

        return WorkflowSuggestMetadataResponse(
            title=title,
            description=description
        )

    except Exception as e:
        # Return fallback suggestions on error
        return WorkflowSuggestMetadataResponse(
            title=f"Workflow with {len(request.nodes)} Actions",
            description=f"This workflow automates a process using {len(request.nodes)} connected action(s)."
        )
