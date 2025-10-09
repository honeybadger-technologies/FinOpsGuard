#!/bin/bash
# Database management script for FinOpsGuard

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  init        - Initialize database (create tables)"
    echo "  migrate     - Run database migrations"
    echo "  upgrade     - Upgrade to latest schema"
    echo "  downgrade   - Downgrade to previous schema"
    echo "  reset       - Drop all tables and reinitialize"
    echo "  status      - Show migration status"
    echo "  shell       - Open PostgreSQL shell"
    echo "  backup      - Backup database to SQL file"
    echo "  restore     - Restore database from SQL file"
    echo ""
    exit 1
}

check_postgres() {
    if ! command -v psql &> /dev/null; then
        echo -e "${RED}Error: psql not found. Please install PostgreSQL client.${NC}"
        exit 1
    fi
}

# Source environment
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
fi

DB_HOST=${POSTGRES_HOST:-localhost}
DB_PORT=${POSTGRES_PORT:-5432}
DB_NAME=${POSTGRES_DB:-finopsguard}
DB_USER=${POSTGRES_USER:-finopsguard}
DB_PASSWORD=${POSTGRES_PASSWORD:-finopsguard}

export DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
export PYTHONPATH="$PROJECT_ROOT/src"

case "${1:-help}" in
    init)
        echo -e "${GREEN}Initializing database...${NC}"
        cd "$PROJECT_ROOT"
        python -c "from finopsguard.database import init_db; init_db()"
        echo -e "${GREEN}✓ Database initialized${NC}"
        ;;
    
    migrate)
        echo -e "${GREEN}Generating migration...${NC}"
        cd "$PROJECT_ROOT"
        read -p "Migration message: " MESSAGE
        alembic revision --autogenerate -m "$MESSAGE"
        echo -e "${GREEN}✓ Migration generated${NC}"
        ;;
    
    upgrade)
        echo -e "${GREEN}Upgrading database to latest version...${NC}"
        cd "$PROJECT_ROOT"
        alembic upgrade head
        echo -e "${GREEN}✓ Database upgraded${NC}"
        ;;
    
    downgrade)
        echo -e "${YELLOW}Downgrading database...${NC}"
        cd "$PROJECT_ROOT"
        read -p "Downgrade to revision (or -1 for previous): " REVISION
        alembic downgrade ${REVISION:-1}
        echo -e "${GREEN}✓ Database downgraded${NC}"
        ;;
    
    reset)
        echo -e "${RED}WARNING: This will drop all tables and data!${NC}"
        read -p "Are you sure? (yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            echo "Aborted."
            exit 0
        fi
        
        echo -e "${YELLOW}Dropping all tables...${NC}"
        cd "$PROJECT_ROOT"
        alembic downgrade base
        echo -e "${GREEN}Recreating tables...${NC}"
        alembic upgrade head
        echo -e "${GREEN}✓ Database reset complete${NC}"
        ;;
    
    status)
        echo -e "${GREEN}Migration status:${NC}"
        cd "$PROJECT_ROOT"
        alembic current
        alembic history
        ;;
    
    shell)
        check_postgres
        echo -e "${GREEN}Opening PostgreSQL shell...${NC}"
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"
        ;;
    
    backup)
        check_postgres
        BACKUP_FILE="${2:-backup_$(date +%Y%m%d_%H%M%S).sql}"
        echo -e "${GREEN}Backing up database to $BACKUP_FILE...${NC}"
        PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"
        echo -e "${GREEN}✓ Database backed up to $BACKUP_FILE${NC}"
        ;;
    
    restore)
        check_postgres
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Please specify backup file to restore${NC}"
            echo "Usage: $0 restore <backup.sql>"
            exit 1
        fi
        
        echo -e "${YELLOW}WARNING: This will overwrite the current database!${NC}"
        read -p "Are you sure? (yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            echo "Aborted."
            exit 0
        fi
        
        echo -e "${GREEN}Restoring database from $2...${NC}"
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" < "$2"
        echo -e "${GREEN}✓ Database restored from $2${NC}"
        ;;
    
    help|--help|-h)
        usage
        ;;
    
    *)
        echo -e "${RED}Error: Unknown command '${1}'${NC}"
        usage
        ;;
esac

