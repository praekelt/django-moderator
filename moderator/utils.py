from django.conf import settings
from moderator.classifier import classifier


def train(comment, is_spam):
    classifier.train(comment.comment, is_spam)
    classifier.store()


def get_class(comment):
    try:
        score = classifier.score(comment.comment)
    except ZeroDivisionError:
        return 'unsure'

    if score < getattr(settings, 'MODERATOR_HAM_CUTOFF', 0.3):
        return 'ham'
    if score > getattr(settings, 'MODERATOR_SPAM_CUTOFF', 0.7):
        return 'spam'
    return 'unsure'
