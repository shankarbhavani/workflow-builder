"""
Temporal worker that processes workflow tasks
"""
import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker
from app.core.config import settings
from app.temporal_workflows.dynamic_workflow import DynamicWorkflow
from app.temporal_workflows.activities import execute_action

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Start the Temporal worker"""
    logger.info("="*50)
    logger.info("WORKFLOW BUILDER - TEMPORAL WORKER")
    logger.info("="*50)
    logger.info(f"Connecting to Temporal at {settings.TEMPORAL_HOST}")

    # Connect to Temporal
    client = await Client.connect(settings.TEMPORAL_HOST)

    logger.info(f"Connected to Temporal namespace: {settings.TEMPORAL_NAMESPACE}")
    logger.info(f"Listening on task queue: {settings.TEMPORAL_TASK_QUEUE}")

    # Create worker
    worker = Worker(
        client,
        task_queue=settings.TEMPORAL_TASK_QUEUE,
        workflows=[DynamicWorkflow],
        activities=[execute_action],
    )

    logger.info("✓ Worker started successfully")
    logger.info("Waiting for workflow tasks...")
    logger.info("="*50)

    # Run worker (blocks indefinitely)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
