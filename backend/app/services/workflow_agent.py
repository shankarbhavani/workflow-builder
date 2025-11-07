"""
LangGraph-based conversational agent for workflow generation
"""
from typing import TypedDict, Annotated, Literal, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
import json

from app.services.azure_llm_service import AzureLLMService


# Define the conversation state
class ConversationState(TypedDict):
    """State for the conversation agent"""
    messages: List[Dict[str, str]]  # Conversation history
    workflow_draft: Dict[str, Any]  # Current workflow structure
    action_catalog: List[Dict[str, Any]]  # Available actions
    intent: str  # Current intent: create, modify, clarify, complete
    clarification_needed: bool  # Whether clarification is needed
    response: str  # Final response to user


class WorkflowAgent:
    """LangGraph agent for conversational workflow creation"""

    def __init__(self):
        self.llm_service = AzureLLMService()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph conversation flow"""

        # Create state graph
        workflow = StateGraph(ConversationState)

        # Add nodes
        workflow.add_node("router", self._route_intent)
        workflow.add_node("create_workflow", self._create_workflow)
        workflow.add_node("modify_workflow", self._modify_workflow)
        workflow.add_node("clarification", self._ask_clarification)
        workflow.add_node("validation", self._validate_workflow)
        workflow.add_node("generate_response", self._generate_response)

        # Set entry point
        workflow.set_entry_point("router")

        # Add edges
        workflow.add_conditional_edges(
            "router",
            self._route_decision,
            {
                "create": "create_workflow",
                "modify": "modify_workflow",
                "clarify": "clarification",
                "complete": "generate_response",
            }
        )

        workflow.add_edge("create_workflow", "validation")
        workflow.add_edge("modify_workflow", "validation")
        workflow.add_edge("clarification", "generate_response")

        workflow.add_conditional_edges(
            "validation",
            self._validation_decision,
            {
                "valid": "generate_response",
                "needs_clarification": "clarification",
            }
        )

        workflow.add_edge("generate_response", END)

        return workflow.compile()

    async def _route_intent(self, state: ConversationState) -> ConversationState:
        """Determine user intent from the latest message"""

        messages = state["messages"]
        workflow_draft = state.get("workflow_draft", {})

        # Get latest user message
        latest_message = messages[-1] if messages else {}
        user_input = latest_message.get("content", "")

        # Use LLM to classify intent
        system_prompt = """You are a workflow assistant. Analyze the user's message and determine their intent.

        Possible intents:
        - create: User wants to create a new workflow
        - modify: User wants to modify existing workflow draft
        - clarify: User is answering a clarification question
        - complete: User wants to finalize/save the workflow

        Return ONLY the intent word, nothing else."""

        context = f"Current workflow draft exists: {bool(workflow_draft)}"

        response = await self.llm_service.chat(
            messages=[{"role": "user", "content": f"{context}\n\nUser message: {user_input}"}],
            system_prompt=system_prompt
        )

        state["intent"] = response.strip().lower()
        return state

    def _route_decision(self, state: ConversationState) -> str:
        """Decision function for routing"""
        intent = state.get("intent", "create")

        if intent in ["create", "modify", "clarify", "complete"]:
            return intent
        return "create"

    async def _create_workflow(self, state: ConversationState) -> ConversationState:
        """Create initial workflow from user description"""

        messages = state["messages"]
        action_catalog = state.get("action_catalog", [])

        # Get user's workflow description
        latest_message = messages[-1] if messages else {}
        user_description = latest_message.get("content", "")

        # Build action catalog summary
        actions_summary = "\n".join([
            f"- {action['name']}: {action.get('description', '')}"
            for action in action_catalog
        ])

        system_prompt = f"""You are a workflow builder assistant. Create a workflow based on the user's description.

Available actions:
{actions_summary}

Return a JSON object with this structure:
{{
    "nodes": [
        {{
            "id": "node_1",
            "type": "action",
            "data": {{
                "action_name": "action_name_from_catalog",
                "label": "Human readable label",
                "config": {{}}
            }},
            "position": {{"x": 100, "y": 100}}
        }}
    ],
    "edges": [
        {{
            "id": "edge_1",
            "source": "node_1",
            "target": "node_2"
        }}
    ]
}}

