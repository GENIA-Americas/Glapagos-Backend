# Glápagos Backend API Documentation

## Overview
This document provides an overview of the API endpoints available in the Glápagos Backend.  
All endpoints follow REST conventions and return JSON responses.

## Base URL
http://localhost:8000/api/

## Endpoints

### Health Check
- **URL:** `/health/`
- **Method:** GET
- **Description:** Checks if the API is running.
- **Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-12-06T12:00:00Z"
}
