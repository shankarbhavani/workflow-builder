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


async def seed_actions(session: AsyncSession):
    """Seed actions from action_catalogue.json"""
    # Load action catalog
    catalog_path = Path(__file__).parent.parent.parent.parent / "action_catalogue.json"

    if not catalog_path.exists():
        print(f"✗ Action catalog not found at {catalog_path}")
        return

    with open(catalog_path, "r") as f:
        catalog = json.load(f)

    actions_data = catalog.get("actions", [])
    print(f"Found {len(actions_data)} actions in catalog")

    seeded_count = 0
    updated_count = 0

    for action_data in actions_data:
        # Check if action already exists
        stmt = select(Action).where(Action.action_name == action_data["action_name"])
        result = await session.execute(stmt)
        existing_action = result.scalar_one_or_none()

        if existing_action:
            print(f"  ⟳ Action '{action_data['action_name']}' already exists, skipping")
            updated_count += 1
            continue

        # Create new action
        action = Action(
            action_name=action_data["action_name"],
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
    print(f"\n✓ Seeded {seeded_count} new actions")
    print(f"✓ Skipped {updated_count} existing actions")


def _extract_tags(action_data: dict) -> list:
    """Extract tags from action metadata"""
    tags = []

    # Add tags based on action characteristics
    if "LLM" in action_data.get("description", "") or "AI" in action_data.get("description", ""):
        tags.append("AI-Powered")

    if action_data["domain"] == "Carrier Follow Up":
        tags.append("Popular")
    elif action_data["domain"] == "Shipment Update":
        tags.append("Stable")
    elif action_data["domain"] == "Escalation":
        tags.append("Essential")

    # Add domain-specific tags
    if "email" in action_data["action_name"]:
        tags.append("Communication")
    if "load" in action_data["action_name"]:
        tags.append("Logistics")
    if "escalation" in action_data["action_name"]:
        tags.append("Workflow")

    return tags


async def seed_database():
    """Main seed function"""
    print("\n" + "="*50)
    print("WORKFLOW BUILDER - DATABASE SEEDING")
    print("="*50 + "\n")

    # Create tables
    await create_tables()

    # Seed actions
    async with AsyncSessionLocal() as session:
        await seed_actions(session)

    print("\n" + "="*50)
    print("✓ Database seeding completed successfully!")
    print("="*50 + "\n")


if __name__ == "__main__":
    asyncio.run(seed_database())