Generate a logical workflow that accomplishes the user's goal."""

        response = await self.llm_service.chat_with_structured_output(
            messages=[{"role": "user", "content": user_description}],
            system_prompt=system_prompt
        )

        state["workflow_draft"] = response
        state["clarification_needed"] = False
        return state

    async def _modify_workflow(self, state: ConversationState) -> ConversationState:
        """Modify existing workflow based on user feedback"""

        messages = state["messages"]
        workflow_draft = state.get("workflow_draft", {})

        latest_message = messages[-1] if messages else {}
        modification_request = latest_message.get("content", "")

        system_prompt = f"""You are a workflow builder assistant. Modify the existing workflow based on the user's request.

Current workflow:
{json.dumps(workflow_draft, indent=2)}

User's modification request:
{modification_request}

Return the COMPLETE modified workflow as JSON with the same structure (nodes and edges)."""

        response = await self.llm_service.chat_with_structured_output(
            messages=[{"role": "user", "content": modification_request}],
            system_prompt=system_prompt
        )

        state["workflow_draft"] = response
        state["clarification_needed"] = False
        return state

    async def _ask_clarification(self, state: ConversationState) -> ConversationState:
        """Generate clarification question for the user"""

        messages = state["messages"]
        workflow_draft = state.get("workflow_draft", {})

        system_prompt = """You are a workflow builder assistant. Generate a helpful clarification question
        to better understand the user's needs. Be specific and actionable."""

        response = await self.llm_service.chat(
            messages=messages,
            system_prompt=system_prompt
        )

        state["response"] = response
        state["clarification_needed"] = False
        return state

    async def _validate_workflow(self, state: ConversationState) -> ConversationState:
        """Validate the workflow structure"""

        workflow_draft = state.get("workflow_draft", {})

        # Basic validation
        nodes = workflow_draft.get("nodes", [])
        edges = workflow_draft.get("edges", [])

        # Check if workflow is valid
        if len(nodes) == 0:
            state["clarification_needed"] = True
            state["response"] = "I couldn't generate any workflow nodes. Could you provide more details about what you want to accomplish?"
        elif len(nodes) < 2:
            state["clarification_needed"] = True
            state["response"] = "The workflow seems incomplete. Would you like to add more steps?"
        else:
            state["clarification_needed"] = False

        return state

    def _validation_decision(self, state: ConversationState) -> str:
        """Decision function for validation"""
        if state.get("clarification_needed", False):
            return "needs_clarification"
        return "valid"

    async def _generate_response(self, state: ConversationState) -> ConversationState:
        """Generate final response to user"""

        workflow_draft = state.get("workflow_draft", {})
        intent = state.get("intent", "")

        if intent == "complete":
            state["response"] = "Great! Your workflow is ready. Click 'Save Workflow' to finalize it."
        elif intent == "clarify":
            # Response already set by clarification node
            pass
        else:
            # Generate descriptive response about the workflow
            nodes = workflow_draft.get("nodes", [])
            num_steps = len(nodes)

            if num_steps > 0:
                state["response"] = f"I've created a workflow with {num_steps} steps. Review it on the canvas and let me know if you'd like any changes!"
            else:
                state["response"] = "I need more information to create your workflow. What would you like it to do?"

        return state

    async def process_message(
        self,
        message: str,
        conversation_state: Dict[str, Any],
        action_catalog: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process a user message and update conversation state

        Args:
            message: User's message
            conversation_state: Current conversation state (messages, workflow_draft)
            action_catalog: Available actions from the action catalogue

        Returns:
            Updated state with response and workflow_draft
        """

        # Prepare initial state
        messages = conversation_state.get("messages", [])
        messages.append({"role": "user", "content": message})

        initial_state: ConversationState = {
            "messages": messages,
            "workflow_draft": conversation_state.get("workflow_draft", {}),
            "action_catalog": action_catalog,
            "intent": "",
            "clarification_needed": False,
            "response": ""
        }

        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)

        # Add assistant response to messages
        response = final_state.get("response", "")
        final_state["messages"].append({"role": "assistant", "content": response})

        return {
            "messages": final_state["messages"],
            "workflow_draft": final_state.get("workflow_draft", {}),
            "response": response
        }
