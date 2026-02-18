# Azure Database Required

## Important Notice

CyberVantage **requires** an Azure PostgreSQL database to run. SQLite is not supported.

## Why Azure Database Only?

This application is designed for production deployment with enterprise-grade database requirements:

1. **Scalability**: Azure PostgreSQL handles multiple concurrent users
2. **Security**: Built-in SSL/TLS encryption and advanced security features
3. **Reliability**: Automated backups and high availability
4. **Performance**: Optimized for production workloads
5. **Compliance**: Meets enterprise security and compliance standards

## Quick Setup

### Option 1: Azure PostgreSQL (Recommended)

1. **Create Database**
   ```bash
   az postgres flexible-server create \
     --resource-group myResourceGroup \
     --name cybervantage-db \
     --location eastus \
     --admin-user dbadmin \
     --admin-password <SecurePassword> \
     --sku-name Standard_B1ms \
     --tier Burstable \
     --version 14
   ```

2. **Configure Firewall**
   ```bash
   # Allow Azure services
   az postgres flexible-server firewall-rule create \
     --resource-group myResourceGroup \
     --name cybervantage-db \
     --rule-name AllowAzureServices \
     --start-ip-address 0.0.0.0 \
     --end-ip-address 0.0.0.0
   ```

3. **Get Connection String**
   - Navigate to Azure Portal → Your PostgreSQL server
   - Go to "Connection strings"
   - Copy the connection string

4. **Set Environment Variable**
   ```bash
   export DATABASE_URL="postgresql://dbadmin:password@cybervantage-db.postgres.database.azure.com:5432/postgres?sslmode=require"
   ```

### Option 2: Vercel Postgres (Easiest)

If deploying on Vercel:

1. Go to your Vercel project dashboard
2. Navigate to **Storage** tab
3. Click **Create Database**
4. Select **Postgres**
5. Follow the prompts

Vercel automatically sets `POSTGRES_URL` and related environment variables.

### Option 3: Local PostgreSQL for Development

If you need to run locally for development:

1. **Install PostgreSQL**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # macOS
   brew install postgresql
   
   # Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

2. **Create Database**
   ```bash
   sudo -u postgres psql
   CREATE DATABASE cybervantage;
   CREATE USER cybervantage_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE cybervantage TO cybervantage_user;
   \q
   ```

3. **Set Connection String**
   ```bash
   export DATABASE_URL="postgresql://cybervantage_user:your_password@localhost:5432/cybervantage"
   ```

## Environment Variable Format

The application accepts database configuration in multiple formats:

```bash
# Standard PostgreSQL URL (recommended)
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require

# Vercel-style variables (auto-configured on Vercel)
POSTGRES_URL=postgres://user:password@host:5432/dbname
POSTGRES_PRISMA_URL=postgres://user:password@host:5432/dbname?pgbouncer=true
POSTGRES_URL_NON_POOLING=postgres://user:password@host:5432/dbname
```

**Priority Order:**
1. `DATABASE_URL`
2. `POSTGRES_URL`
3. `POSTGRES_PRISMA_URL`
4. `POSTGRES_URL_NON_POOLING`
5. `DATABASE_URL_UNPOOLED`

The first variable found will be used.

## Error Messages

### "No database configuration found"

This error means no database connection string was provided.

**Solution:**
```bash
# Set one of these in your .env file or environment:
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require
```

### "connection refused" or "could not connect to server"

**Possible causes:**
1. Database server is not running
2. Firewall rules are blocking connection
3. Incorrect host/port in connection string

**Solution:**
1. Verify database server is running
2. Check Azure firewall rules allow your IP
3. Verify connection string is correct

### "SSL connection required"

**Solution:**
Add `?sslmode=require` to your connection string:
```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require
```

## Testing Database Connection

Test your database connection before running the app:

```python
from sqlalchemy import create_engine, text

DATABASE_URL = "your-connection-string-here"
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        print(f"✅ Connected to: {result.fetchone()[0]}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

## Free Tier Options

If you don't want to pay for Azure PostgreSQL:

1. **Vercel Postgres (Neon)** - Free tier available
   - 0.5 GB storage
   - 60 hours compute per month
   - Perfect for testing/small projects

2. **Neon.tech** - Generous free tier
   - 3 GB storage
   - Unlimited compute hours
   - PostgreSQL compatible

3. **Supabase** - Free tier available
   - 500 MB storage
   - PostgreSQL with additional features

4. **Azure PostgreSQL** - Free credits
   - $200 Azure credit for new accounts
   - Use for 12 months

## Migration from SQLite

If you have existing SQLite data:

1. **Export from SQLite**
   ```bash
   sqlite3 users.db .dump > backup.sql
   ```

2. **Clean SQL for PostgreSQL**
   ```bash
   # Remove SQLite-specific syntax
   sed -i 's/AUTOINCREMENT/SERIAL/g' backup.sql
   sed -i 's/INTEGER PRIMARY KEY/SERIAL PRIMARY KEY/g' backup.sql
   ```

3. **Import to PostgreSQL**
   ```bash
   psql $DATABASE_URL < backup.sql
   ```

## Support

For detailed setup instructions, see:
- [Azure Database Setup Guide](./AZURE_DATABASE_SETUP.md)
- [Deployment Guide](./DEPLOYMENT.md)

For issues:
- Check connection string format
- Verify firewall rules
- Test connection with `psql` command
- Check Azure Portal for database status
