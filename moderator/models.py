from django.db import models
from django.contrib.comments.models import Comment
import secretballot


class ClassifiedComment(models.Model):
    comment = models.ForeignKey('comments.Comment')
    cls = models.CharField(
        'Class',
        max_length=64,
        choices=(
            ('spam', 'Spam'),
            ('ham', 'Ham'),
            ('unsure', 'Unsure'),
        )
    )

    class Meta:
        ordering = ['-comment__submit_date', ]


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

# Enable voting on Comments (for negative votes/reporting abuse).
secretballot.enable_voting_on(Comment)
