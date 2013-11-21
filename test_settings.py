import djcelery
djcelery.setup_loader()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.sqlite',
    }
}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.comments',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'secretballot',

    'moderator',
    'djcelery',
)

MODERATOR = {
    'CLASSIFIER': 'moderator.storage.RedisClassifier',
    'HAM_CUTOFF': 0.3,
    'SPAM_CUTOFF': 0.7,
    'ABUSE_CUTOFF': 3,
}

ROOT_URLCONF = 'test_urls'

CELERY_IMPORTS = ('moderator.tasks', )
CELERY_ALWAYS_EAGER = True
