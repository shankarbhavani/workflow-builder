"""
HTTP client for fetching actions from external action catalog service
"""
import httpx
import base64
from typing import List, Dict, Any, Optional
from app.core.config import settings


class ActionServiceClient:
    """Client for external action catalog API"""

    def __init__(self):
        self.base_url = settings.EXTERNAL_ACTION_SERVICE_URL
        self.auth_user = settings.ACTION_SERVICE_AUTH_USER
        self.auth_password = settings.ACTION_SERVICE_AUTH_PASSWORD
        self.timeout = 30.0

    def _get_auth_header(self) -> str:
        """Generate Basic Auth header"""
        credentials = f"{self.auth_user}:{self.auth_password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    async def fetch_actions(self) -> List[Dict[str, Any]]:
        """
        Fetch all actions from external catalog

        Returns:
            List of action dictionaries with keys: action_name, domain, display_name, description, parameters
        """
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Assuming the external service has a similar endpoint structure
                # Adjust the endpoint path if needed based on actual API
                response = await client.get(
                    f"{self.base_url}/api/actions",
                    headers=headers
                )
                response.raise_for_status()

                data = response.json()

                # Handle different response formats
                if isinstance(data, dict) and "actions" in data:
                    actions = data["actions"]
                elif isinstance(data, list):
                    actions = data
                else:
                    print(f"Unexpected response format from external catalog: {type(data)}")
                    return []

                return actions

        except httpx.HTTPStatusError as e:
            print(f"HTTP error fetching external actions: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.RequestError as e:
            print(f"Network error fetching external actions: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching external actions: {str(e)}")
            return []

    async def build_action_lookup(self) -> Dict[str, Dict[str, Any]]:
        """
        Build a lookup dictionary mapping action_name to action metadata

        Returns:
            Dictionary with action_name as key and action data as value
        """
        actions = await self.fetch_actions()

        # Build lookup dictionary
        lookup = {}
        for action in actions:
            action_name = action.get("action_name")
            if action_name:
                lookup[action_name] = {
                    "id": action.get("id"),
                    "action_name": action_name,
                    "domain": action.get("domain") or action.get("category"),
                    "display_name": action.get("display_name") or self._generate_display_name(action_name),
                    "description": action.get("description"),
                    "parameters": action.get("parameters", {})
                }

        return lookup

    @staticmethod
    def _generate_display_name(action_name: str) -> str:
        """Generate display name from action_name (snake_case to Title Case)"""
        words = action_name.replace('_', ' ').split()
        return ' '.join(word.capitalize() for word in words)


# Singleton instance
action_service_client = ActionServiceClient()
