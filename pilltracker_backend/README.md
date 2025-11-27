# 💊 Smart Pillbox Backend

A Django REST Framework-based backend for managing pill reminders, schedules, and refill alerts.

## 🚀 Features
- User management (Doctors, Patients)
- Pill schedules and intake tracking
- Refill detection & logging
- Voice agent integration (optional)
- Celery + Redis for scheduled reminders

## 🧩 Tech Stack
- **Backend:** Django, Django REST Framework  
- **Database:** PostgreSQL / SQLite  
- **Task Queue:** Celery + Redis  
- **Deployment:** Render / Railway / AWS EC2  

## ⚙️ Installation

```bash
# 1. Clone repository
git clone https://github.com/yourusername/pilltracker_backend.git
cd pilltracker_backend

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate    # (Windows)
# or
source venv/bin/activate # (Linux/Mac)

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Start development server
python manage.py runserver
