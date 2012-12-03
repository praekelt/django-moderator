from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from moderator.classifier import classifier
from moderator.constants import DEFAULT_CONFIG
from secretballot.models import Vote
from moderator import models


def train(comment, is_spam):
    classifier.train(comment.comment, is_spam)
    classifier.store()


def clear():
    classifier.bayes.clear()


def get_class(comment):
    """
    Returns comment class as determined by Baysian classifier.
    """
    try:
        score = classifier.score(comment.comment)
    except ZeroDivisionError:
        return 'unsure'

    if score < getattr(settings, 'MODERATOR', DEFAULT_CONFIG)['HAM_CUTOFF']:
        return 'ham'
    if score > getattr(settings, 'MODERATOR', DEFAULT_CONFIG)['SPAM_CUTOFF']:
        return 'spam'
    return 'unsure'


def classify_comment(comment, cls=None):
    """
    Trains Baysian inference classifier with comment and provided class
    (either 'ham' or 'spam').

    If 'unsure' class is provided no training occures, the comment's class
    is simply set as such.

    If 'reported' class is provided no training occures, the comment's class
    is simply set as such and removed.

    If no class is provided a lookup is done to see if the comment has been
    reported by users as abusive. If indicated as abusive class is set
    as 'reported', with spam training occuring and the comment being removed.

    If a comment is not reported as abusive by users and without a class being
    provided a class is determined using Baysian inference. In this case no
    training occurs to prevent self learning.

    Returns a newly created or updated ClassifiedComment object.
    As a side effect also sets is_removed field of comment based on class.
    """
    if cls not in ['spam', 'ham', 'unsure', 'reported', None]:
        raise Exception("Unrecognized classifications.")

    classified_comment, created = models.ClassifiedComment.objects.get_or_create(
        comment=comment
    )

    if cls == 'spam' and classified_comment.cls != 'spam':
        train(comment, is_spam=True)
        comment.is_removed = True
        comment.save()
        classified_comment.cls = cls
        classified_comment.save()
        return classified_comment

    if cls == 'ham' and classified_comment.cls != 'ham':
        train(comment, is_spam=False)
        comment.is_removed = False
        comment.save()
        classified_comment.cls = cls
        classified_comment.save()
        return classified_comment

    if cls == 'unsure' and classified_comment.cls != 'unsure':
        classified_comment.cls = cls
        classified_comment.save()
        return classified_comment

    if cls == 'reported' and classified_comment.cls != 'reported':
        train(comment, is_spam=True)
        comment.is_removed = True
        comment.save()
        classified_comment.cls = cls
        classified_comment.save()
        return classified_comment

    if cls is None:
        comment_content_type = ContentType.objects.get_for_model(comment)
        moderator_settings = getattr(settings, 'MODERATOR', DEFAULT_CONFIG)
        if Vote.objects.filter(
            content_type=comment_content_type,
            object_id=comment.id,
            vote=-1
        ).count() >= moderator_settings['ABUSE_CUTOFF']:
            cls = 'reported'
            comment.is_removed = True
            comment.save()
            classified_comment.cls = cls
            classified_comment.save()
            return classified_comment
        else:
            cls = get_class(comment)
            comment.is_removed = cls == 'spam'
            comment.save()
            classified_comment.cls = cls
            classified_comment.save()
            return classified_comment

    return classified_comment
