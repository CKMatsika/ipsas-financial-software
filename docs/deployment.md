# IPSAS Financial Software - Deployment Guide

This guide provides comprehensive instructions for deploying the IPSAS Financial Software in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start with Docker](#quick-start-with-docker)
3. [Manual Installation](#manual-installation)
4. [Production Deployment](#production-deployment)
5. [Configuration](#configuration)
6. [Database Setup](#database-setup)
7. [Security Considerations](#security-considerations)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+), Windows 10+, macOS 10.15+
- **CPU**: 2+ cores, 2.0+ GHz
- **Memory**: 4GB RAM minimum, 8GB+ recommended
- **Storage**: 20GB+ available disk space
- **Network**: Stable internet connection for initial setup

### Software Requirements

- **Docker**: 20.10+ (for containerized deployment)
- **Docker Compose**: 2.0+
- **PostgreSQL**: 12+ (if not using Docker)
- **Redis**: 6.0+ (if not using Docker)
- **Node.js**: 16+ (for frontend development)
- **Python**: 3.8+ (for backend development)

## Quick Start with Docker

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ipsas-financial-software
```

### 2. Environment Configuration

Copy the environment template and configure it:

```bash
cp backend/env.example backend/.env
# Edit backend/.env with your configuration
```

### 3. Start the Application

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Admin Interface**: http://localhost:8000/admin
- **Database**: localhost:5432

## Manual Installation

### Backend Setup

#### 1. Python Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Database Setup

```bash
# Create PostgreSQL database
sudo -u postgres createdb ipsas_financial
sudo -u postgres createuser ipsas_user

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic
```

#### 3. Start Backend Services

```bash
# Start Django development server
python manage.py runserver

# Start Celery worker (in separate terminal)
celery -A ipsas_financial worker --loglevel=info

# Start Celery beat (in separate terminal)
celery -A ipsas_financial beat --loglevel=info
```

### Frontend Setup

#### 1. Install Dependencies

```bash
cd frontend
npm install
```

#### 2. Start Development Server

```bash
npm start
```

## Production Deployment

### Docker Production Setup

#### 1. Production Environment

```bash
# Create production environment file
cp backend/env.example backend/.env.prod

# Edit production settings
nano backend/.env.prod
```

#### 2. Production Docker Compose

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Production Setup

#### 1. Web Server Configuration

**Nginx Configuration**:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Frontend
    location / {
        root /var/www/ipsas-frontend;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Admin interface
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 2. Gunicorn Configuration

Create `gunicorn.conf.py`:

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
```

#### 3. Systemd Services

**Backend Service** (`/etc/systemd/system/ipsas-backend.service`):

```ini
[Unit]
Description=IPSAS Financial Backend
After=network.target

[Service]
Type=notify
User=ipsas
Group=ipsas
WorkingDirectory=/opt/ipsas/backend
Environment=PATH=/opt/ipsas/backend/venv/bin
ExecStart=/opt/ipsas/backend/venv/bin/gunicorn ipsas_financial.wsgi:application -c gunicorn.conf.py
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

**Celery Worker Service** (`/etc/systemd/system/ipsas-celery.service`):

```ini
[Unit]
Description=IPSAS Financial Celery Worker
After=network.target

[Service]
Type=simple
User=ipsas
Group=ipsas
WorkingDirectory=/opt/ipsas/backend
Environment=PATH=/opt/ipsas/backend/venv/bin
ExecStart=/opt/ipsas/backend/venv/bin/celery -A ipsas_financial worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Django secret key | - | Yes |
| `DEBUG` | Debug mode | False | No |
| `ALLOWED_HOSTS` | Allowed hostnames | localhost | Yes |
| `DB_NAME` | Database name | ipsas_financial | Yes |
| `DB_USER` | Database user | postgres | Yes |
| `DB_PASSWORD` | Database password | - | Yes |
| `DB_HOST` | Database host | localhost | Yes |
| `DB_PORT` | Database port | 5432 | Yes |
| `REDIS_URL` | Redis connection URL | redis://localhost:6379/0 | Yes |

### Database Configuration

#### PostgreSQL Optimization

```sql
-- Increase shared buffers
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Reload configuration
SELECT pg_reload_conf();
```

#### Connection Pooling

Install and configure PgBouncer:

```ini
[databases]
ipsas_financial = host=127.0.0.1 port=5432 dbname=ipsas_financial

[pgbouncer]
listen_port = 6432
listen_addr = 127.0.0.1
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
```

## Database Setup

### Initial Data Setup

#### 1. Chart of Accounts

```bash
# Create default account categories
python manage.py shell
```

```python
from chart_of_accounts.models import AccountCategory, AccountGroup, AccountType

# Create categories
categories = [
    {'name': 'Assets', 'code': 'A', 'category_type': 'assets'},
    {'name': 'Liabilities', 'code': 'L', 'category_type': 'liabilities'},
    {'name': 'Equity', 'code': 'E', 'category_type': 'equity'},
    {'name': 'Revenue', 'code': 'R', 'category_type': 'revenue'},
    {'name': 'Expenses', 'code': 'X', 'category_type': 'expenses'},
]

for cat_data in categories:
    AccountCategory.objects.get_or_create(**cat_data)
```

#### 2. User Roles

```python
from accounts.models import User

# Create admin user
admin_user = User.objects.create_superuser(
    username='admin',
    email='admin@example.com',
    password='secure_password_here',
    role='admin'
)
```

### Data Migration

#### 1. Export/Import Data

```bash
# Export data
python manage.py dumpdata > backup.json

# Import data
python manage.py loaddata backup.json
```

#### 2. Database Backup

```bash
# Create backup
pg_dump ipsas_financial > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
psql ipsas_financial < backup_file.sql
```

## Security Considerations

### 1. SSL/TLS Configuration

```bash
# Generate SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. Firewall Configuration

```bash
# UFW firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. Database Security

```sql
-- Create read-only user
CREATE USER ipsas_readonly WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE ipsas_financial TO ipsas_readonly;
GRANT USAGE ON SCHEMA public TO ipsas_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ipsas_readonly;
```

### 4. Application Security

```python
# settings.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

## Monitoring and Maintenance

### 1. Log Management

```bash
# Log rotation
sudo nano /etc/logrotate.d/ipsas

/var/log/ipsas/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 ipsas ipsas
    postrotate
        systemctl reload ipsas-backend
    endscript
}
```

### 2. Health Checks

```bash
# Health check script
#!/bin/bash
curl -f http://localhost:8000/api/health/ || exit 1
```

### 3. Performance Monitoring

Install and configure monitoring tools:

- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **AlertManager**: Alerting

### 4. Backup Strategy

```bash
#!/bin/bash
# Daily backup script
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/ipsas"

# Database backup
pg_dump ipsas_financial > "$BACKUP_DIR/db_$DATE.sql"

# File backup
tar -czf "$BACKUP_DIR/files_$DATE.tar.gz" /opt/ipsas/media

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U ipsas_user -d ipsas_financial

# Check logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### 2. Celery Issues

```bash
# Check Celery status
celery -A ipsas_financial inspect active

# Restart Celery
sudo systemctl restart ipsas-celery

# Check Redis connection
redis-cli ping
```

#### 3. Frontend Build Issues

```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version
npm --version
```

### Performance Issues

#### 1. Database Performance

```sql
-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### 2. Application Performance

```bash
# Check memory usage
free -h

# Check CPU usage
top

# Check disk usage
df -h

# Check network connections
netstat -tulpn
```

### Support and Resources

- **Documentation**: [Project Wiki](link-to-wiki)
- **Issue Tracker**: [GitHub Issues](link-to-issues)
- **Community**: [Discord/Slack](link-to-community)
- **Email Support**: support@ipsas-financial.com

## Conclusion

This deployment guide covers the essential aspects of deploying the IPSAS Financial Software. For additional support or specific configurations, please refer to the project documentation or contact the development team.

Remember to:
- Always test in a staging environment first
- Keep backups of your data and configuration
- Monitor system performance and logs
- Keep the system updated with security patches
- Document any custom configurations
