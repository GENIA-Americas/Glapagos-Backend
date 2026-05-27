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
- **Description:** Checks the health of connected services (database, Redis). Returns 200 when all services are healthy, 503 when any service is down.
- **Response (200):**
```json
{
  "status": "healthy",
  "database": "ok",
  "redis": "ok",
  "timestamp": "2025-12-06T12:00:00Z"
}
```
- **Response (503):**
```json
{
  "status": "unhealthy",
  "database": "error",
  "redis": "ok",
  "timestamp": "2025-12-06T12:00:00Z"
}
```
