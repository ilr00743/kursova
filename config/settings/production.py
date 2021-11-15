from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'illiaR$db_gradebook',
        'HOST': 'illiaR.mysql.pythonanywhere-services.com',
        'USER': 'illiaR',
        'PASSWORD': '1agbdlcid!',
    }
}

ALLOWED_HOSTS = ['illiaR.pythonanywhere.com']
STATIC_ROOT = '/home/illiaR/static/'
DEBUG = False
