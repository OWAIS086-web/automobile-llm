# Dealership Management System

A comprehensive dealership management system integrated with the existing AI chatbot platform. This system provides complete vehicle lifecycle tracking, service management, and analytics for automotive dealerships.

## 🚀 Features

### Core Functionality
- **VIN-based Vehicle Tracking**: Complete vehicle history from factory to customer
- **Pre-Delivery Inspection (PDI)**: Track PDI reports with objection management
- **Free Service Management**: FFS (1000km) and SFS (5000km) inspection tracking
- **Warranty Claims**: Comprehensive warranty claim management with AI analysis
- **Campaign Management**: Service campaigns and recall management
- **Repair Orders**: Complete RO lifecycle management
- **Analytics & Reporting**: Visual insights and performance metrics

### AI Integration
- **Problem Analysis**: AI-powered analysis of warranty claims and repair descriptions
- **Cause Analysis**: Intelligent root cause analysis for recurring issues
- **Enrichment**: Automatic categorization and tagging of service records
- **Chat Integration**: Ask questions about dealership data through the AI chatbot

## 📊 System Architecture

### Database Schema
The system uses SQLite with the following main tables:

- `vehicles` - Master vehicle data
- `dealerships` - Dealership information
- `warranty_claims` - Warranty claim records
- `campaigns` - Service campaigns
- `campaign_services` - Campaign service records
- `pdi_inspections` - Pre-delivery inspections
- `ffs_inspections` - First free service inspections
- `sfs_inspections` - Second free service inspections
- `repair_orders` - Repair order records

### Key Components

#### Models (`models/dealership.py`)
- `DealershipDatabase` - Database initialization and management
- `WarrantyClaim` - Warranty claim operations
- `CampaignService` - Campaign management
- `InspectionService` - Inspection operations
- `RepairOrder` - Repair order management

#### Controllers (`controllers/dealership.py`)
- Route handlers for all dealership pages
- API endpoints for data retrieval
- Business logic implementation

#### Frontend
- **Templates**: Modern responsive HTML templates with purple theme
- **CSS**: Comprehensive styling with dark/light mode support
- **JavaScript**: Interactive features, charts, and data management

## 🛠️ Installation & Setup

### 1. Database Initialization
The database is automatically initialized when the system starts. Tables are created with proper indexes for optimal performance.

### 2. Sample Data Population
To populate the system with sample data for demonstration:

```bash
python seed_dealership_data.py
```

This will create:
- 6 Dealerships (Haval Central, Lahore, Karachi, etc.)
- 100 Sample Vehicles
- 80 PDI Inspections (with some objections)
- 50 Warranty Claims
- 4 Service Campaigns with 100 services
- 60 FFS Inspections
- 40 SFS Inspections
- 30 Repair Orders

### 3. Access the System
Navigate to `/dealership` in your browser to access the main dashboard.

## 📱 User Interface

### Dashboard (`/dealership`)
- Quick statistics overview
- Recent activity feed
- Quick actions (VIN search, new claims, reports)
- Navigation to all sections

### Warranty Claims (`/dealership/warranty-claims`)
- Filter by VIN, dealership, date range, claim type
- Most complained VINs analysis
- Dealership performance comparison
- Export functionality

### Campaign Reports (`/dealership/campaign-reports`)
- Campaign service tracking
- Dealership participation analysis
- Service completion rates
- Campaign type distribution

### FFS Inspections (`/dealership/ffs-inspections`)
- First free service tracking
- Odometer reading validation
- Findings and recommendations
- Dealership performance metrics

### SFS Inspections (`/dealership/sfs-inspections`)
- Second free service tracking
- Service completion rates
- Monthly trends analysis
- Car model distribution

### PDI Inspections (`/dealership/pdi-inspections`)
- Pre-delivery inspection reports
- Objection tracking and analysis
- Delivery status management
- Quality control metrics

### Repair Orders (`/dealership/repair-orders`)
- Complete RO lifecycle management
- Customer information tracking
- Parts and labor cost analysis
- Warranty vs non-warranty breakdown

### VIN History (`/dealership/vin-history`)
- Complete vehicle service timeline
- All inspections, claims, and services
- Visual timeline representation
- Service summary statistics

## 📈 Analytics & Insights

