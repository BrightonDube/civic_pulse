#!/bin/bash

# CivicPulse Railway Deployment Script
# Usage: ./scripts/deploy.sh [backend|frontend|all]

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_railway_cli() {
    if ! command -v railway &> /dev/null; then
        print_error "Railway CLI is not installed."
        echo "Install it with: npm install -g @railway/cli"
        exit 1
    fi
}

check_railway_auth() {
    if ! railway whoami &> /dev/null; then
        print_error "Not authenticated with Railway."
        echo "Run: railway login"
        exit 1
    fi
}

deploy_backend() {
    print_status "Deploying backend to Railway..."
    
    cd "$(dirname "$0")/.."
    
    if railway up --service backend --path-as-root backend --detach; then
        print_success "Backend deployment initiated!"
        echo "View logs: railway logs --service backend"
    else
        print_error "Backend deployment failed!"
        exit 1
    fi
}

deploy_frontend() {
    print_status "Deploying frontend to Railway..."
    
    cd "$(dirname "$0")/.."
    
    if railway up --service frontend --detach; then
        print_success "Frontend deployment initiated!"
        echo "View logs: railway logs --service frontend"
    else
        print_error "Frontend deployment failed!"
        exit 1
    fi
}

deploy_all() {
    print_status "Deploying both backend and frontend..."
    
    deploy_backend
    echo ""
    deploy_frontend
    
    echo ""
    print_success "All deployments initiated!"
}

show_help() {
    echo "CivicPulse Railway Deployment Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  backend   Deploy only the backend service"
    echo "  frontend  Deploy only the frontend service"
    echo "  all       Deploy both backend and frontend (default)"
    echo "  status    Show deployment status"
    echo "  logs      Show recent logs for both services"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 backend    # Deploy backend only"
    echo "  $0 all        # Deploy everything"
    echo "  $0 status     # Check deployment status"
}

show_status() {
    print_status "Checking deployment status..."
    
    cd "$(dirname "$0")/.."
    
    echo ""
    echo "=== Backend Status ==="
    railway status --service backend 2>/dev/null || echo "Unable to fetch backend status"
    
    echo ""
    echo "=== Frontend Status ==="
    railway status --service frontend 2>/dev/null || echo "Unable to fetch frontend status"
}

show_logs() {
    print_status "Fetching recent logs..."
    
    cd "$(dirname "$0")/.."
    
    echo ""
    echo "=== Backend Logs (last 20 lines) ==="
    railway logs --service backend --tail 20 2>/dev/null || echo "Unable to fetch backend logs"
    
    echo ""
    echo "=== Frontend Logs (last 20 lines) ==="
    railway logs --service frontend --tail 20 2>/dev/null || echo "Unable to fetch frontend logs"
}

# Main script
main() {
    check_railway_cli
    check_railway_auth
    
    case "${1:-all}" in
        backend)
            deploy_backend
            ;;
        frontend)
            deploy_frontend
            ;;
        all)
            deploy_all
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
