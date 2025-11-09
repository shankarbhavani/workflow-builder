"""
Main API router that combines all endpoint routers
"""
from fastapi import APIRouter
from app.api.endpoints import actions, workflows, executions, auth, chat, gmail_s3_action

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(actions.router)
api_router.include_router(workflows.router)
api_router.include_router(executions.router)
api_router.include_router(chat.router)
api_router.include_router(gmail_s3_action.router)
