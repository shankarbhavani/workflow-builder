"""
Azure OpenAI LLM service for natural language workflow generation
"""
from typing import List, Dict, Any
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.core.config import settings


class AzureLLMService:
    """Service for interacting with Azure OpenAI"""

    _llm: AzureChatOpenAI = None

    @classmethod
    def get_llm(cls) -> AzureChatOpenAI:
        """Get or create Azure OpenAI client"""
        if cls._llm is None:
            cls._llm = AzureChatOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                temperature=0.7,
                max_tokens=2000,
            )
        return cls._llm

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = None
    ) -> str:
        """
        Send chat messages to Azure OpenAI and get response

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            system_prompt: Optional system prompt to prepend

        Returns:
            Response content string
        """
        llm = self.get_llm()

        # Convert messages to LangChain format
        lc_messages = []

        if system_prompt:
            lc_messages.append(SystemMessage(content=system_prompt))

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content))

        # Get response from LLM
        response = await llm.ainvoke(lc_messages)

        return response.content

    async def chat_with_structured_output(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = None
    ) -> Dict[str, Any]:
        """
        Send chat messages and parse structured output (for workflow generation)

        Args:
            messages: List of message dicts
            system_prompt: Optional system prompt

        Returns:
            Parsed structured output dict
        """
        import json

        # Add instruction to return JSON
        enhanced_system = system_prompt or ""
        enhanced_system += "\n\nIMPORTANT: Always return your response as valid JSON."

        response = await self.chat(messages, enhanced_system)

        # Try to parse JSON from response
        try:
            # Remove markdown code blocks if present
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            return json.loads(cleaned.strip())
        except json.JSONDecodeError:
            # If parsing fails, return response as-is
            return {"content": response}
