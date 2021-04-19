"""
Django settings for business_calender project.

Generated by 'django-admin startproject' using Django 2.1.15.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

from django.utils.translation import gettext_lazy as _
import os
import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfUniqueNamesType, ActiveDirectoryGroupType

import logging
logger = logging.getLogger('django_auth_ldap')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

# Baseline configuration.
# LDAP_SERVER = '192.168.1.82:389'
AUTH_LDAP_SERVER_URI = 'ldap://'
# The following may be needed if you are binding to Active Directory.
# AUTH_LDAP_CONNECTION_OPTIONS = {
#        # ldap.OPT_DEBUG_LEVEL: 1,
#     ldap.OPT_REFERRALS: 0
# }
# AUTH_LDAP_USER_DN_TEMPLATE = "sAMAccountName=%(user)s,DC=lichcongtac,DC=vn"
AUTH_LDAP_BIND_DN = 'CN=Bind,CN=Users,DC=lichcongtac,DC=vn'
AUTH_LDAP_BIND_PASSWORD = '@123abc#'
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "DC=lichcongtac,DC=vn",
    ldap.SCOPE_SUBTREE,
    '(sAMAccountName=%(user)s)',
)
# Populate the Django user from the LDAP directory.
AUTH_LDAP_USER_ATTR_MAP = {
    #'username': 'sAMAccountName',
    'first_name': 'cn',
    'last_name': 'sn',
    'email': 'mail',
}

AUTH_LDAP_MIRROR_GROUPS = True
# Set up the basic group parameters.
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "DC=lichcongtac,DC=vn",
    ldap.SCOPE_SUBTREE,
    '(objectCategory=Group)',
)
AUTH_LDAP_GROUP_TYPE = ActiveDirectoryGroupType(name_attr="cn")
# AUTH_LDAP_GROUP_TYPE = GroupOfUniqueNamesType()
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    'is_active': ('CN=ChuyenVien,CN=Users,DC=lichcongtac,DC=vn',
    'CN=LanhDao,CN=Users,DC=lichcongtac,DC=vn',
    'CN=VanThu,CN=Users,DC=lichcongtac,DC=vn', ),
    'is_staff': ('CN=ChuyenVien,CN=Users,DC=lichcongtac,DC=vn',
    'CN=LanhDao,CN=Users,DC=lichcongtac,DC=vn',
    'CN=VanThu,CN=Users,DC=lichcongtac,DC=vn', ),
    # 'is_superuser': 'cn=Administrators,cn=Users,DC=lichcongtac,DC=vn',
}

# Use LDAP group membership to calculate group permissions.
AUTH_LDAP_FIND_GROUP_PERMS = True
AUTH_LDAP_CACHE_GROUPS = True

# Cache distinguished names and group memberships for an hour to minimize
# LDAP traffic.
AUTH_LDAP_GROUP_CACHE_TIMEOUT = 3600

# This is the default, but I like to be explicit.
AUTH_LDAP_ALWAYS_UPDATE_USER = True
# AUTH_LDAP_CACHE_TIMEOUT = 3600

AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# BUGSNAG = {
#     'api_key': '7eb1d1c3a5b48721280eb7147e1c77bc',
#     'project_root': BASE_DIR,
# }

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '$b9t9bi-@rm&rn&n3x0@xg_a3v_(aquly-v@oqh%6!dm$^u7ak'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# ALLOWED_HOSTS = ['192.168.1.50']
ALLOWED_HOSTS = []

LANGUAGES = (
    ('vi', _('Vietnamese')),
    ('en', _('English')),
)

MULTILINGUAL_LANGUAGES = (
    "en-us",
    "vi",
)
# Application definition

INSTALLED_APPS = [
    # 'jet.dashboard',
    'jet',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'calender',
    'vehicle',
    'rest_framework',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.locale.LocaleMiddleware', 
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'bugsnag.django.middleware.BugsnagMiddleware',
]

ROOT_URLCONF = 'business_calender.urls'

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
                'django.template.context_processors.media'
            ],
        },
    },
]

WSGI_APPLICATION = 'business_calender.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'sql_server.pyodbc',
        'NAME': 'calender_13_office',
        'HOST': 'DESKTOP-1LRH31L\SQLEXPRESS',
        'PASSWORD': '@123abc#',
        'USER': 'sa',
        'POST':'1433',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        }
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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

STATICFILES_DIRS = [
    "/calender/static",
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

# LOGIN_URL = '/admin/calender/calender/'
# LOGIN_REDIRECT_URL = 'wagtailadmin_home'

LANGUAGE_CODE = 'vi-VI'

TIME_ZONE = 'Asia/Ho_Chi_Minh'

USE_I18N = True

USE_L10N = True

USE_TZ = False
DATE_FORMAT = '%d-%m-%Y'
DATE_INPUT_FORMATS = ('%d-%m-%Y', '%Y-%m-%d')
DATETIME_INPUT_FORMATS = ('%d-%m-%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S')
#JET_DEFAULT_THEME = 'default'
JET_DEFAULT_THEME = 'light-blue'
JET_SIDE_MENU_COMPACT = True
# JET_INDEX_DASHBOARD = 'jet.dashboard.dashboard.DefaultIndexDashboard'
# JET_APP_INDEX_DASHBOARD  =  'jet.dashboard.DefaultAppIndexDashboard'
JET_CHANGE_FORM_SIBLING_LINKS = True
# AUTH_USER_MODEL = 'calender.UserCustom'
# LOGIN_REDIRECT_URL = "/admin/calender/calender/"
LOGOUT_REDIRECT_URL = "/"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/files/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'files')