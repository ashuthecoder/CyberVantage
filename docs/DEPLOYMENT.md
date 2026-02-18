# CyberVantage Deployment Guide

This guide covers deploying CyberVantage to production with Azure PostgreSQL database (required).

## ⚠️ IMPORTANT: Azure Database Required

CyberVantage **requires** an Azure PostgreSQL database. SQLite is not supported.

You must configure one of these environment variables:
- `DATABASE_URL`
- `POSTGRES_URL`  
- `POSTGRES_PRISMA_URL`
- `POSTGRES_URL_NON_POOLING`

See [Azure Database Setup Guide](./AZURE_DATABASE_SETUP.md) for instructions.

## Quick Start

### Prerequisites

1. **Azure PostgreSQL Database** (Required)
   - Create an Azure PostgreSQL server
   - Or use Vercel Postgres (Neon)
   - Get connection string

2. **API Keys**
   - Google Gemini API key (required for AI features)
   - Azure OpenAI key (optional fallback)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/ujwwal/CyberVantage.git
   cd CyberVantage
   ```

2. **Setup Azure PostgreSQL**
   
   Follow [Azure Database Setup Guide](./AZURE_DATABASE_SETUP.md) to create your database.

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Azure database connection string
   # REQUIRED: Set DATABASE_URL or POSTGRES_URL
   ```

5. **Run the application**
   ```bash
   python main.py
   ```
   
   If you see an error about database configuration, ensure you've set DATABASE_URL in your .env file.

### Production Deployment (Vercel + Azure Database)

#### Step 1: Setup Azure PostgreSQL Database

Follow the [Azure Database Setup Guide](./AZURE_DATABASE_SETUP.md) to:
- Create Azure PostgreSQL server
- Configure firewall rules
- Get connection string

#### Step 2: Deploy to Vercel

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy**
   ```bash
   vercel
   ```

4. **Configure Environment Variables**
   
   In Vercel Dashboard, add these environment variables:
   
   **Required:**
   - `DATABASE_URL` - Your Azure PostgreSQL connection string
   - `SECRET_KEY` - Random secure string for Flask
   - `JWT_SECRET_KEY` - Random secure string for JWT
   - `GOOGLE_API_KEY` - Google Gemini API key
   
   **Optional:**
   - `AZURE_OPENAI_KEY` - Azure OpenAI API key (fallback)
   - `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint
   - `VIRUSTOTAL_API_KEY` - VirusTotal API key for threat intelligence
   - `RESEND_API_KEY` - Resend API key for emails
   - `RESEND_FROM_EMAIL` - From email address

5. **Set Production Environment**
   ```bash
   vercel env add FLASK_ENV production
   ```

6. **Deploy to Production**
   ```bash
   vercel --prod
   ```

## Database Configuration

### Connection String Format

The application automatically detects and supports multiple database configurations:

```bash
# Priority order (first found is used):
1. DATABASE_URL
2. POSTGRES_URL
3. POSTGRES_PRISMA_URL
4. POSTGRES_URL_NON_POOLING
5. DATABASE_URL_UNPOOLED
```

### Azure PostgreSQL

```bash
DATABASE_URL=postgresql://username:password@servername.postgres.database.azure.com:5432/dbname?sslmode=require
```

### Vercel Postgres (Neon)

Vercel automatically configures these when you add Postgres storage:
```bash
POSTGRES_URL=postgres://...
POSTGRES_PRISMA_URL=postgres://...
POSTGRES_URL_NON_POOLING=postgres://...
```

The app will use them automatically!

## Environment Variables

### Security Keys

Generate secure keys:
```bash
# Flask secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# JWT secret key  
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Encryption key (for sensitive data)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### AI Provider Configuration

**Primary: Google Gemini (Recommended)**
```bash
PRIMARY_AI_MODEL=gemini
GOOGLE_API_KEY=your-google-api-key
```

