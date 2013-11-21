from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from moderator.constants import DEFAULT_CONFIG
from secretballot.models import Vote
from moderator.models import ClassifiedComment
from celery.task import task


@task(ignore_result=True)
def flag_reported_comments_task(comment):
    classified_comment, created = ClassifiedComment.objects.get_or_create(
        comment=comment
    )
    comment_content_type = ContentType.objects.get_for_model(comment)
    moderator_settings = getattr(settings, 'MODERATOR', DEFAULT_CONFIG)
    if Vote.objects.filter(
        content_type=comment_content_type,
        object_id=comment.id,
        vote=-1
    ).count() >= moderator_settings['ABUSE_CUTOFF']:
        comment.is_removed = True
        comment.save()
        classified_comment.cls = 'reported'
        classified_comment.save()
