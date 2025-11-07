#!/bin/bash

# Workflow Builder - Local Development Startup Script
# This script starts all required services for local development

set -e

PROJECT_ROOT="/Users/bhavani.shankar/Desktop/code/python_projects/workflow-builder"
cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Workflow Builder - Local Dev Setup  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check PostgreSQL
echo -e "${YELLOW}[1/6] Checking PostgreSQL...${NC}"
if ! brew services list | grep -q "postgresql@16.*started"; then
    echo -e "${YELLOW}Starting PostgreSQL...${NC}"
    brew services start postgresql@16
    sleep 3
else
    echo -e "${GREEN}PostgreSQL is already running${NC}"
fi

# Check if database exists, create if not
if ! psql -lqt | cut -d \| -f 1 | grep -qw workflow_builder; then
    echo -e "${YELLOW}Creating database 'workflow_builder'...${NC}"
    createdb workflow_builder
    echo -e "${GREEN}Database created${NC}"
else
    echo -e "${GREEN}Database 'workflow_builder' already exists${NC}"
fi
echo ""

# Setup Backend
echo -e "${YELLOW}[2/6] Setting up backend...${NC}"
cd "$PROJECT_ROOT/backend"

# Activate virtual environment
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
else
    echo -e "${RED}Virtual environment not found. Run 'uv venv' first.${NC}"
    exit 1
fi

# Run migrations
echo -e "${YELLOW}Running database migrations...${NC}"
uv run alembic upgrade head

# Seed database
echo -e "${YELLOW}Seeding database with actions...${NC}"
uv run python -m app.core.seed_data

echo -e "${GREEN}Backend setup complete${NC}"
echo ""

# Instructions for starting services
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Setup Complete! Now start services:  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}Open 4 separate terminals and run:${NC}"
echo ""

echo -e "${GREEN}Terminal 1 - Temporal Server:${NC}"
echo -e "  temporal server start-dev"
echo ""

echo -e "${GREEN}Terminal 2 - Backend API:${NC}"
echo -e "  cd $PROJECT_ROOT"
echo -e "  source .venv/bin/activate"
echo -e "  cd backend"
echo -e "  uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""

echo -e "${GREEN}Terminal 3 - Temporal Worker:${NC}"
echo -e "  cd $PROJECT_ROOT"
echo -e "  source .venv/bin/activate"
echo -e "  cd backend"
echo -e "  uv run python -m app.temporal_workflows.worker"
echo ""

echo -e "${GREEN}Terminal 4 - Frontend:${NC}"
echo -e "  cd $PROJECT_ROOT/frontend"
echo -e "  npm run dev"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Access Points:${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "  Frontend:      ${GREEN}http://localhost:3000${NC}"
echo -e "  Backend API:   ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs:      ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  Temporal UI:   ${GREEN}http://localhost:8233${NC}"
echo ""
echo -e "${BLUE}Login: admin / admin${NC}"
echo ""
