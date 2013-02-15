from datetime import timedelta

from django.conf import settings
from django.contrib.comments.models import Comment
from django.db import models
from django.db.models.signals import m2m_changed, pre_delete
from django.dispatch import receiver
from moderator import constants
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
        choices=constants.CLASS_CHOICES
    )

    class Meta:
        ordering = ['-comment__submit_date', ]

    def __unicode__(self):
        return self.cls.title()


class ClassifierState(models.Model):
    """
    Stores state (number of ham and spam trained) for classifier type.
    """
    spam_count = models.IntegerField()
    ham_count = models.IntegerField()


class Word(models.Model):
    word = models.CharField(
        max_length=128
    )
    spam_count = models.IntegerField()
    ham_count = models.IntegerField()


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
def comment_reply_post_create_handler(sender, instance, action, model, pk_set, using, **kwargs):
    for replied_to_comment in instance.replied_to_comments.all():
        if instance.canned_reply:
            comment_text = instance.canned_reply.comment
        else:
            comment_text = instance.comment

        #try:
        #    reply_comment = instance.reply_comment
        #    reply_comment.user = instance.user
        #    reply_comment.comment = comment_text
        #    reply_comment.save()
        #except AttributeError, Comment.DoesNotExist:
        instance.reply_comments.add(
            Comment.objects.create(
                comment=comment_text,
                content_type=replied_to_comment.content_type,
                object_pk=replied_to_comment.object_pk,
                site=replied_to_comment.site,
                submit_date=replied_to_comment.submit_date +
                timedelta(seconds=1),
                user=instance.user
            )
        )
        #    instance.save()


# Enable voting on Comments (for negative votes/reporting abuse).
secretballot.enable_voting_on(Comment)
