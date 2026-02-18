# Azure Database Setup Guide

This guide explains how to configure CyberVantage to work with Azure PostgreSQL databases.

## Prerequisites

- Azure account with active subscription
- Azure PostgreSQL Flexible Server or Azure Database for PostgreSQL

## Database Configuration

### Option 1: Azure PostgreSQL (Recommended)

1. **Create Azure PostgreSQL Database**
   ```bash
   # Using Azure CLI
   az postgres flexible-server create \
     --resource-group myResourceGroup \
     --name myserver \
     --location eastus \
     --admin-user myadmin \
     --admin-password <password> \
     --sku-name Standard_B1ms \
     --tier Burstable \
     --version 14
   ```

2. **Configure Firewall Rules**
   ```bash
   # Allow Azure services
   az postgres flexible-server firewall-rule create \
     --resource-group myResourceGroup \
     --name myserver \
     --rule-name AllowAzureServices \
     --start-ip-address 0.0.0.0 \
     --end-ip-address 0.0.0.0
   ```

3. **Get Connection String**
   - Navigate to your PostgreSQL server in Azure Portal
   - Go to "Connection strings" under Settings
   - Copy the connection string

4. **Set Environment Variable**
   
   Add to your `.env` file or Vercel environment variables:
   ```bash
   # Direct connection (for non-pooled operations)
   DATABASE_URL=postgresql://username:password@servername.postgres.database.azure.com:5432/dbname?sslmode=require
   
   # Or use Vercel-style variables
   POSTGRES_URL=postgres://username:password@servername.postgres.database.azure.com:5432/dbname
   ```

### Option 2: Vercel Postgres (Neon)

If deploying on Vercel with Vercel Postgres:

1. **Add Vercel Postgres to your project**
   - Go to your Vercel project
   - Navigate to Storage tab
   - Create a new Postgres database

2. **Environment Variables are Auto-Configured**
   Vercel automatically sets these variables:
   - `POSTGRES_URL` - Pooled connection
   - `POSTGRES_PRISMA_URL` - Prisma connection
   - `POSTGRES_URL_NON_POOLING` - Direct connection
   - `DATABASE_URL` - Main connection URL

   The app will automatically use these variables.

## Database Features

### Automatic SSL/TLS

The application automatically adds `sslmode=require` for PostgreSQL connections to ensure encrypted communication with Azure databases.

### Connection String Format

The app supports multiple connection string formats:

```bash
# PostgreSQL standard
postgresql://user:pass@host:5432/dbname

# Postgres short form (auto-converted)
postgres://user:pass@host:5432/dbname

# With SSL mode
postgresql://user:pass@host:5432/dbname?sslmode=require

# With connection pooling (PgBouncer)
postgres://user:pass@host:5432/dbname?pgbouncer=true
```

### Schema Migration

The application automatically:
- Creates tables on first run
- Adds missing columns via `update_database_schema()`
- Detects database type (PostgreSQL vs SQLite)
- Uses appropriate SQL syntax for each database type

### Database Type Detection

The schema update function automatically detects the database type and uses appropriate SQL:

- **PostgreSQL**: Uses `"user"` (quoted) table name and `FALSE` for booleans
- **SQLite**: Uses `user` (unquoted) and `0` for booleans

## Connection Pooling

For production deployments with Azure PostgreSQL:

1. **Use Connection Pooling**
   - Azure Database for PostgreSQL supports built-in connection pooling
   - Or use PgBouncer for external connection pooling
   - Configure `POSTGRES_PRISMA_URL` for pooled connections

2. **Connection Limits**
   - Set appropriate `pool_size` in SQLAlchemy if needed
   - Default is 5 connections per instance

## Security Best Practices

1. **Use SSL/TLS**
   - Always use `sslmode=require` in production
   - The app adds this automatically if not present

2. **Secure Credentials**
   - Store credentials in environment variables
   - Use Azure Key Vault for sensitive data
   - Never commit credentials to git

3. **Firewall Rules**
   - Restrict database access to known IP ranges
   - Use VNet integration for better security

4. **Backup and Recovery**
   - Enable automated backups in Azure Portal
   - Configure point-in-time restore
   - Test restore procedures regularly

## Troubleshooting

### Connection Issues

**Problem**: `connection refused` or `timeout`
**Solution**:
- Check firewall rules in Azure Portal
- Verify SSL mode is set correctly
- Ensure credentials are correct

**Problem**: `SSL connection required`
**Solution**:
- Add `?sslmode=require` to connection string
- Or set `POSTGRES_SSLMODE=require` environment variable

**Problem**: `too many connections`
**Solution**:
- Use connection pooling
- Reduce number of app instances
- Increase max_connections in Azure Portal

### Schema Issues

**Problem**: `column does not exist`
**Solution**:
- Restart the application to run schema updates
- Check logs for schema migration errors
- Manually run `update_database_schema()` if needed

## Testing Database Connection

Test your database connection:

```python
from main import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # Test connection
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            print(f"Connected to: {result.fetchone()[0]}")
            print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
```

## Monitoring

Monitor your Azure PostgreSQL database:

1. **Azure Portal Metrics**
   - Connection count
   - CPU/Memory usage
   - Storage usage
   - Query performance

2. **Application Logs**
   - Check Flask logs for database errors
   - Monitor slow queries
   - Track connection pool usage

## Performance Optimization

1. **Indexes**
   - Add indexes on frequently queried columns
   - Email, user_id, created_at are good candidates

2. **Query Optimization**
   - Use SELECT with specific columns
   - Avoid N+1 queries
   - Use pagination for large result sets

3. **Caching**
   - Cache frequently accessed data
   - Use Redis for session storage
   - Implement query result caching

## Migration from SQLite

To migrate from SQLite to Azure PostgreSQL:

1. **Export data from SQLite**
   ```bash
   sqlite3 users.db .dump > backup.sql
   ```

2. **Create PostgreSQL database**
   ```bash
   createdb cybervantage
   ```

3. **Update connection string**
   ```bash
   DATABASE_URL=postgresql://user:pass@host:5432/cybervantage
   ```

4. **Run the application**
   - Tables will be created automatically
   - Import data if needed

5. **Verify data migration**
   - Check all tables exist
   - Verify record counts
   - Test application functionality
