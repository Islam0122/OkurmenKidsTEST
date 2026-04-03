import os
import environ
from pathlib import Path

env = environ.Env()
environ.Env.read_env(os.path.join(Path(__file__).resolve().parent.parent.parent, '.env'))

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = env('SECRET_KEY', default='django-insecure-super-secret-key-change-in-production')
DEBUG = True
ALLOWED_HOSTS = []
GIGACHAT_CLIENT_ID = env('GIGACHAT_CLIENT_ID', default='')
GIGACHAT_SECRET    = env('GIGACHAT_SECRET',    default='')

DJANGO_APPS = [
    'jazzmin',
    'nested_admin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    'django_filters',
    'import_export',
]

LOCAL_APPS: list[str] = [
    'apps.testing',

]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = '/admin-panel/login/'
LOGIN_REDIRECT_URL = '/admin-panel/'
LOGOUT_REDIRECT_URL = '/admin-panel/login/'

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 week


LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Asia/Bishkek'
USE_I18N = True
USE_TZ = True


STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── DRF ──────────────────────────────────────────────────────────────────────

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}


SPECTACULAR_SETTINGS = {
    'TITLE': 'OkurmenKids API',
    'DESCRIPTION': 'REST API for OkurmenKids platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}


from .cors import *


JAZZMIN_SETTINGS = {
    "site_logo": "img/logo.png",
    "site_logo_classes": "elevation-2",    # круглая обрезка
    "site_icon": "img/logo.png",
    "custom_css": "css/import_export.css",

    # Branding
    "site_title":        "OkurmenKids Admin",
    "site_header":       "OkurmenKids",
    "site_brand":        "OkurmenKids",

    "welcome_sign":      "Добро пожаловать в OkurmenKids 🚀",
    "copyright":         "OkurmenKids © 2026 — Islam Developer",


    "topmenu_links": [
        {"name": "Сайт",     "url": "/",                          "new_window": True},
        {"name": "API Docs", "url": "/api/schema/swagger-ui/",    "new_window": True},

    ],



    # "custom_links": {
    #     "testing": [
    #         {
    #             "name":        "Импорт вопросов",
    #             "url":         "/testing1/import/",
    #             "icon":        "fas fa-file-upload",
    #             "permissions": ["auth.change_user"],
    #         },
    #         {
    #             "name":        "Экспорт вопросов",
    #             "url":         "/testing1/export/",
    #             "icon":        "fas fa-file-download",
    #             "permissions": ["auth.change_user"],
    #         },
    #     ],
    # },

    "icons": {
        "auth":                        "fas fa-users-cog",
        "auth.user":                   "fas fa-user",
        "auth.Group":                  "fas fa-users",

        "testing.Test":                "fas fa-book-open",
        "testing.Question":            "fas fa-question-circle",
        "testing.QuestionOption":      "fas fa-dot-circle",

        "testing.TestSession":         "fas fa-clock",
        "testing.StudentAttempt":      "fas fa-chart-bar",
        "testing.Answer":              "fas fa-check-double",
    },

    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    "order_with_respect_to": [
        "testing.Test",
        "testing.Question",
        "testing.QuestionOption",

        "testing.TestSession",
        "testing.StudentAttempt",
        "testing.Answer",

        "auth",
    ],

    "show_sidebar":          True,
    "navigation_expanded":   True,
    "hide_apps":             [],
    "hide_models":           [],
    "related_modal_active":  True,
    "use_google_fonts_cdn":  False,
    # "show_ui_builder":       True,
    "changeform_format":     "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user":  "collapsible",
        "auth.group": "vertical_tabs",
    },
}
#
# JAZZMIN_UI_TWEAKS = {
#     # ── ТЕМА ─────────────────────────────────────
#     "theme": "darkly",
#     "default_theme_mode": "dark",
#
#     # ── NAVBAR (чище и легче) ─────────────────────
#     "navbar": "navbar-dark",
#     "navbar_small_text": False,
#     "navbar_fixed": True,
#     "no_navbar_border": True,
#
#     # ── SIDEBAR (SaaS стиль) ──────────────────────
#     "sidebar": "sidebar-dark-primary",
#     "sidebar_fixed": True,
#     "sidebar_nav_small_text": False,
#     "sidebar_nav_compact_style": True,
#     "sidebar_nav_child_indent": True,
#     "sidebar_nav_legacy_style": False,
#     "sidebar_nav_flat_style": True,
#     "sidebar_disable_expand": False,
#
#     # ── BRAND (минимализм) ────────────────────────
#     "brand_colour": "navbar-dark",
#     "brand_small_text": True,
#
#     # ── ACCENT (аккуратный фокус) ─────────────────
#     "accent": "accent-info",
#
#     # ── BODY (чистота интерфейса) ────────────────
#     "body_small_text": False,
#     "layout_boxed": False,
#
#     # ── FOOTER (минимальный) ──────────────────────
#     "footer_small_text": True,
#     "footer_fixed": False,
#
#     # ── КНОПКИ (чуть softer стиль) ────────────────
#     "button_classes": {
#         "primary": "btn-primary",
#         "secondary": "btn-outline-secondary",
#         "info": "btn-info",
#         "warning": "btn-warning",
#         "danger": "btn-danger",
#         "success": "btn-success",
#     },
# }

IMPORT_EXPORT_USE_TRANSACTIONS = True      # wrap import in DB transaction
IMPORT_EXPORT_SKIP_ADMIN_LOG   = False     # log every imported row (default)
IMPORT_EXPORT_CHUNK_SIZE       = 100