**Fallback: Azure OpenAI**
```bash
AZURE_OPENAI_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/...
```

## Database Migration

### Initial Setup

On first deployment, tables are created automatically. The app runs:
1. `db.create_all()` - Creates all tables
2. `update_database_schema()` - Adds any missing columns

### Schema Updates

The app automatically detects the database type and runs appropriate migrations:

```python
# PostgreSQL
ALTER TABLE "user" ADD COLUMN demographics_completed BOOLEAN DEFAULT FALSE NOT NULL

# SQLite  
ALTER TABLE user ADD COLUMN demographics_completed BOOLEAN DEFAULT 0 NOT NULL
```

### Manual Migration

If needed, run migrations manually:

```python
from main import app, db
from models.database import update_database_schema

with app.app_context():
    db.create_all()
    update_database_schema(app)
```

## Health Checks

### Verify Deployment

```bash
# Check if app is running
curl https://your-app.vercel.app/

# Check database connection
# Login to app and verify dashboard loads
```

### Monitor Logs

```bash
# View deployment logs
vercel logs

# View production logs
vercel logs --prod
```

## Troubleshooting

### Database Connection Issues

**Problem**: "connection refused"

**Solutions**:
1. Check Azure firewall rules
2. Verify connection string is correct
3. Ensure SSL mode is set
4. Check Azure database is running

**Problem**: "SSL connection required"

**Solution**: Add `?sslmode=require` to connection string

### Schema Issues

**Problem**: "column does not exist"

**Solution**: 
1. Check logs for migration errors
2. Manually run schema update
3. Verify database user has ALTER TABLE permissions

### Performance Issues

**Problem**: Slow database queries

**Solutions**:
1. Use connection pooling
2. Add database indexes
3. Enable query caching
4. Scale Azure database tier

## Security Checklist

Before going to production:

- [ ] Set all required environment variables
- [ ] Use strong, unique secrets for all keys
- [ ] Enable SSL for database connections
- [ ] Configure Azure firewall rules
- [ ] Set up automated database backups
- [ ] Enable HTTPS (Vercel does this automatically)
- [ ] Review security headers in `app_config.py`
- [ ] Test authentication and authorization
- [ ] Verify CSRF protection is enabled
- [ ] Check for exposed secrets in logs

## Scaling

### Database Scaling

1. **Vertical Scaling**
   - Increase Azure PostgreSQL tier
   - More CPU/memory for better performance

2. **Connection Pooling**
   - Use PgBouncer
   - Configure in Vercel Postgres
   - Set appropriate pool size

3. **Read Replicas**
   - Use for read-heavy operations
   - Separate read and write operations

### Application Scaling

Vercel automatically scales:
- Handles traffic spikes
- Multiple regions
- CDN for static assets

## Monitoring

### Application Monitoring

1. **Vercel Analytics**
   - Request count
   - Response times
   - Error rates

2. **Azure Portal**
   - Database metrics
   - Connection count
   - Query performance

3. **Custom Logging**
   - Check `logs/` directory
   - Monitor simulation activity
   - Track API usage

## Backup and Recovery

### Automated Backups

Azure PostgreSQL provides:
- Automated backups (7-35 days retention)
- Point-in-time restore
- Geo-redundant backup

### Manual Backup

```bash
# Export database
pg_dump -h servername.postgres.database.azure.com \
        -U username \
        -d dbname > backup.sql

# Import database
psql -h servername.postgres.database.azure.com \
     -U username \
     -d dbname < backup.sql
```

## Support

For issues:
1. Check [AZURE_DATABASE_SETUP.md](./AZURE_DATABASE_SETUP.md)
2. Review application logs
3. Check Vercel deployment logs
4. Open an issue on GitHub

## References

- [Vercel Documentation](https://vercel.com/docs)
- [Azure PostgreSQL Documentation](https://docs.microsoft.com/azure/postgresql/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org/)
