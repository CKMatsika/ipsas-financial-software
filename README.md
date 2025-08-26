# IPSAS Financial Statements Software

A comprehensive web-based financial statements software that fully adheres to International Public Sector Accounting Standards (IPSAS) and the Zimbabwe Financial Reporting Manual for Public Sector Accounts.

## 🎯 Core Features

### IPSAS Compliance
- **Statement of Financial Position** - Automated balance sheet generation
- **Statement of Financial Performance** - Income statement with IPSAS standards
- **Statement of Cash Flows** - Cash flow analysis and reporting
- **Statement of Changes in Net Assets** - Comprehensive net asset tracking
- **Property, Plant & Equipment Schedule** - Asset management and depreciation
- **Investment Property Schedule** - Investment property tracking
- **Budget vs Actuals Report** - Variance analysis and reporting
- **Segment Financial Position & Performance** - Multi-segment reporting
- **Consolidated Accounts** - Group consolidation capabilities

### Automation & Efficiency
- Automatic IPSAS requirement updates
- Trial balance import from external systems
- Continuity across all statements and disclosures
- Automated report generation
- Roll-forward logic for period transitions
- Full audit trail for journal entries

### Integration & Compatibility
- ERP system compatibility (PROMUN, LADS, etc.)
- Multi-GL system aggregation
- Reconciliation engine with audit traceability
- Zimbabwe-specific reporting formats

### User Features
- Configurable financial statement templates
- Real-time dashboards
- Drill-down capabilities
- Multi-user role management
- Multi-entity consolidation

## 🏗️ System Architecture

- **Backend**: Django REST API with PostgreSQL
- **Frontend**: React with TailwindCSS
- **Database**: PostgreSQL with financial data integrity
- **Security**: Role-based access control, encryption, audit trails
- **Deployment**: Docker, Kubernetes, on-premise support

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Docker (optional)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Database Setup
```bash
cd database
# Follow PostgreSQL setup instructions
```

## 📚 Documentation

- [System Setup & Deployment](docs/deployment.md)
- [User Manual & Training](docs/docs/user-manual.md)
- [API Documentation](docs/docs/api.md)
- [IPSAS Compliance Guide](docs/docs/ipsas-compliance.md)

## 🔒 Security Features

- Role-based access control (Admin, Accountant, Auditor, Viewer)
- Encrypted data storage
- Full audit trails
- Multi-factor authentication support

## 📊 Export Capabilities

- Excel (.xlsx)
- PDF reports
- CSV data export
- Custom report templates

## 🌍 Zimbabwe Compliance

- Zimbabwe Financial Reporting Manual alignment
- Local transaction recognition and measurement
- Zimbabwe-specific disclosure requirements
- Local regulatory compliance tools

## 🤝 Training & Support

- Built-in training modules
- Interactive tutorials
- Sample datasets
- Help guides and documentation

## 📝 License

This software is developed for public sector use and compliance with international accounting standards.

---

**Built with ❤️ for Public Sector Financial Excellence**
