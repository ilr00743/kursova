from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'illiaR$db_gradebook',
        'HOST': 'illiaR.mysql.pythonanywhere-services.com',
        'USER': 'illiaR',
        'PASSWORD': env('DATABASE_PASSWORD'),
    }
}

ALLOWED_HOSTS = ['illiaR.pythonanywhere.com']
STATIC_ROOT = '/home/illiaR/static/'
DEBUG = False
