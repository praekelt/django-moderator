from datetime import timedelta

from django.conf import settings
from django.contrib.comments.models import Comment
from django.db import models
from django.db.models.signals import post_delete, post_save
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
    replied_to_comment = models.ForeignKey(
        'comments.Comment',
        related_name='replied_to_comment_set'
    )
    reply_comment = models.ForeignKey(
        'comments.Comment',
        related_name='reply_comment_set'
    )

    class Meta:
        verbose_name_plural = 'Comment replies'

    def save(self, *args, **kwargs):
        replied_to_comment = self.replied_to_comment

        if self.canned_reply:
            comment_text = self.canned_reply.comment
        else:
            comment_text = self.comment

        try:
            reply_comment = self.reply_comment
            reply_comment.user = self.user
            reply_comment.comment = comment_text
            reply_comment.save()
        except Comment.DoesNotExist:
            self.reply_comment = Comment.objects.create(
                comment=comment_text,
                content_type=replied_to_comment.content_type,
                object_pk=replied_to_comment.object_pk,
                site=replied_to_comment.site,
                submit_date=replied_to_comment.submit_date +
                timedelta(seconds=1),
                user=self.user
            )
        super(CommentReply, self).save(*args, **kwargs)

        # Set comment classification to ham.
        classified_comment, created = ClassifiedComment.objects.get_or_create(
            comment=self.reply_comment, defaults={'cls': 'ham'}
        )
        if created:
            classified_comment.cls = 'ham'
            classified_comment.save()

    def __unicode__(self):
        return "%s: %s..." % (self.reply_comment.name,
                              self.reply_comment.comment[:50])

# Proxy models for admin display.
class HamComment(Comment):
    class Meta:
        proxy=True


class ReportedComment(Comment):
    class Meta:
        proxy=True


class SpamComment(Comment):
    class Meta:
        proxy=True


class UnsureComment(Comment):
    class Meta:
        proxy=True


@receiver(post_delete, sender=CommentReply)
def comment_reply_post_delete_handler(sender, instance, **kwargs):
    instance.reply_comment.delete()


# Enable voting on Comments (for negative votes/reporting abuse).
secretballot.enable_voting_on(Comment)
