from .settings import *  # noqa: F401,F403

# Use local SQLite databases for test runs to avoid external MySQL dependencies.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_default.sqlite3',
    },
    'ai_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_ai.sqlite3',
    },
    'audit_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_audit.sqlite3',
    },
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Allow login without AdminApps during automated tests (no external service available).
ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS = True

# Disable owner-only restriction so test users can authenticate freely.
OWNER_ORGANIZATION_ONLY_ACCESS = False