### Key Metrics Tracked
- **Quality Control**: PDI objection rates and patterns
- **Service Efficiency**: Turnaround times and completion rates
- **Customer Satisfaction**: Service quality indicators
- **Revenue Analysis**: Parts, labor, and total service revenue
- **Dealership Performance**: Comparative analysis across locations

### Visual Analytics
- Interactive charts using Chart.js
- Responsive design for all screen sizes
- Real-time data updates
- Export capabilities for reports

## 🔍 Search & Filtering

### VIN Search
- 17-character VIN validation
- Complete vehicle history retrieval
- Cross-reference all service records
- Timeline visualization

### Advanced Filtering
- Date range filtering
- Dealership-specific views
- Status-based filtering
- Multi-criteria search

## 🎨 Design System

### Theme
- **Primary Color**: Purple (#7c3aed)
- **Secondary Color**: Light Purple (#a855f7)
- **Success**: Green (#10b981)
- **Warning**: Amber (#f59e0b)
- **Error**: Red (#ef4444)

### Features
- Dark/Light mode toggle
- Responsive design (mobile-first)
- Smooth animations and transitions
- Consistent iconography
- Accessible color contrasts

## 🔧 Technical Implementation

### Backend (Python/Flask)
- SQLite database with optimized indexes
- Comprehensive logging system
- Error handling and validation
- RESTful API endpoints

### Frontend (HTML/CSS/JavaScript)
- Modern ES6+ JavaScript
- Chart.js for data visualization
- CSS Grid and Flexbox layouts
- Progressive enhancement

### Integration
- Seamless integration with existing AI chatbot
- Shared authentication system
- Consistent navigation and theming
- Cross-system data sharing

## 📊 Sample Queries Supported

The system can answer questions like:

### Technical Reports
- "Which VIN number encounters most complaints?"
- "How many tyre complaints in December?"
- "Which dealership has the most complaints?"
- "Show me overall and car level complaint information"

### Campaign Reports
- "How many campaigns did each dealership complete?"
- "Which dealership did the most H6/Jolion services?"
- "Show me 6 months/yearly campaign statistics"

### FFS/SFS Inspections
- "Which dealership completed the most FFS inspections?"
- "Show me FFS statistics by car model"
- "Compare SFS completion rates across dealerships"

### PDI Inspections
- "How many PDI reports were submitted in date range?"
- "Which dealership submitted the most PDI reports?"
- "Show me PDI reports with objections"
- "What's the ratio of objections to total PDIs?"

### Repair Orders
- "How many ROs against this VIN?"
- "Show me repair order statistics by dealership"
- "What are the most common repair issues?"

### VIN History
- "Show me complete history of this VIN number"
- "Has this vehicle had any campaigns, warranty claims, or inspections?"

## 🚀 Future Enhancements

### Planned Features
1. **AI-Powered Insights**: Advanced pattern recognition in service data
2. **Predictive Analytics**: Predict potential issues based on service history
3. **Mobile App**: Native mobile application for field technicians
4. **Integration APIs**: Connect with external systems (DMS, ERP)
5. **Advanced Reporting**: Custom report builder with scheduling
6. **Workflow Automation**: Automated notifications and approvals

### Technical Improvements
1. **Performance Optimization**: Database query optimization and caching
2. **Real-time Updates**: WebSocket integration for live data updates
3. **Advanced Security**: Role-based access control and audit trails
4. **Data Import/Export**: Bulk data operations and format support
5. **Backup & Recovery**: Automated backup and disaster recovery

## 📞 Support & Maintenance

### Logging
- Comprehensive logging system in `utils/logger.py`
- Separate log files for different components
- Configurable log levels and rotation

### Error Handling
- Graceful error handling throughout the system
- User-friendly error messages
- Detailed error logging for debugging

### Performance
- Optimized database queries with proper indexing
- Efficient data loading and pagination
- Responsive design for fast loading

## 🤝 Contributing

When extending the dealership system:

1. **Follow Existing Patterns**: Use the established code structure and naming conventions
2. **Update Documentation**: Keep this README and code comments up to date
3. **Test Thoroughly**: Test all new features across different browsers and devices
4. **Maintain Consistency**: Follow the design system and UI patterns
5. **Log Appropriately**: Use the logging system for debugging and monitoring

## 📝 License

This dealership management system is part of the larger AI chatbot platform and follows the same licensing terms.

---

**Built with ❤️ for modern automotive dealership management**