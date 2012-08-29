DJANGO_SAMPLE_CONFIG = {
    'CLASSIFIER': 'moderator.storage.DjangoClassifier',
    'HAM_CUTOFF': 0.3,
    'SPAM_CUTOFF': 0.7,
    'ABUSE_CUTOFF': 3,
}

REDIS_SAMPLE_CONFIG = {
    'CLASSIFIER': 'moderator.storage.RedisClassifier',
    'CLASSIFIER_CONFIG': {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'password': None,
        'socket_timeout': None,
        'connection_pool': None,
        'charset': 'utf-8',
        'errors': 'strict',
        'unix_socket_path': None,
    },
    'HAM_CUTOFF': 0.3,
    'SPAM_CUTOFF': 0.7,
    'ABUSE_CUTOFF': 3,
}

DEFAULT_CONFIG = DJANGO_SAMPLE_CONFIG

CLASS_CHOICES = (
    ('reported', 'Reported'),
    ('spam', 'Spam'),
    ('ham', 'Ham'),
    ('unsure', 'Unsure'),
)
