"""
Django settings for dva project.

Generated by 'django-admin startproject' using Django 1.10.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os, dj_database_url, sys, logging

DVA_PRIVATE_ENABLE = 'DVA_PRIVATE_ENABLE' in os.environ
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_BUCKET = os.environ.get('MEDIA_BUCKET', None)
CLOUD_FS_PREFIX = os.environ.get('CLOUD_FS_PREFIX', 's3') # By default AWS "s3", Tensorflow also supports "gs" for GCS
DEPLOY_ON_HEROKU = 'DEPLOY_ON_HEROKU' in os.environ
DISABLE_NFS = os.environ.get('DISABLE_NFS',False)

if DISABLE_NFS and (MEDIA_BUCKET is None):
    raise EnvironmentError("Either an NFS/Data volume or a remote S3 bucket is required!")

# SECURITY WARNING: keep the secret key used in production secret!
if 'SECRET_KEY' in os.environ or DEPLOY_ON_HEROKU:
    SECRET_KEY = os.environ['SECRET_KEY']
    AUTH_DISABLED = False
else:
    SECRET_KEY = 'changemeabblasdasbdbrp2$j&^'  # change this in prod
    AUTH_DISABLED = os.environ.get('AUTH_DISABLED', False)

INTERNAL_IPS = ['localhost','127.0.0.1']

# SECURITY WARNING: don't run with debug turned on in production!
if 'DISABLE_DEBUG' in os.environ or DEPLOY_ON_HEROKU:
    DEBUG = False
else:
    DEBUG = True

if sys.platform == 'darwin':
    DEV_ENV = True
else:
    DEV_ENV = False

if DEPLOY_ON_HEROKU:
    ALLOWED_HOSTS = [k.strip() for k in os.environ['ALLOWED_HOSTS'].split(',') if k.strip()]
    # SESSION_COOKIE_SECURE = True
    # CSRF_COOKIE_SECURE = True
    # SECURE_SSL_REDIRECT = True
    # SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') # Confirm this cannot be spoofed for heroku
    # SECURE_REDIRECT_EXEMPT = [r'^vdn/.']
else:
    ALLOWED_HOSTS = ["*"]  # Dont use this in prod

#: Only add pickle to this list if your broker is secured
#: from unwanted access (see userguide/security.html)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'django-db'
WSGI_APPLICATION = 'dva.wsgi.application'
ROOT_URLCONF = 'dva.urls'

INSTALLED_APPS = [
                     'django.contrib.admin',
                     'django.contrib.auth',
                     'django.contrib.contenttypes',
                     'django.contrib.sessions',
                     'django.contrib.messages',
                     'django.contrib.staticfiles',
                     'dvaapp',
                     'dvaui',
                     'django.contrib.humanize',
                     'django.contrib.postgres',
                     'django_celery_results',
                     'corsheaders',
                     'rest_framework',
                     'django_filters',
                     'crispy_forms',
                     'rest_framework.authtoken',
                     'django_celery_beat'
                 ] + (['dvap', ] if DVA_PRIVATE_ENABLE else [])+ (['debug_toolbar'] if DEV_ENV and DEBUG else [])


MIDDLEWARE_CLASSES = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEV_ENV and DEBUG:
    MIDDLEWARE_CLASSES = ['debug_toolbar.middleware.DebugToolbarMiddleware',] +MIDDLEWARE_CLASSES
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_METHODS = ('POST', 'GET',)
CORS_ALLOW_CREDENTIALS = True
if not DEPLOY_ON_HEROKU:
    CORS_URLS_REGEX = r'^api/.*$'
REST_FRAMEWORK = {
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    )
}

PATH_PROJECT = os.path.realpath(os.path.dirname(__file__))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates/'), ],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': True,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases
if DEPLOY_ON_HEROKU:
    DATABASES = {}
    db_from_env = dj_database_url.config(conn_max_age=500)
    DATABASES['default'] = db_from_env
    BROKER_URL = os.environ['CLOUDAMQP_URL']
elif DEV_ENV:
    BROKER_URL = 'amqp://{}:{}@localhost//'.format('dvauser', 'localpass')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'postgres',
            'USER': 'postgres',
            'PASSWORD': '',
            'HOST': 'localhost',
            'PORT': '',
        }
    }
elif 'CONTINUOUS_INTEGRATION' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'postgres',
            'USER': 'postgres',
            'PASSWORD': '',
            'HOST': 'localhost',
            'PORT': '',
        }
    }
    BROKER_URL = 'amqp://{}:{}@localhost//'.format('guest', 'guest')
elif 'DOCKER_MODE' in os.environ:
    if 'BROKER_URL' in os.environ:
        BROKER_URL = os.environ['BROKER_URL']
    else:
        BROKER_URL = 'amqp://{}:{}@{}//'.format(os.environ.get('RABBIT_USER', 'dvauser'),
                                                os.environ.get('RABBIT_PASS', 'localpass'),
                                                os.environ.get('RABBIT_HOST', 'rabbit'))
    if 'DATABASE_URL' in os.environ:
        DATABASES = {}
        db_from_env = dj_database_url.config(conn_max_age=500)
        DATABASES['default'] = db_from_env
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': os.environ.get('DB_NAME', 'postgres'),
                'USER': os.environ.get('DB_USER', 'postgres'),
                'PASSWORD': os.environ.get('DB_PASS', 'postgres'),
                'HOST': os.environ.get('DB_HOST', 'db'),
                'PORT': 5432,
            }
        }

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/
MEDIA_ROOT = os.path.expanduser('~/media/') if sys.platform == 'darwin' or os.environ.get('TRAVISTEST',False) else "/root/media/"

if DEPLOY_ON_HEROKU and ('MEDIA_URL' not in os.environ or 'STATIC_URL' not in os.environ):
    raise EnvironmentError('Please set STATIC_URL and MEDIA_URL')
elif DISABLE_NFS and ('LAUNCH_SERVER' in os.environ or 'LAUNCH_SERVER_NGINX' in os.environ) and 'MEDIA_URL' not in os.environ:
    raise EnvironmentError('You must set MEDIA_URL (e.g. http://s3bucketname.s3-website-us-east-1.amazonaws.com/)'
                           ' when launching websever in NFS disabled mode.')

MEDIA_URL = os.environ.get('MEDIA_URL', '/media/')
STATIC_URL = os.environ.get('STATIC_URL', '/static/')
DATA_UPLOAD_MAX_MEMORY_SIZE = 26214400

STATIC_ROOT = os.path.join(PROJECT_ROOT, 'staticfiles')
STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

GLOBAL_MODEL_QUEUE_ENABLED = False
GLOBAL_RETRIEVER_QUEUE_ENABLED = True

Q_MANAGER = 'qmanager'
Q_EXTRACTOR = 'qextract'
Q_CLUSTER = 'qclusterer'
Q_TRAINER = 'qtrainer'
Q_LAMBDA = 'qlambda'
GLOBAL_MODEL = 'q_slow_global_model'  # if a model specific queue does not exists then this is where the task ends up
GLOBAL_RETRIEVER = 'q_slow_global_retriever' # if a retriever specific queue does not exists then the task ends up here

TASK_NAMES_TO_QUEUE = {
    "perform_region_import":Q_EXTRACTOR,
    "perform_model_import":Q_EXTRACTOR,
    "perform_video_segmentation":Q_EXTRACTOR,
    "perform_video_decode":Q_EXTRACTOR,
    "perform_frame_download": Q_EXTRACTOR,
    "perform_dataset_extraction":Q_EXTRACTOR,
    "perform_transformation":Q_EXTRACTOR,
    "perform_export":Q_EXTRACTOR,
    "perform_deletion":Q_EXTRACTOR,
    "perform_sync":Q_EXTRACTOR,
    "perform_detector_import":Q_EXTRACTOR,
    "perform_import":Q_EXTRACTOR,
    "perform_retriever_creation": Q_CLUSTER,
    "perform_detector_training": Q_TRAINER,
    "perform_video_decode_lambda": Q_LAMBDA
}