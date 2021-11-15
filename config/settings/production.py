from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': f'{env("ACC_NAME")}$db_gradebook',
        'HOST': f'{env("ACC_NAME")}.mysql.pythonanywhere-services.com',
        'USER': env('ACC_NAME'),
        'PASSWORD': env('DATABASE_PASSWORD'),
    }
}

ALLOWED_HOSTS = [f'{env("ACC_NAME")}.pythonanywhere.com']
STATIC_ROOT = f'/home/{env("ACC_NAME")}/static/'
DEBUG = False