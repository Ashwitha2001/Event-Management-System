# Collaborative Event Management System

A RESTful API backend for managing events collaboratively with support for role-based permissions, recurring events, version history, and real-time collaboration features.

# Tech Stack

- Backend: Python, Django, Django REST Framework
- Database: PostgreSQL
- Authentication: JWT (via SimpleJWT)
- Real-time: Django Channels (via `consumers.py`)
- Documentation: Swagger (drf-yasg)
- Security: DRF permissions, custom rate limiting

# Project Structure

event_manager/
├── event_manager/         # Django project settings
│   ├── **init**.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── events/                # Main app for event logic
│   ├── admin.py
│   ├── apps.py
│   ├── consumers.py
│   ├── models.py
│   ├── permissions.py
│   ├── routing.py
│   ├── serializers.py
│   ├── urls.py
│   ├── utils.py
│   ├── views.py
│   └── ...
├── manage.py              # Django CLI entry point


# Features

- User registration and JWT-based authentication
- Role-based access (Owner, Editor, Viewer)
- Create, update, delete, and view events
- Recurring events with rules
- Batch creation of events
- Conflict detection
- Event sharing with permission control
- Version history and rollback
- Changelog with diff viewer
- Real-time update support (via Django Channels)
- API documentation (Swagger)


#  Setup Instructions

1. Clone Repository
   ```bash
   https://github.com/Ashwitha2001/Event-Management.git
   cd event-manager
````

2. Create and Activate Virtual Environment

   ```bash
   python -m venv event
   event\Scripts\activate 
   ```

3. Install Dependencies

   ```bash
   pip install -r requirements.txt
   ```

4. Apply Migrations

   ```bash
   python manage.py migrate
   ```

5. Run Development Server

   ```bash
   python manage.py runserver
   ```

6. Access API Docs

   * Visit: `http://127.0.0.1:8000/swagger/`



# API Endpoints Overview

| Endpoint                        | Method           | Description            |
| ------------------------------- | ---------------- | ---------------------- |
| `/api/register/`                | POST             | Register a user        |
| `/api/token/`                   | POST             | Login and get JWT      |
| `/api/token/refresh/`           | POST             | Refresh token          |
| `/api/events/`                  | GET, POST        | List or create events  |
| `/api/events/{id}/`             | GET, PUT, DELETE | Event details          |
| `/api/events/batch/`            | POST             | Create multiple events |
| `/api/events/{id}/share/`       | POST             | Share event with role  |
| `/api/events/{id}/permissions/` | GET              | View permissions       |
| `/api/events/{id}/rollback/`    | POST             | Rollback to version    |
| `/api/events/{id}/changelog/`   | GET              | Get version history    |



# Security

* JWT Authentication  via SimpleJWT
* Custom Permissions  for event roles
* Rate Limiting with `django-ratelimit`
* Input Validation with DRF serializers

