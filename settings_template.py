import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'a864krz_55um$ne3+4klalm2x@=@hskshj4t@s&srdvai1rrr5'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
PROJECT_NAME = 'A-PROJECT-NAME-TO-REPLACE'
ALLOWED_HOSTS = ['*']

APPEND_SLASH = True
# Application definition
TOKEN_NEED= False


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'rest_framework',
    'rest_framework_gis',
    'corsheaders',
    'hyper_resource',

]

MIDDLEWARE_CLASSES = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'PROJECT-NAME.urls'
CORS_ALLOW_HEADERS = (
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'content-location',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
)
CORS_ORIGIN_ALLOW_ALL = True
CORS_EXPOSE_HEADERS = ['accept',
                       'accept-encoding',
                       'authorization',
                       'content-type',
                       'content-location',
                       'dnt',
                       'origin',
                       'user-agent',
                       'x-csrftoken',
                       'x-requested-with',
                       'x-access-token',
                       ]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = PROJECT_NAME + '.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

if not 'IP_SGBD' in os.environ:
    os.environ['IP_SGBD'] = '172.30.10.86'

if not 'PORT_SGBD' in os.environ:
    os.environ['PORT_SGBD'] = '54329'

if not 'DB_NAME' in os.environ:
    os.environ['DB_NAME'] = 'gis'

if not 'DB_USERNAME' in os.environ:
    os.environ['DB_USERNAME'] = 'docker'

if not 'DB_PASSWORD' in os.environ:
    os.environ['DB_PASSWORD'] = 'docker'

ip_sgbd = os.environ['IP_SGBD']
port_sgbd = os.environ['PORT_SGBD']
db_name = os.environ['DB_NAME']
user = os.environ['DB_USERNAME']
password = os.environ['DB_PASSWORD']


DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'OPTIONS': {
            'options': '-c search_path=public',
        },

        'HOST': ip_sgbd,
        'PORT': port_sgbd,
        'NAME': db_name,
        'USER': user,
        'PASSWORD': password
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
