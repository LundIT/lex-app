from __future__ import absolute_import
import sys
from pathlib import Path

from google.oauth2 import service_account

import warnings

from django.core.cache import CacheKeyWarning
"""
Django settings for lex_app project.

Generated by 'django-admin startproject' using Django 3.0.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
from .celery import app as celery_app, app

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from datetime import timedelta

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

def traces_sampler(sampling_context):
    if sampling_context == "/health":
        # Drop this transaction, by setting its sample rate to 0%
        return 0
    else:
        # Default sample rate for all others (replaces traces_sample_rate)
        return 0.1
if os.getenv("DEPLOYMENT_ENVIRONMENT") != 'DEV'  and os.getenv("DEPLOYMENT_ENVIRONMENT") is not None:
    sentry_sdk.init(
        dsn="https://a3aa24a7fccd42dbbb7457e6402b5443@o1318244.ingest.sentry.io/6573603",
        integrations=[
            DjangoIntegration(),
        ],
        environment=os.getenv("DEPLOYMENT_ENVIRONMENT"),

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sampler=traces_sampler,

        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True
    )


warnings.simplefilter("ignore", CacheKeyWarning)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEW_BASE_DIR = Path(os.getenv("PROJECT_ROOT")).parent.as_posix()
sys.path.append(NEW_BASE_DIR)

GRAPH_MODELS = {
  'app_labels': ["generic_app"],
  'group_models': True,
}

ASGI_APPLICATION = "lex_app.asgi.application"

if os.getenv("DEPLOYMENT_ENVIRONMENT") is None:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }
else:
    CHANNEL_LAYERS = {
            "default": {
                "BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
                "CONFIG": {
                    "hosts": [(f"redis://{os.getenv('REDIS_USERNAME')}:{os.getenv('REDIS_PASSWORD')}@{os.getenv('REDIS_HOST')}/2"
                               if os.getenv("DEPLOYMENT_ENVIRONMENT") is not None else "redis://127.0.0.1:6379/2")],
                    "capacity": 100000,
                    "expiry": 10,
                    "prefix": f'{os.getenv("INSTANCE_RESOURCE_IDENTIFIER", "local")}:'
                },
            },
    }

DEFAULT_FILE_STORAGE = 'lex_app.CustomDefaultStorage.CustomDefaultStorage'

SHAREPOINT_APP_CLIENT_ID = os.getenv("SHAREPOINT_APP_CLIENT_ID")
SHAREPOINT_APP_CLIENT_SECRET = os.getenv("SHAREPOINT_APP_CLIENT_SECRET")
SHAREPOINT_URL = os.getenv("SHAREPOINT_URL", "local")
SHAREPOINT_STATIC_DIR = "static"
SHAREPOINT_MEDIA_DIR = "uploads"

if os.getenv("STORAGE_TYPE") == "SHAREPOINT":
    DEFAULT_FILE_STORAGE = 'django_sharepoint_storage.SharePointCloudStorageUtils.Media'
    MEDIA_ROOT = "uploads/"

if os.getenv("STORAGE_TYPE") == "GCS":
    DEFAULT_FILE_STORAGE = 'lex_app.gcsUtils.Media'
    GS_BUCKET_NAME = os.getenv("GS_BUCKET_NAME")
    GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
        os.path.join(NEW_BASE_DIR, 'django-storages', 'gcpCredentials.json'),
    )
    MEDIA_ROOT = "uploads/"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', default='pjlulvaa77lteno-_y6!oxb%63xqiaw4%n%1or&77a!x9@nkd+')

# SECURITY WARNING: don't run with debug turned on in production!
if os.getenv("LEX_ENVIRONMENT_TAG", "envvar_not_existing") == "dev":
    DEBUG = True
else:
    DEBUG = False

ALLOWED_HOSTS = [os.getenv("DOMAIN_HOSTED", "localhost"), '127.0.0.1', 'localhost',
                 os.environ.get('POD_IP', default='envvar_not_existing')]
if os.getenv("KUBERNETES_ENVIRONMENT", "envvar_not_existing") == "AGI":
    ALLOWED_CIDR_NETS = ['172.16.0.0/12']
else:
    ALLOWED_CIDR_NETS = ['10.0.0.0/8']

LOGIN_REDIRECT_URL = '/process_admin/all'

CSRF_TRUSTED_ORIGINS = ['https://*.' + os.getenv("DOMAIN_HOSTED", "localhost")]

REACT_APP_BUILD_PATH = (Path(__file__).resolve().parent.parent / Path("react/build")).as_posix()
repo_name = os.getenv("PROJECT_ROOT").split("/")[-1]
LEGACY_MEDIA_ROOT = os.path.join(NEW_BASE_DIR, f"{repo_name}/")
# Application definition

INSTALLED_APPS = [
    'channels',
    'lex.lex_app.apps.LexAppConfig',
    # f'{repo_name}.apps.ArmiraCashflowConfig',
    repo_name,
    'celery',
    'react',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'mozilla_django_oidc',
    'rest_framework',
    'rest_framework_api_key',
    "django.contrib.postgres",
]

CRISPY_FAIL_SILENTLY = not DEBUG

MIDDLEWARE = [
    'allow_cidr.middleware.AllowCIDRMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "django_cprofile_middleware.middleware.ProfilerMiddleware",
]

DJANGO_CPROFILE_MIDDLEWARE_REQUIRE_STAFF = False

ROOT_URLCONF = 'lex_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), 'generic_app/submodels/']
        ,
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

WSGI_APPLICATION = 'lex_app.wsgi.application'

DISABLE_SERVER_SIDE_CURSORS = True

db_username = os.getenv("POSTGRES_USERNAME", "django")
kubernetes = not os.getenv("KUBERNETES_ENGINE", "NONE") == "NONE"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "default_cache",
        'TIMEOUT': None,
    },
    "oidc": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "oidc_cache",
    }
}


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': f'db_{repo_name}',
        'USER': 'django',
        'PASSWORD': 'lundadminlocal',
        'HOST': 'localhost',
        'PORT': '5432',
        'TEST': {
            'NAME': f'db_{repo_name}',
        }
    },

    'GCP': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv("DATABASE_NAME", "envvar_not_existing"),
        'USER': db_username,
        'PASSWORD': os.getenv("POSTGRES_PASSWORD", "envvar_not_existing"),
        'HOST': os.getenv("DATABASE_DOMAIN", "envvar_not_existing"),
        'PORT': '5432',
        'TEST': {
            'NAME': os.getenv("DATABASE_NAME", "envvar_not_existing"),
        }
    },

    'DOCKER-COMPOSE': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv("DATABASE_NAME", "envvar_not_existing"),
        'USER': db_username,
        'PASSWORD': os.getenv("POSTGRES_PASSWORD", "envvar_not_existing"),
        'HOST': os.getenv("DATABASE_DOMAIN", "envvar_not_existing"),
        'PORT': '5432',
        'TEST': {
            'NAME': os.getenv("DATABASE_NAME", "envvar_not_existing"),
        }
    },

    'K8S': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv("DATABASE_NAME", "envvar_not_existing"),
        'USER': db_username,
        'PASSWORD': os.getenv("POSTGRES_PASSWORD", "envvar_not_existing"),
        'HOST': os.getenv("DATABASE_DOMAIN", "envvar_not_existing"),
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'disable'
        },
        'TEST': {
            'NAME': os.getenv("DATABASE_NAME", "envvar_not_existing"),
        }
    },
}
DATABASE_DEPLOYMENT_TARGET = os.getenv("DATABASE_DEPLOYMENT_TARGET", "local") 
if DATABASE_DEPLOYMENT_TARGET != "local":
    DATABASES["default"] = DATABASES[DATABASE_DEPLOYMENT_TARGET]

MIGRATION_MODULES = {}


# CELERY STUFF
CELERY_BROKER_URL = f"redis://{os.getenv('REDIS_USERNAME')}:{os.getenv('REDIS_PASSWORD')}@{os.getenv('REDIS_HOST')}/1" if os.getenv("DEPLOYMENT_ENVIRONMENT") is not None else "redis://127.0.0.1:6379/1"
CELERY_RESULT_BACKEND = f'db+postgresql://{db_username}:{os.getenv("POSTGRES_PASSWORD", "envvar_not_existing")}@{os.getenv("DATABASE_DOMAIN", "envvar_not_existing")}/{os.getenv("DATABASE_NAME", "envvar_not_existing")}' \
    if os.getenv("DEPLOYMENT_ENVIRONMENT") is not None \
    else f'db+postgresql://django:lundadminlocal@localhost/db_{repo_name}'
CELERY_CACHE_BACKEND = 'default'
CELERY_ACCEPT_CONTENT = ['application/json', 'pickle']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_CREATE_MISSING_QUEUES = True
CELERY_TASK_TRACK_STARTED = True
CELERY_RESULT_PERSISTENT = True
CELERY_TASK_DEFAULT_QUEUE = os.getenv("INSTANCE_RESOURCE_IDENTIFIER", "celery")
CELERY_BROKER_TRANSPORT_OPTIONS = {'global_keyprefix': f'{os.getenv("INSTANCE_RESOURCE_IDENTIFIER", "celery")}:',
                            'visibility_timeout': float("inf")}
CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS = {'global_keyprefix': f'{os.getenv("INSTANCE_RESOURCE_IDENTIFIER", "celery")}:',
                                    'visibility_timeout': float("inf")}
CELERY_TASK_ACKS_LATE = True



try:
    c_force_root = os.getenv('C_FORCE_ROOT')
    if os.getenv('C_FORCE_ROOT') == 'True':
        celery_active = True
    else:
        celery_active = False
except Exception as e:
    celery_active = False

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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

CORS_ORIGIN_ALLOW_ALL = True

# ##################################################
# ################## START AUTH ####################
# ##################################################

# Django doesn't allow OIDC and local JWT to be combined, that's why it can be selected here, which strategy
# will be used in the project. Specify the strategy in the variable USED_AUTH_BACKEND

# Local authentication with jwt tokens:     "local"
# Using Azure AD with drf-oidc-auth:        "azure_drf" (default)
# Using Azure AD with mozilla-django-oidc:  "azure_mozilla"
USED_AUTH_BACKEND = 'azure_drf'

DATA_UPLOAD_MAX_NUMBER_FIELDS = None

OIDC_AUTH = {
    # Specify OpenID Connect endpoint. Configuration will be
    # automatically done based on the discovery document found
    # at <endpoint>/.well-known/openid-configuration
    # instance
    'OIDC_ENDPOINT': os.getenv("KEYCLOAK_URL", "auth_url")+'/realms/'+os.getenv("KEYCLOAK_REALM", "default"),
    # local
    # 'OIDC_ENDPOINT': 'https://auth.test-excellence-cloud.de/realms/hassine_realm',

    # Accepted audiences the ID Tokens can be issued to
    'OIDC_AUDIENCES': ('account',),

    # (Optional) Function that resolves id_token into user.
    # This function receives a request and an id_token dict and expects to
    # return a User object. The default implementation tries to find the user
    # based on username (natural key) taken from the 'sub'-claim of the
    # id_token.
    # 'OIDC_RESOLVE_USER_FUNCTION': 'oidc_auth.authentication.get_user_by_id',
    'OIDC_RESOLVE_USER_FUNCTION': 'lex_app.auth_helpers.resolve_user',

    # (Optional) Number of seconds in the past valid tokens can be
    # issued (default 600)
    'OIDC_LEEWAY': 600,

    # (Optional) Time before signing keys will be refreshed (default 24 hrs)
    'OIDC_JWKS_EXPIRATION_TIME': 24 * 60 * 60,

    # (Optional) Time before bearer token validity is verified again (default 10 minutes)
    'OIDC_BEARER_TOKEN_EXPIRATION_TIME': 10 * 60,

    # (Optional) Token prefix in JWT authorization header (default 'JWT')
    'JWT_AUTH_HEADER_PREFIX': 'JWT',

    # (Optional) Token prefix in Bearer authorization header (default 'Bearer')
    'BEARER_AUTH_HEADER_PREFIX': 'Bearer',

    # (Optional) Which Django cache to use
    'OIDC_CACHE_NAME': 'oidc',

    # (Optional) A cache key prefix when storing and retrieving cached values
    'OIDC_CACHE_PREFIX': 'oidc_auth.',
}

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=2),
}

OIDC_OP_JWKS_ENDPOINT = 'https://login.microsoftonline.com/05de5765-cb4f-40f1-bd36-43c168137df6/discovery/v2.0/keys'
OIDC_RP_CLIENT_ID = 'ed12bb9c-8191-49fb-b1dd-8e5eea9e6ab2'
OIDC_RP_CLIENT_SECRET = "..53k_1E_31644IlQJotO.2Sfg66-SjwJz"
OIDC_OP_AUTHORIZATION_ENDPOINT = 'https://login.microsoftonline.com/05de5765-cb4f-40f1-bd36-43c168137df6/oauth2/v2.0/authorize'
OIDC_OP_TOKEN_ENDPOINT = 'https://login.microsoftonline.com/05de5765-cb4f-40f1-bd36-43c168137df6/oauth2/v2.0/token'
OIDC_OP_USER_ENDPOINT = "https://graph.microsoft.com/oidc/userinfo"

OIDC_DRF_AUTH_BACKEND = 'mozilla_django_oidc.auth.OIDCAuthenticationBackend'

if USED_AUTH_BACKEND == "local":
    DEFAULT_AUTHENTICATION_CLASSES = ('rest_framework_simplejwt.authentication.JWTAuthentication',)
elif USED_AUTH_BACKEND == "azure_drf":
    DEFAULT_AUTHENTICATION_CLASSES = (
        'oidc_auth.authentication.BearerTokenAuthentication',
        'oidc_auth.authentication.JSONWebTokenAuthentication'
    )
elif USED_AUTH_BACKEND == "azure_mozilla":
    DEFAULT_AUTHENTICATION_CLASSES = ('mozilla_django_oidc.contrib.drf.OIDCAuthentication',)
else:
    raise ValueError("USED_AUTH_BACKEND has to be either local, azure-drf or azure-mozilla, not " + USED_AUTH_BACKEND)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": DEFAULT_AUTHENTICATION_CLASSES,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    # FIXME: maybe use this at some point (for giving individual access rights):
    # "DEFAULT_PERMISSION_CLASSES": ['rest_framework_api_key.permissions.HasAPIKey' | 'rest_framework.permissions.IsAuthenticated']
}
API_KEY_CUSTOM_HEADER = "HTTP_API_KEY"

if os.getenv("SENDGRID_API_KEY", "envvar_not_existing") != "envvar_not_existing":
    SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]
else:
    print("SENDGRID_API_KEY not found in environmental variables.")
    SENDGRID_API_KEY = 'improperlyConfigured'

EMAIL_BACKEND = "sendgrid_backend.SendgridBackend"
SENDGRID_SANDBOX_MODE_IN_DEBUG = False
SENDGRID_ECHO_TO_STDOUT = True

# ##################################################
# ################## END AUTH ######################
# ##################################################

CORS_ORIGIN_WHITELIST = ['https://' + os.getenv("DOMAIN_HOSTED", "localhost:3000"), 'http://localhost:3000', 'http://127.0.0.1:3000']

LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# TODO: does this fix the "Unauthorized: /api/model_tree/"-issue which occurs after some time??
TIME_ZONE = 'Europe/Berlin'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static-django/'

STATIC_ROOT = "/static"

if os.getenv("STORAGE_TYPE") == "LEGACY" or not os.getenv("STORAGE_TYPE"):

    if os.getenv("KUBERNETES_ENGINE", "NONE") == "NONE":
        MEDIA_ROOT = os.path.join(NEW_BASE_DIR, f"{repo_name}/")
        MEDIA_URL = os.path.join(NEW_BASE_DIR, f"{repo_name}/")
        USER_REPORT_ROOT = os.path.join(NEW_BASE_DIR, f"{repo_name}/")
    else:
        # this section is not in effect when a cloud storage option is used.
        # Check DjangoProcessAdminGeneric/gcsUtils.py or
        # DjangoProcessAdminGeneric/sharepoint/SharePointCloudStorageUtils.py for replacement.
        MEDIA_ROOT = '/app/storage/uploads/'
        MEDIA_URL = '/app/storage/uploads/'

        USER_REPORT_ROOT = '/app/storage/reports/'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {message}',
            'style': '{'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.getenv("LOG_LEVEL", "DEBUG"),
    }
}
DATA_UPLOAD_MAX_MEMORY_SIZE=None
