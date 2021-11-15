from .base import *

DATABASES = {
    'default': {
        'ENGINE': env('ENGINE'),
        'NAME': env('DATABASE_NAME'),
        'USER': env('DATABASE_USER'),
        'PASSWORD': env('DATABASE_PASSWORD'),
    }
}

DEBUG = True
ALLOWED_HOSTS = []
