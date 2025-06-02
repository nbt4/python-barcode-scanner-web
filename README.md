# Barcode Scanner Web Application

A responsive web application for managing devices, jobs, and barcode scanning operations.

## Features

- User authentication and authorization
- Job management (create, read, update, delete)
- Device tracking with barcode/QR code scanning
- Real-time camera integration for scanning
- Custom pricing for devices
- PDF report generation
- Responsive design for mobile and desktop

## Project Structure

```
webapp/
├── backend/              # Flask API server
│   ├── app/             # Application package
│   │   ├── routes/      # API endpoints
│   │   └── utils/       # Utility functions
│   ├── config.py        # Configuration settings
│   ├── requirements.txt # Python dependencies
│   └── run.py          # Application entry point
└── frontend/            # React application
    ├── public/         # Static files
    └── src/            # Source code
        ├── components/ # Reusable components
        └── pages/      # Application pages
```

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- MySQL database

## Setup

### Backend Setup

1. Create a virtual environment and activate it:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the backend directory (copy from .env.example):
```bash
cp .env.example .env
```

4. Start the Flask server:
```bash
python run.py
```

The backend server will start at http://localhost:5000

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm start
```

The frontend application will start at http://localhost:3000

## API Endpoints

### Authentication
- POST `/api/v1/auth/login` - User login
- GET `/api/v1/auth/verify` - Verify JWT token
- POST `/api/v1/auth/logout` - User logout

### Jobs
- GET `/api/v1/jobs` - List all jobs
- GET `/api/v1/jobs/<id>` - Get job details
- POST `/api/v1/jobs` - Create new job
- PUT `/api/v1/jobs/<id>` - Update job
- DELETE `/api/v1/jobs/<id>` - Delete job

### Devices
- GET `/api/v1/devices/job/<job_id>` - List devices in job
- POST `/api/v1/devices/job/<job_id>/device` - Add device to job
- DELETE `/api/v1/devices/job/<job_id>/device/<device_id>` - Remove device from job
- GET `/api/v1/devices/qrcode/<device_id>` - Generate QR code
- GET `/api/v1/devices/barcode/<device_id>` - Generate barcode
- GET `/api/v1/devices/verify/<device_id>` - Verify device

### Reports
- GET `/api/v1/reports/jobs` - Generate jobs report
- GET `/api/v1/reports/job/<job_id>/devices` - Generate job devices report

## Environment Variables

### Backend (.env)
```
MYSQL_HOST=tsunami-events.de
MYSQL_DATABASE=TS-Lager
MYSQL_POOL_SIZE=5
SECRET_KEY=your-secret-key-here
JWT_EXPIRATION=3600
CORS_ORIGINS=*
FLASK_ENV=development
FLASK_DEBUG=True
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.
