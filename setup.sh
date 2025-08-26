#!/bin/bash

# IPSAS Financial Software - Complete Setup Script
# This script automates the installation and configuration of the entire system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root"
        exit 1
    fi
}

# Check system requirements
check_system() {
    log "Checking system requirements..."
    
    # Check OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        success "Linux detected"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        success "macOS detected"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        success "Windows detected"
    else
        warning "Unknown OS: $OSTYPE"
    fi
    
    # Check available memory
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        MEMORY=$(free -m | awk 'NR==2{printf "%.0f", $2/1024}')
        if [ $MEMORY -lt 4 ]; then
            warning "Low memory detected: ${MEMORY}GB (4GB+ recommended)"
        else
            success "Memory: ${MEMORY}GB"
        fi
    fi
    
    # Check available disk space
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        DISK_SPACE=$(df -BG . | awk 'NR==2{print $4}' | sed 's/G//')
        if [ $DISK_SPACE -lt 20 ]; then
            warning "Low disk space: ${DISK_SPACE}GB (20GB+ recommended)"
        else
            success "Disk space: ${DISK_SPACE}GB"
        fi
    fi
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Detect Linux distribution
        if command -v apt-get &> /dev/null; then
            # Ubuntu/Debian
            sudo apt-get update
            sudo apt-get install -y curl wget git python3 python3-pip python3-venv nodejs npm postgresql postgresql-contrib redis-server
        elif command -v yum &> /dev/null; then
            # CentOS/RHEL
            sudo yum update -y
            sudo yum install -y curl wget git python3 python3-pip postgresql postgresql-server redis
        elif command -v dnf &> /dev/null; then
            # Fedora
            sudo dnf update -y
            sudo dnf install -y curl wget git python3 python3-pip postgresql postgresql-server redis
        else
            error "Unsupported Linux distribution"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if ! command -v brew &> /dev/null; then
            log "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install python3 node postgresql redis
    fi
    
    success "System dependencies installed"
}

# Install Docker and Docker Compose
install_docker() {
    log "Installing Docker and Docker Compose..."
    
    if ! command -v docker &> /dev/null; then
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Install Docker on Linux
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            rm get-docker.sh
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            # Install Docker Desktop on macOS
            brew install --cask docker
        fi
    else
        success "Docker already installed"
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        # Install Docker Compose
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    else
        success "Docker Compose already installed"
    fi
    
    success "Docker and Docker Compose installed"
}

# Setup PostgreSQL
setup_postgresql() {
    log "Setting up PostgreSQL..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v systemctl &> /dev/null; then
            sudo systemctl start postgresql
            sudo systemctl enable postgresql
        fi
        
        # Create database and user
        sudo -u postgres psql -c "CREATE DATABASE ipsas_financial;"
        sudo -u postgres psql -c "CREATE USER ipsas_user WITH PASSWORD 'ipsas_password';"
        sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ipsas_financial TO ipsas_user;"
        sudo -u postgres psql -c "ALTER USER ipsas_user CREATEDB;"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start postgresql
        
        # Create database and user
        createdb ipsas_financial
        createuser -s ipsas_user
        psql -d ipsas_financial -c "ALTER USER ipsas_user WITH PASSWORD 'ipsas_password';"
    fi
    
    success "PostgreSQL setup completed"
}

# Setup Redis
setup_redis() {
    log "Setting up Redis..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v systemctl &> /dev/null; then
            sudo systemctl start redis-server
            sudo systemctl enable redis-server
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start redis
    fi
    
    success "Redis setup completed"
}

# Setup Python environment
setup_python() {
    log "Setting up Python environment..."
    
    cd backend
    
    # Create virtual environment
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install Python dependencies
    pip install -r requirements.txt
    
    # Install additional development dependencies
    pip install gunicorn psycopg2-binary
    
    cd ..
    
    success "Python environment setup completed"
}

# Setup Node.js environment
setup_nodejs() {
    log "Setting up Node.js environment..."
    
    cd frontend
    
    # Install Node.js dependencies
    npm install
    
    # Install additional dependencies
    npm install -g serve
    
    cd ..
    
    success "Node.js environment setup completed"
}

# Setup environment files
setup_environment() {
    log "Setting up environment configuration..."
    
    # Backend environment
    if [ ! -f backend/.env ]; then
        cp backend/env.example backend/.env
        
        # Generate secret key
        SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
        
        # Update .env file
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/your-secret-key-here-change-in-production/$SECRET_KEY/" backend/.env
        else
            sed -i "s/your-secret-key-here-change-in-production/$SECRET_KEY/" backend/.env
        fi
    fi
    
    success "Environment configuration completed"
}

