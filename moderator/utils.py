from django.conf import settings
from moderator.classifier import classifier
from moderator.constants import DEFAULT_CONFIG


def train(comment, is_spam):
    classifier.train(comment.comment, is_spam)
    classifier.store()


def get_class(comment):
    try:
        score = classifier.score(comment.comment)
    except ZeroDivisionError:
        return 'unsure'

    if score < getattr(settings, 'MODERATOR', DEFAULT_CONFIG)['HAM_CUTOFF']:
        return 'ham'
    if score > getattr(settings, 'MODERATOR', DEFAULT_CONFIG)['SPAM_CUTOFF']:
        return 'spam'
    return 'unsure'
