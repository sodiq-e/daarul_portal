# 17. APIs and Integration Points

## Built-in API Surface
The project includes Django REST Framework support, though the main implementation is template-rendered rather than API-first.

## Current API Observations
- rest_framework is installed in settings.py
- The repository contains app-level views and URL structures, but the project mostly uses standard Django views rather than explicit DRF router endpoints

## Integration Points
- Django admin endpoints
- Template-based website routes
- Email sending via Django mail backend
- Optional cloud/static storage support via cloudinary packages
- AI provider service integration

## Notes for Maintainers
- If the project is to evolve into a more API-driven platform, the existing templates and views can be wrapped progressively with DRF serializers and endpoints
- Current code is more centered on server-rendered workflows than JSON APIs
