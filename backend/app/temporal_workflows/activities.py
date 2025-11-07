"""
Temporal activities for executing actions
"""
import base64
from typing import Dict, Any
from temporalio import activity
import httpx
from app.core.config import settings


@activity.defn
async def execute_action(
    action_name: str,
    config: Dict[str, Any],
    state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute an action by calling the AI Agent Actions API

    Args:
        action_name: Name of the action to execute
        config: Configuration for the action
        state: Current workflow state

    Returns:
        Action execution result
    """
    activity.logger.info(f"Executing action: {action_name}")

    # TODO: Load action details from database to get endpoint
    # For now, use a default endpoint pattern
    endpoint = f"{settings.ACTION_SERVICE_URL}/api/v1/actions/{action_name}"

    # Build request body
    request_body = {
        "event_data": config.get("event_data", {}),
        "configurations": config.get("configurations", {}),
        "data": config.get("data", {})
    }

    # Build auth header
    credentials = f"{settings.ACTION_SERVICE_AUTH_USER}:{settings.ACTION_SERVICE_AUTH_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }

    # Make HTTP request with retry
    max_retries = 3
    last_error = None

    async with httpx.AsyncClient(timeout=120.0) as client:
        for attempt in range(max_retries):
            try:
                activity.logger.info(f"Attempt {attempt + 1}/{max_retries} for action {action_name}")

                response = await client.post(
                    endpoint,
                    json=request_body,
                    headers=headers
                )

                response.raise_for_status()
                result = response.json()

                activity.logger.info(f"Action {action_name} completed successfully")

                return {
                    "status": "SUCCESS",
                    "data": result,
                    "action_name": action_name
                }

            except httpx.HTTPStatusError as e:
                last_error = e
                activity.logger.error(f"HTTP error on attempt {attempt + 1}: {e}")
                if e.response.status_code >= 500 and attempt < max_retries - 1:
                    # Retry on server errors
                    continue
                else:
                    break

            except Exception as e:
                last_error = e
                activity.logger.error(f"Error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    continue
                else:
                    break

    # All retries failed
    activity.logger.error(f"Action {action_name} failed after {max_retries} attempts")

    return {
        "status": "FAILED",
        "error": str(last_error),
        "action_name": action_name
    }
