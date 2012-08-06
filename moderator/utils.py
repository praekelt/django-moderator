from django.conf import settings
from moderator.classifier import classifier
from moderator.constants import DEFAULT_CONFIG


def train(comment, is_spam):
    classifier.train(comment.comment, is_spam)
    classifier.store()


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
    (either ham or spam).

    If no class is provided a class is determined based on user abuse reports.
    If indicated to be spam by users the Baysian inference classifier is
    trained with the comment as such.

    If user abuse reports does not clearly classify a comment as spam a class
    is determined using Baysian inference. In this case no training occurs to
    prevent circular training.

    Returns a newly created or updated ClassifiedComment object.
    As a side effect also set is_removed field of comment based on class.
    """
    from moderator.models import ClassifiedComment

    if cls not in ['spam', 'ham', 'unsure', None]:
        raise Exception("Unrecognized classifications.")

    classified_comment, created = ClassifiedComment.objects.get_or_create(
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

    if cls is None:
        if comment.total_downvotes >= getattr(settings, 'MODERATOR',
                                              DEFAULT_CONFIG)['ABUSE_CUTOFF']:
            cls = 'spam'
            train(comment, is_spam=True)
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
