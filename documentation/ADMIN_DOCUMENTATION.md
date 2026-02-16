# Admin Panel Documentation - CyberVantage

This documentation provides guidance on how to manage users and perform administrative tasks in CyberVantage, both through the GUI and programmatically.

## Admin Panel GUI Features

### Accessing the Admin Panel

1. **Login as Admin User**: Use an account with admin privileges
2. **Navigate to Admin Panel**: Go to `/admin/users` or click on user management if available in the interface

### User Management Features

#### 1. View All Users
- **Location**: Admin Users page (`/admin/users`)
- **Features**: 
  - User statistics dashboard
  - Complete user list with ID, name, email, role, and registration date
  - Real-time user counts (Total, Admin, Regular users)

#### 2. Password Management
- **Reset User Password**: Click the "Reset Password" button next to any user
- **Features**:
  - Manual password entry with strength validation
  - Auto-generate secure passwords
  - Real-time password strength feedback
  - Confirmation matching validation

#### 3. User Role Management
- **Make Admin**: Promote regular users to admin status
- **Role Badges**: Visual indicators for user roles

#### 4. User Deletion
- **Delete User**: Remove user accounts (except your own)
- **Safety Features**: Confirmation prompts, referential integrity maintenance

## Coding/Backend Administration

### Database Schema Management

#### User Table Structure
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    encrypted_data BLOB,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    password_reset_token VARCHAR(255),
    password_reset_expires DATETIME
);
```

### Administrative Commands

#### 1. Create Admin User (Python Console)
```python
from models.database import User, db

# Create new admin user
admin_user = User(
    name="Admin Name",
    email="admin@example.com",
    is_admin=True
)
admin_user.set_password("SecurePassword123!")
db.session.add(admin_user)
db.session.commit()
```

#### 2. Promote Existing User to Admin
```python
from models.database import User, db

# Find and promote user
user = User.query.filter_by(email="user@example.com").first()
if user:
    user.is_admin = True
    db.session.commit()
    print(f"User {user.name} promoted to admin")
```

#### 3. Reset User Password Programmatically
```python
from models.database import User, db

# Reset password for user
user = User.query.filter_by(email="user@example.com").first()
if user:
    user.set_password("NewPassword123!")
    db.session.commit()
    print(f"Password reset for {user.name}")
```

#### 4. List All Users
```python
from models.database import User

# Get all users
users = User.query.all()
for user in users:
    role = "Admin" if user.is_admin else "User"
    print(f"ID: {user.id}, Name: {user.name}, Email: {user.email}, Role: {role}")
```

#### 5. Delete User Account
```python
from models.database import User, SimulationResponse, SimulationSession, db

# Delete user and related data
user = User.query.filter_by(email="user@example.com").first()
if user:
    # Delete related records first
    SimulationResponse.query.filter_by(user_id=user.id).delete()
    SimulationSession.query.filter_by(user_id=user.id).delete()
    
    # Delete user
    db.session.delete(user)
    db.session.commit()
    print(f"User {user.name} deleted successfully")
```

### Database Maintenance Commands

#### 1. Database Schema Updates
```python
from models.database import update_database_schema
from config.app_config import create_app

app = create_app()
with app.app_context():
    update_database_schema(app)
```

#### 2. Database Backup
```bash
# SQLite backup
sqlite3 users.db ".backup backup_$(date +%Y%m%d_%H%M%S).db"
```

#### 3. Database Integrity Check
```python
import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Check database integrity
cursor.execute("PRAGMA integrity_check")
result = cursor.fetchall()
print("Integrity check result:", result)

conn.close()
```

## Security Best Practices

### Password Management
1. **Strength Requirements**:
   - Minimum 8 characters
   - At least one uppercase letter
   - At least one lowercase letter  
   - At least one number
   - At least one special character

2. **Password Storage**: Uses bcrypt hashing with salts

### Admin Security
1. **Access Control**: Admin routes protected with `@admin_required` decorator
2. **Session Management**: JWT tokens with expiration
3. **CSRF Protection**: All forms include CSRF tokens
4. **Rate Limiting**: Login attempt restrictions

### Environment Security
```bash
# Required environment variables
FLASK_SECRET=your-secure-secret-key
JWT_SECRET=your-jwt-secret-key
CSRF_SECRET=your-csrf-secret-key
ENCRYPTION_KEY=your-fernet-encryption-key
DATABASE_URL=sqlite:///users.db
```

## API Endpoints

### Admin-Only Endpoints
- `POST /admin/reset_password/<user_id>` - Reset user password
- `POST /admin/make_admin/<user_id>` - Promote user to admin
- `POST /admin/delete_user/<user_id>` - Delete user account
- `GET /admin/users` - View all users

### Authentication Required
- `POST /extend_session` - Extend user session
- `GET /dashboard` - User dashboard
- `GET /learn` - Learning modules
- `GET /simulate` - Phishing simulation

## Troubleshooting

### Common Issues

1. **Database Lock Error**
   ```bash
   # Kill any processes using the database
   fuser users.db
   # Or restart the application
   ```

2. **Admin Access Denied**
   ```python
   # Check user admin status
   from models.database import User
   user = User.query.filter_by(email="your@email.com").first()
   print(f"Is admin: {user.is_admin}")
   ```

3. **Session Timeout Issues**
   - Check JWT token expiration (default: 1 hour)
   - Use session extension endpoint if needed

### Logs and Monitoring
- Application logs: Check console output
- Database operations: Monitor DB query logs
- User activities: Check simulation and response tables

## Deployment Considerations

### Production Setup
1. **Database**: Migrate from SQLite to PostgreSQL/MySQL for production
2. **Security Keys**: Generate strong, unique keys for production
3. **HTTPS**: Enable SSL/TLS encryption
4. **Backup Strategy**: Implement automated database backups
5. **Monitoring**: Set up application performance monitoring

### Environment Configuration
```bash
# Production environment
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@localhost/cybervantage
```

This documentation covers the complete admin functionality available in CyberVantage, both through the GUI and programmatic interfaces.