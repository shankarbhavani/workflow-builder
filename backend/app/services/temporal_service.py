"""
Temporal service for workflow execution
"""
import uuid
from datetime import datetime
from typing import Dict, Any
from temporalio.client import Client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.workflow import Workflow
from app.models.execution import Execution


class TemporalService:
    """Service for interacting with Temporal"""

    _client: Client = None

    @classmethod
    async def get_client(cls) -> Client:
        """Get or create Temporal client"""
        if cls._client is None:
            cls._client = await Client.connect(settings.TEMPORAL_HOST)
        return cls._client

    async def start_workflow(
        self,
        workflow_id: uuid.UUID,
        inputs: Dict[str, Any],
        db_session: AsyncSession
    ) -> Execution:
        """
        Start a workflow execution on Temporal

        Args:
            workflow_id: UUID of the workflow to execute
            inputs: Input parameters for the workflow
            db_session: Database session

        Returns:
            Execution record
        """
        # Load workflow from database
        stmt = select(Workflow).where(Workflow.id == workflow_id)
        result = await db_session.execute(stmt)
        workflow = result.scalar_one_or_none()

        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Generate unique temporal workflow ID
        temporal_workflow_id = f"workflow-{workflow_id}-{uuid.uuid4()}"

        # Get Temporal client
        client = await self.get_client()

        # Start workflow on Temporal
        from app.temporal_workflows.dynamic_workflow import DynamicWorkflow

        handle = await client.start_workflow(
            DynamicWorkflow.run,
            args=[workflow.config, inputs],
            id=temporal_workflow_id,
            task_queue=settings.TEMPORAL_TASK_QUEUE,
        )

        # Create execution record
        execution = Execution(
            workflow_id=workflow_id,
            temporal_workflow_id=temporal_workflow_id,
            temporal_run_id=handle.first_execution_run_id,
            status="RUNNING",
            inputs=inputs,
            started_at=datetime.utcnow()
        )

        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)

        return execution

    async def cancel_workflow(
        self,
        execution_id: uuid.UUID,
        db_session: AsyncSession
    ) -> None:
        """
        Cancel a running workflow execution

        Args:
            execution_id: UUID of the execution to cancel
            db_session: Database session
        """
        # Load execution from database
        stmt = select(Execution).where(Execution.id == execution_id)
        result = await db_session.execute(stmt)
        execution = result.scalar_one_or_none()

        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        # Get workflow handle
        client = await self.get_client()
        handle = client.get_workflow_handle(execution.temporal_workflow_id)

        # Cancel workflow
        await handle.cancel()

        # Update execution status
        execution.status = "CANCELLED"
        execution.completed_at = datetime.utcnow()

        await db_session.commit()

    async def get_workflow_status(
        self,
        execution_id: uuid.UUID,
        db_session: AsyncSession
    ) -> str:
        """
        Get current status of a workflow execution

        Args:
            execution_id: UUID of the execution
            db_session: Database session

        Returns:
            Current status string
        """
        # Load execution from database
        stmt = select(Execution).where(Execution.id == execution_id)
        result = await db_session.execute(stmt)
        execution = result.scalar_one_or_none()

        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        # Get workflow handle and describe
        client = await self.get_client()
        handle = client.get_workflow_handle(execution.temporal_workflow_id)

        try:
            description = await handle.describe()

            # Update status in database if changed
            temporal_status = str(description.status)
            if temporal_status != execution.status:
                execution.status = temporal_status
                if temporal_status in ["COMPLETED", "FAILED", "CANCELLED"]:
                    execution.completed_at = datetime.utcnow()
                await db_session.commit()

            return temporal_status
        except Exception:
            return execution.status
