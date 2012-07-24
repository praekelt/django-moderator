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
        ordering = ['-comment__submit_date',]

    def save(self, *args, **kwargs):
        created = not self.pk
        if not created:
            previous_cls = ClassifiedComment.objects.get(pk=self.pk).cls
        if self.cls == 'spam':
            # Remove comment.
            self.comment.is_removed = True
            self.comment.save()
        if self.cls == 'ham':
            # Display comment.
            self.comment.is_removed = False
            self.comment.save()
        super(ClassifiedComment, self).save(*args, **kwargs)

        # Don't train on initial creation to prevent circular training.
        # Initial creation is done by classifycomments management command.
        # We only want to train when a human has made a classification.
        # Don't train when cls is unsure as we can't classify anyway.
        if created or self.cls == 'unsure':
            return
        else:
            # Only train when a cls changed.
            if self.cls != previous_cls:
                from moderator import utils
                if self.cls == 'spam':
                    utils.train(self.comment, is_spam=True)
                    return
                if self.cls == 'ham':
                    utils.train(self.comment, is_spam=False)
                    return
                raise Exception("Unhandled classifications.")


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
