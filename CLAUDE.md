# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Workflow Builder** for creating automated logistics workflows using AI Agent Actions. The project enables building workflows for:
- **Carrier Follow Up**: Search for late loads and send automated follow-up emails to carriers
- **Shipment Update**: Process incoming emails, extract shipment data, and update loads
- **Escalation**: Multi-level escalation workflows (L1→L2→L3) for loads without response

## Project Setup

### Python Version
- Required: Python 3.10+
- Version file: `.python-version` (set to 3.10)

### Environment Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install dependencies (once pyproject.toml is populated)
pip install -e .
```

### Running the Project
```bash
python main.py
```

## Architecture

### Action Catalogue System
The core of this project is the `action_catalogue.json` file, which defines 17+ available actions organized by domain:

**Carrier Follow Up Domain:**
- `load_search_trigger`: Search for loads with filters (status, date range, carrier, mode)
- `send_email`: Send emails with LLM generation or HTML templates

**Shipment Update Domain:**
- `process_emails`: Process Gmail emails with categorization and webhook routing
- `extract_data`: Extract structured data from emails/files using 35+ fine-tuned prompts
- `load_update`: Update load-level information (assets, driver, contacts)
- `load_stop_update`: Update stop-level information (ETAs, appointments)
- `update_milestones`: Track workflow progress and communication status
- `add_smart_action`/`update_smart_action`: Track automated actions for audit

**Escalation Domain:**
- `get_escalation_milestones`: Find loads needing escalation based on time elapsed
- `draft_escalation_mail`: Generate escalation emails with original thread context
- `load_get_details`: Retrieve load details by load numbers
- `retrieve_escalation_contacts_v2`: Get L2/L3 contacts based on escalation level
- `send_escalation_mail_loop`: Send escalation emails in loop
- `update_escalation_milestones`: Update milestone status after escalation

### Workflow Patterns
Three primary workflow patterns are defined in the action catalogue:

1. **Carrier Follow Up Pattern**:
   - Sequence: `load_search_trigger` → `send_email`
   - Use case: Daily automated follow-up for delayed shipments

2. **Shipment Update Pattern**:
   - Sequence: `process_emails` → `extract_data` → `load_update`/`load_stop_update` → `update_milestones`
   - Use case: Automated processing of carrier email updates

3. **Escalation Pattern**:
   - Sequence: `get_escalation_milestones` → `draft_escalation_mail` → `load_get_details` → `retrieve_escalation_contacts_v2` → `send_escalation_mail_loop` → `update_escalation_milestones`
   - Use case: Multi-level escalation for late loads without response

### LangGraph Integration
Workflows are designed to be built using LangGraph:
- **State Management**: Use TypedDict to define state with all required fields
- **Nodes**: Each action becomes an async function node that takes state and returns state
- **Conditional Edges**: Branch based on response data or conditions
- **Loop Nodes**: For iterating over collections (e.g., sending emails per SCAC/thread)

### API Communication
All actions use **HTTP API calls** (not Python imports):
- Base URL: `ACTION_SERVICE_URL` environment variable (default: http://localhost:8081)
- Authentication: Basic Auth with header `Authorization: Basic <base64_encoded_credentials>`
- Request format: JSON with `event_data`, `configurations`, and optional `data` sections
- Response format: JSON with action-specific results and `audit` trail

## Key Development Concepts

### Action Structure
Each action in the catalogue defines:
- **Parameters**: `event_data` (shipper_id, agent_id), `configurations` (action-specific settings), `data` (input from previous actions)
- **Returns**: Action-specific outputs and audit logs
- **API Details**: Endpoint, HTTP method, authentication, timeout, retry policy
- **Prerequisites**: Required dependencies and API access
- **Examples**: Usage examples with request/response samples

### Common Configuration
```python
# Required in all actions
event_data = {
    "shipper_id": "shipper-123",
    "agent_id": "TRACY",  # Options: TRACY, SAM, ALAN, PETE
    "parent_request_id": "req-456",  # For tracking
    "workflow_id": "wf-789"  # For workflow tracking
}
```

### Data Flow Between Actions
Actions pass data through the state dictionary:
- `load_search_trigger` outputs `scac_load_dict` → consumed by `send_email`
- `process_emails` outputs `processed_emails` → consumed by `extract_data`
- `extract_data` outputs `extracted_entities` → consumed by `load_update`/`load_stop_update`
- `get_escalation_milestones` outputs `escalation_milestones` → consumed by `draft_escalation_mail`

### Environment Variables
Required environment variables:
```bash
ACTION_SERVICE_URL=http://localhost:8081  # AI Agent Actions API base URL
AUTH_TOKEN=<base64_encoded_credentials>   # Basic auth token
ANTHROPIC_API_KEY=<key>                   # For LLM-powered actions
OPENAI_API_KEY=<key>                      # Alternative to Anthropic
```

## Best Practices

### When Building Workflows
1. **Always use `load_search_trigger` before `send_email`** to get properly formatted `scac_load_dict`
2. **Enable smart action tracking** with `is_smart_action: true` for visibility
3. **Use `exact_match=true`** in `load_get_details` when you have specific load numbers
4. **Set `enable_webhook_calls=false`** for safe testing of `process_emails`
5. **Include `parent_request_id`** for tracking across API calls
6. **Use `include_scac_grouped=true`** when sending carrier emails (groups loads by carrier)

### Error Handling
- Always use try/except blocks for HTTP requests
- Check response status codes before processing
- Extract data safely with `.get()` on state dictionaries
- Include error information in state for downstream nodes
- Handle partial failures (e.g., some loads update successfully, others fail)

### Email Actions
- **LLM Generation Mode**: Set `use_llm_generation: true` and provide `email_description`
- **Template Mode**: Set `use_llm_generation: false` and provide `email_template` with `{{placeholders}}`
- **Gmail OAuth**: Provide `gmail_config` in request body (recommended for MCP) OR use environment variables
- **Contact Retrieval**: Use `custom_recipients` to override platform contacts, or `to_list`/`cc_list` to concatenate

### Data Extraction
- **Fine-tuned prompts**: 35+ available (load_number, tracking_id, pickup_date, delivery_date, driver_name, etc.)
- **Custom prompts**: Use objects with `{name, description, force_custom}` for ad-hoc fields
- **Source types**: `file` (Excel/CSV/PDF), `text`, or `email`
- **Entity types**: Not limited to loads - supports orders, shipments, inventory, custom

## Action Catalogue Reference

For detailed information about each action:
1. Open `action_catalogue.json`
2. Search for the action name
3. Review: `description`, `when_to_use`, `parameters`, `returns`, `example_usage`, and `additional_examples`

The catalogue includes inline documentation for:
- 100+ email template placeholders
- Redis state management for `process_emails`
- Fine-tuned data extraction prompts
- Webhook routing and categorization logic
- Milestone status tracking
- Escalation level logic (L1→L2→L3)
