Daarul Portal - Complete starter package
=======================================

Quick start (Windows PowerShell):
1. python -m venv venv
2. .\venv\Scripts\Activate.ps1
3. pip install -r requirements.txt
4. python manage.py migrate
5. python manage.py createsuperuser
6. python manage.py loaddata students/fixtures/sample_data.json  # or use management command
7. python manage.py runserver

## Deployment

For detailed deployment instructions on PythonAnywhere, see [PYTHONANYWHERE_DEPLOYMENT.md](PYTHONANYWHERE_DEPLOYMENT.md).

Quick deployment checklist:
- [ ] Copy `.env.example` to `.env` and update values
- [ ] Run `python manage.py collectstatic`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Push code to Git repository (if using version control)
- [ ] Follow deployment guide for PythonAnywhere setup
