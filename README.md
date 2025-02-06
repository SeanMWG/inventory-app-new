# IT Inventory Management System

A modern, secure, and scalable application for managing IT hardware inventory, built with Flask and Azure services.

## Features

- Azure AD Authentication
- Hardware inventory management
- Location and space tracking
- Audit logging
- Loaner equipment tracking
- Role-based access control

## Technology Stack

- **Backend**: Python 3.11, Flask
- **Database**: Azure SQL Database
- **Authentication**: Azure AD
- **Monitoring**: Application Insights
- **Infrastructure**: Azure App Service, Terraform

## Project Structure

```
inventory-app/
├── src/                  # Application source code
├── tests/               # Test files
├── migrations/          # Database migrations
├── docs/               # Documentation
├── infrastructure/     # Infrastructure as code
├── static/            # Static files (CSS, JS)
└── templates/         # HTML templates
```

## Setup

1. **Prerequisites**
   - Python 3.11+
   - Azure CLI
   - SQL Server ODBC Driver 18
   - Terraform (for infrastructure)

2. **Environment Setup**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   .\venv\Scripts\activate   # Windows

   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configuration**
   Create a `.env` file in the root directory:
   ```
   FLASK_APP=src/app.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key
   DATABASE_URL=your-database-url
   CLIENT_ID=your-azure-client-id
   CLIENT_SECRET=your-azure-client-secret
   TENANT_ID=your-azure-tenant-id
   ```

4. **Database Setup**
   ```bash
   # Apply migrations
   flask db upgrade
   ```

5. **Running the Application**
   ```bash
   # Development
   flask run

   # Production
   gunicorn "src.app:create_app()"
   ```

## Development

1. **Creating Database Migrations**
   ```bash
   flask db migrate -m "Description of changes"
   flask db upgrade
   ```

2. **Running Tests**
   ```bash
   pytest
   ```

3. **Code Quality**
   ```bash
   # Format code
   black .

   # Lint code
   flake8

   # Type checking
   mypy .
   ```

## Deployment

1. **Infrastructure Setup**
   ```bash
   cd infrastructure/terraform
   terraform init
   terraform plan
   terraform apply
   ```

2. **Application Deployment**
   - Automated via GitHub Actions
   - Manual deployment available through Azure CLI

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## Security

- All sensitive data is stored in Azure Key Vault
- Authentication handled by Azure AD
- HTTPS enforced in production
- Regular security audits
- Comprehensive audit logging

## License

This project is proprietary and confidential.

## Support

Contact IT Support for assistance.
# Updated: Thu, Feb  6, 2025 12:30:20 PM
