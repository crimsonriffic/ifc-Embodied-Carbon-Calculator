# IFC Embodied Carbon Calculator

## Introduction

This project is an IFC Embodied Carbon Calculator Collaborative Platform. It allows multiple stakeholders—including architects, ESD consultants, contractors, and C&S engineers—to collaborate on evaluating the embodied carbon footprint of a project.

Users can upload an IFC file for their project, and the platform will automatically extract relevant details and calculate the embodied carbon value. Additionally, different stakeholders working on the same project can view progress updates made by others, ensuring a transparent and collaborative workflow.

## Overview
This project consists of a frontend and a backend, designed to work together seamlessly. The frontend is built using JavaScript with Vite, while the backend is developed in Python.

## Project Structure
```
/project-root
│-- frontend/    # React frontend
│-- backend/     # Python backend
│-- README.md    # Project documentation
```

## Getting Started
Follow the steps below to set up and run the project.

### Prerequisites
Make sure you have the following installed:
- **Node.js** (for the frontend)
- **Python 3** (for the backend)

### Setting Up Environment Variables

Before running the backend, you need to create a .env file inside the backend/ directory with the following structure:

MONGODB_URL=<your-mongodb-url>
DB_NAME=projects
AWS_ACCESS_KEY=<your-aws-access-key>
AWS_SECRET_KEY=<your-aws-secret-key>
S3_BUCKET=ifcfiles

Replace the placeholder values (<your-mongodb-url>, <your-aws-access-key>, etc.) with your actual credentials.

### Running the Frontend
1. Navigate to the frontend directory:
   ```sh
   cd frontend
   ```
2. Install dependencies:
   ```sh
   npm install
   ```
3. Start the development server:
   ```sh
   npm run dev
   ```
The frontend should now be running on `http://localhost:5173` (or another available port).

### Running the Backend
1. Navigate to the backend directory:
   ```sh
   cd backend
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Start the backend server:
   ```sh
   python main.py
   ```
The backend should now be running on `http://localhost:5000` (or another configured port).


