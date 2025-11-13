-------Debugging------
1. pipenv install django-debug-toolbar
2. goto settings.py and add 'debug-ttolbar' to INSTALLED_APPS
3. goto intern_logbbok_analysis -> urls.py
    add -> path('__debug__/', include('debug_toolbar.urls'))
4. goto settings.py and add 'debug_toolbar.middleware.DebugToolbarMiddleware' to MIDDLEWARE
5. goto settings.py and add ->
    INTERNAL_IPS = [
        '127.0.0.1',
    ]

-------Install Dependencies------
pip install -r requirements.txt

-------run the application------
python manage.py runserver