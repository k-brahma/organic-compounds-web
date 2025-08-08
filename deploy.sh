#!/bin/bash

# Production deployment script for Organic Compounds Web App
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from .env.example..."
    cp .env.example .env
    print_info "Please edit .env file with your production settings before deploying"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Parse command line arguments
COMMAND=${1:-"up"}
FORCE_BUILD=${2:-""}

case $COMMAND in
    "up"|"start")
        print_info "Starting production environment..."
        
        # Build images if forced or first time
        if [ "$FORCE_BUILD" == "--build" ] || [ ! "$(docker images -q organic-compounds-web-app 2> /dev/null)" ]; then
            print_info "Building Docker images..."
            docker-compose -f docker-compose.production.yml build --no-cache
        fi
        
        # Start services
        print_info "Starting services..."
        docker-compose -f docker-compose.production.yml up -d
        
        # Wait for health checks
        print_info "Waiting for services to be healthy..."
        sleep 10
        
        # Check status
        docker-compose -f docker-compose.production.yml ps
        
        print_info "Production environment started successfully!"
        print_info "Application is available at http://localhost"
        
        if [ ! -z "$DOMAIN_NAME" ]; then
            print_info "Configure your DNS to point $DOMAIN_NAME to this server"
        fi
        ;;
        
    "down"|"stop")
        print_info "Stopping production environment..."
        docker-compose -f docker-compose.production.yml down
        print_info "Services stopped"
        ;;
        
    "restart")
        print_info "Restarting production environment..."
        docker-compose -f docker-compose.production.yml restart
        ;;
        
    "logs")
        docker-compose -f docker-compose.production.yml logs -f --tail=100
        ;;
        
    "status")
        docker-compose -f docker-compose.production.yml ps
        ;;
        
    "backup")
        print_info "Creating backup..."
        BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p $BACKUP_DIR
        
        # Backup volumes
        docker run --rm -v organic-compounds-web_app-data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/app-data.tar.gz -C /data .
        
        print_info "Backup created in $BACKUP_DIR"
        ;;
        
    "update")
        print_info "Updating application..."
        
        # Pull latest changes
        git pull origin main
        
        # Rebuild and restart
        print_info "Rebuilding images..."
        docker-compose -f docker-compose.production.yml build --no-cache
        
        print_info "Restarting services..."
        docker-compose -f docker-compose.production.yml up -d
        
        print_info "Update completed"
        ;;
        
    "ssl")
        print_info "Setting up SSL certificates..."
        
        if [ -z "$DOMAIN_NAME" ] || [ -z "$SSL_EMAIL" ]; then
            print_error "DOMAIN_NAME and SSL_EMAIL must be set in .env file"
            exit 1
        fi
        
        # Install certbot and obtain certificate
        docker run -it --rm \
            -v $(pwd)/nginx/ssl:/etc/letsencrypt \
            -v $(pwd)/nginx/conf.d:/etc/nginx/conf.d \
            -p 80:80 \
            certbot/certbot certonly \
            --standalone \
            --email $SSL_EMAIL \
            --agree-tos \
            --no-eff-email \
            -d $DOMAIN_NAME \
            -d www.$DOMAIN_NAME
        
        print_info "SSL certificates obtained. Update nginx configuration to enable SSL."
        ;;
        
    "clean")
        print_warning "This will remove all containers, images, and volumes!"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose -f docker-compose.production.yml down -v --rmi all
            print_info "Cleanup completed"
        fi
        ;;
        
    *)
        echo "Usage: $0 {up|down|restart|logs|status|backup|update|ssl|clean} [--build]"
        echo ""
        echo "Commands:"
        echo "  up/start    - Start production environment"
        echo "  down/stop   - Stop production environment"
        echo "  restart     - Restart all services"
        echo "  logs        - Show logs"
        echo "  status      - Show service status"
        echo "  backup      - Create backup of data volumes"
        echo "  update      - Update application from git and restart"
        echo "  ssl         - Setup SSL certificates with Let's Encrypt"
        echo "  clean       - Remove all containers, images, and volumes"
        echo ""
        echo "Options:"
        echo "  --build     - Force rebuild of Docker images (with 'up' command)"
        exit 1
        ;;
esac