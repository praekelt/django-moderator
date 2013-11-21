from datetime import timedelta

from django.conf import settings
from django.contrib.comments.models import Comment
from django.db import models
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import receiver
from moderator.constants import CLASS_CHOICES
from likes.signals import object_liked
import secretballot


COMMENT_MAX_LENGTH = getattr(settings, 'COMMENT_MAX_LENGTH', 3000)


class CannedReply(models.Model):
    comment = models.TextField(max_length=COMMENT_MAX_LENGTH)
    site = models.ForeignKey(
        'sites.Site',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name_plural = 'Canned replies'

    def __unicode__(self):
        return self.comment


class ClassifiedComment(models.Model):
    comment = models.ForeignKey('comments.Comment')
    cls = models.CharField(
        'Class',
        max_length=64,
        choices=CLASS_CHOICES
    )

    class Meta:
        ordering = ['-comment__submit_date', ]

    def __unicode__(self):
        return self.cls.title()


class CommentReply(models.Model):
    user = models.ForeignKey(
        'auth.User',
        limit_choices_to={'is_staff': True}
    )
    canned_reply = models.ForeignKey(
        'moderator.CannedReply',
        help_text='Select a canned reply or otherwise enter '
                  'a custom comment below.',
        blank=True,
        null=True,
    )
    comment = models.TextField(
        max_length=COMMENT_MAX_LENGTH,
        help_text='Enter a custom comment (only used if no '
                  'canned reply is selected).',
        blank=True,
        null=True,
    )
    replied_to_comments = models.ManyToManyField(
        'comments.Comment',
        related_name='replied_to_comments_set',
        help_text='Comment on which this reply applies.'
    )
    reply_comments = models.ManyToManyField(
        'comments.Comment',
        related_name='reply_comments_set',
        blank=True,
        null=True,
        help_text='Generated reply comments.'
    )

    class Meta:
        verbose_name_plural = 'Comment replies'

    def __unicode__(self):
        return "%s: %s..." % (
            self.user.username,
            self.comment[:50]
        )

    @property
    def comment_text(self):
        if self.canned_reply:
            return self.canned_reply.comment
        if self.comment:
            return self.comment


# Proxy models for admin display.
class HamComment(Comment):
    class Meta:
        proxy = True


class ReportedComment(Comment):
    class Meta:
        proxy = True


class SpamComment(Comment):
    class Meta:
        proxy = True


class UnsureComment(Comment):
    class Meta:
        proxy = True


@receiver(pre_delete, sender=CommentReply)
def comment_reply_pre_delete_handler(sender, instance, **kwargs):
    """
    Deletes all generated reply comments.
    """
    instance.reply_comments.all().delete()


@receiver(m2m_changed, sender=CommentReply.replied_to_comments.through)
def comment_reply_post_create_handler(sender, instance, action, model, pk_set,
    using, **kwargs):
    if action == 'post_add':
        for replied_to_comment in instance.replied_to_comments.all():
            moderator_settings = getattr(settings, 'MODERATOR', None)
            offset_timedelta = timedelta(seconds=1)
            if moderator_settings:
                if 'REPLY_BEFORE_COMMENT' in moderator_settings:
                    if moderator_settings['REPLY_BEFORE_COMMENT']:
                        offset_timedelta = timedelta(seconds=-1)

            created = False
            # We use try except DoesNotExist instead of get or create to
            # allow us to add a is_reply_comment to a newly created comment
            # which facilitates realtime_comment_classifier below to distinguish
            # between normal comments and reply comments.
            try:
                comment_obj = Comment.objects.get(
                    content_type=replied_to_comment.content_type,
                    object_pk=replied_to_comment.object_pk,
                    site=replied_to_comment.site,
                    submit_date=replied_to_comment.submit_date + offset_timedelta,
                    user=instance.user,
                )
            except Comment.DoesNotExist:
                comment_obj = Comment(
                    content_type=replied_to_comment.content_type,
                    object_pk=replied_to_comment.object_pk,
                    site=replied_to_comment.site,
                    submit_date=replied_to_comment.submit_date + offset_timedelta,
                    user=instance.user,
                    comment=instance.comment_text,
                )
                comment_obj.is_reply_comment = True
                comment_obj.save()
                created = True

            if not created:
                comment_obj.comment = instance.comment_text
                comment_obj.save()

            if comment_obj not in instance.reply_comments.all():
                instance.reply_comments.add(comment_obj)


@receiver(post_save, sender=Comment)
def realtime_comment_classifier(sender, instance, created, **kwargs):
    """
    Classifies a comment after it has been created.

    This behaviour is configurable by the REALTIME_CLASSIFICATION MODERATOR,
    default behaviour is to classify(True).
    """
    # Only classify if newly created.
    if created:
        moderator_settings = getattr(settings, 'MODERATOR', None)
        if moderator_settings:
            if 'REALTIME_CLASSIFICATION' in moderator_settings:
                if not moderator_settings['REALTIME_CLASSIFICATION']:
                    return

        # Only classify if not a reply comment.
        if not getattr(instance, 'is_reply_comment', False):
            from moderator.utils import classify_comment
            classify_comment(instance)


@receiver(object_liked)
def flag_reported_comments(instance, request, **kwargs):
    if not getattr(instance, 'is_reply_comment', False):
        from moderator.tasks import flag_reported_comments_task
        flag_reported_comments_task.delay(instance)


# Enable voting on Comments (for negative votes/reporting abuse).
secretballot.enable_voting_on(Comment)
