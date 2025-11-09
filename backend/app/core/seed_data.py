"""
Seed data script - loads actions from action_catalogue.json into database
"""
import json
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import engine, AsyncSessionLocal, Base
from app.models.action import Action


async def create_tables():
    """Create all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Database tables created")


async def seed_actions(session: AsyncSession, catalog_path: Path):
    """Seed actions from a given catalog file"""
    if not catalog_path.exists():
        print(f"✗ Action catalog not found at {catalog_path}")
        return 0, 0

    with open(catalog_path, "r") as f:
        catalog = json.load(f)

    actions_data = catalog.get("actions", [])
    print(f"Found {len(actions_data)} actions in {catalog_path.name}")

    seeded_count = 0
    updated_count = 0

    for action_data in actions_data:
        # Check if action already exists using endpoint (unique identifier)
        endpoint = action_data["api"]["endpoint"]
        stmt = select(Action).where(Action.endpoint == endpoint)
        result = await session.execute(stmt)
        existing_action = result.scalar_one_or_none()

        if existing_action:
            # Update existing action with latest data from catalogue
            existing_action.display_name = _generate_display_name(action_data["action_name"])
            existing_action.class_name = action_data["class_name"]
            existing_action.method_name = action_data["method_name"]
            existing_action.domain = action_data["domain"]
            existing_action.endpoint = action_data["api"]["endpoint"]
            existing_action.http_method = action_data["api"]["http_method"]
            existing_action.description = action_data.get("description")
            existing_action.parameters = action_data.get("parameters", {})
            existing_action.returns = action_data.get("returns", {})
            existing_action.category = action_data["domain"]
            existing_action.tags = _extract_tags(action_data)
            existing_action.is_active = True

            updated_count += 1
            print(f"  ⟳ Updated action: {action_data['action_name']}")
            continue

        # Create new action
        action = Action(
            action_name=action_data["action_name"],
            display_name=_generate_display_name(action_data["action_name"]),
            class_name=action_data["class_name"],
            method_name=action_data["method_name"],
            domain=action_data["domain"],
            endpoint=action_data["api"]["endpoint"],
            http_method=action_data["api"]["http_method"],
            description=action_data.get("description"),
            parameters=action_data.get("parameters", {}),
            returns=action_data.get("returns", {}),
            category=action_data["domain"],  # Use domain as category
            tags=_extract_tags(action_data),
            is_active=True
        )

        session.add(action)
        seeded_count += 1
        print(f"  ✓ Seeded action: {action_data['action_name']}")

    await session.commit()
    print(f"✓ Seeded {seeded_count} new actions")
    print(f"✓ Updated {updated_count} existing actions")

    return seeded_count, updated_count


def _generate_display_name(action_name: str) -> str:
    """Generate display name from action_name (snake_case to Title Case)"""
    # Convert snake_case to Title Case
    # load_search_trigger -> Load Search Trigger
    words = action_name.replace('_', ' ').split()
    return ' '.join(word.capitalize() for word in words)


def _extract_tags(action_data: dict) -> list:
    """Extract tags from action metadata"""
    tags = []

    # Add tags based on action characteristics
    if "LLM" in action_data.get("description", "") or "AI" in action_data.get("description", ""):
        tags.append("AI-Powered")

    # Domain-based tags
    if action_data["domain"] == "Carrier Follow Up":
        tags.append("Popular")
    elif action_data["domain"] == "Shipment Update":
        tags.append("Stable")
    elif action_data["domain"] == "Escalation":
        tags.append("Essential")
    elif action_data["domain"] == "Document Processing":
        tags.append("SAM")
        tags.append("Document Processing")

    # Action-specific tags
    action_name_lower = action_data["action_name"].lower()
    if "email" in action_name_lower:
        tags.append("Communication")
    if "load" in action_name_lower or "shipment" in action_name_lower:
        tags.append("Logistics")
    if "escalation" in action_name_lower:
        tags.append("Workflow")
    if "extract" in action_name_lower or "classifier" in action_name_lower:
        tags.append("Data Extraction")
    if "order" in action_name_lower or "create" in action_name_lower:
        tags.append("Order Management")

    return tags


async def seed_database():
    """Main seed function"""
    print("\n" + "="*50)
    print("WORKFLOW BUILDER - DATABASE SEEDING")
    print("="*50 + "\n")

    # Create tables
    await create_tables()

    # Get base directory (project root)
    base_dir = Path(__file__).parent.parent.parent.parent

    # Seed actions from both catalogues
    total_seeded = 0
    total_updated = 0

    async with AsyncSessionLocal() as session:
        # Seed from action_catalogue.json (original actions)
        print("\nSeeding from action_catalogue.json...")
        catalog1_path = base_dir / "action_catalogue.json"
        seeded1, updated1 = await seed_actions(session, catalog1_path)
        total_seeded += seeded1
        total_updated += updated1

        # Seed from sam_action_catalogue.json (SAM actions)
        print("\nSeeding from sam_action_catalogue.json...")
        catalog2_path = base_dir / "sam_action_catalogue.json"
        seeded2, updated2 = await seed_actions(session, catalog2_path)
        total_seeded += seeded2
        total_updated += updated2

    print("\n" + "="*50)
    print(f"✓ Total: {total_seeded} new actions seeded, {total_updated} actions updated")
    print("✓ Database seeding completed successfully!")
    print("="*50 + "\n")


if __name__ == "__main__":
    asyncio.run(seed_database())