# Run Django migrations
run_migrations() {
    log "Running Django migrations..."
    
    cd backend
    source venv/bin/activate
    
    # Run migrations
    python manage.py migrate
    
    # Create superuser if it doesn't exist
    echo "from accounts.models import User; User.objects.get_or_create(username='admin', defaults={'email': 'admin@ipsas.com', 'is_staff': True, 'is_superuser': True, 'role': 'admin'})" | python manage.py shell
    
    # Collect static files
    python manage.py collectstatic --noinput
    
    cd ..
    
    success "Django migrations completed"
}

# Build frontend
build_frontend() {
    log "Building frontend application..."
    
    cd frontend
    
    # Build production version
    npm run build
    
    cd ..
    
    success "Frontend build completed"
}

# Test the application
test_application() {
    log "Testing the application..."
    
    # Test backend
    cd backend
    source venv/bin/activate
    
    # Run tests
    python manage.py test --verbosity=2
    
    cd ..
    
    # Test frontend
    cd frontend
    
    # Run tests
    npm test -- --watchAll=false
    
    cd ..
    
    success "Application testing completed"
}

# Create startup scripts
create_startup_scripts() {
    log "Creating startup scripts..."
    
    # Backend startup script
    cat > start_backend.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/backend"
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
EOF
    
    # Frontend startup script
    cat > start_frontend.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/frontend"
npm start
EOF
    
    # Celery worker startup script
    cat > start_celery.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/backend"
source venv/bin/activate
celery -A ipsas_financial worker --loglevel=info
EOF
    
    # Celery beat startup script
    cat > start_celery_beat.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/backend"
source venv/bin/activate
celery -A ipsas_financial beat --loglevel=info
EOF
    
    # Make scripts executable
    chmod +x start_backend.sh start_frontend.sh start_celery.sh start_celery_beat.sh
    
    success "Startup scripts created"
}

# Create systemd services (Linux only)
create_systemd_services() {
    if [[ "$OSTYPE" == "linux-gnu"* ]] && command -v systemctl &> /dev/null; then
        log "Creating systemd services..."
        
        # Backend service
        sudo tee /etc/systemd/system/ipsas-backend.service > /dev/null << EOF
[Unit]
Description=IPSAS Financial Backend
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$(pwd)/backend
Environment=PATH=$(pwd)/backend/venv/bin
ExecStart=$(pwd)/backend/venv/bin/gunicorn ipsas_financial.wsgi:application --bind 0.0.0.0:8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
        
        # Celery worker service
        sudo tee /etc/systemd/system/ipsas-celery.service > /dev/null << EOF
[Unit]
Description=IPSAS Financial Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$(pwd)/backend
Environment=PATH=$(pwd)/backend/venv/bin
ExecStart=$(pwd)/backend/venv/bin/celery -A ipsas_financial worker --loglevel=info
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
        
        # Enable services
        sudo systemctl daemon-reload
        sudo systemctl enable ipsas-backend
        sudo systemctl enable ipsas-celery
        
        success "Systemd services created and enabled"
    fi
}

# Display completion message
show_completion() {
    echo
    success "🎉 IPSAS Financial Software setup completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Start the application:"
    echo "   - Backend: ./start_backend.sh"
    echo "   - Frontend: ./start_frontend.sh"
    echo "   - Celery Worker: ./start_celery.sh"
    echo "   - Celery Beat: ./start_celery_beat.sh"
    echo
    echo "2. Access the application:"
    echo "   - Frontend: http://localhost:3000"
    echo "   - Backend API: http://localhost:8000"
    echo "   - Admin Interface: http://localhost:8000/admin"
    echo
    echo "3. Default credentials:"
    echo "   - Username: admin"
    echo "   - Password: (check the console output above)"
    echo
    echo "4. For production deployment, see docs/deployment.md"
    echo
}

# Main setup function
main() {
    echo "🚀 IPSAS Financial Software - Complete Setup"
    echo "============================================="
    echo
    
    # Check if not running as root
    check_root
    
    # Check system requirements
    check_system
    
    # Install dependencies
    install_dependencies
    
    # Install Docker
    install_docker
    
    # Setup services
    setup_postgresql
    setup_redis
    
    # Setup application
    setup_python
    setup_nodejs
    setup_environment
    
    # Run migrations
    run_migrations
    
    # Build frontend
    build_frontend
    
    # Test application
    test_application
    
    # Create startup scripts
    create_startup_scripts
    
    # Create systemd services (Linux only)
    create_systemd_services
    
    # Show completion message
    show_completion
}

# Run main function
main "$@"
