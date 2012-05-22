from django.db import models


class ClassifiedComment(models.Model):
    comment = models.ForeignKey('comments.Comment')
    cls = models.CharField(
        max_length=64,
        choices=(
            ('spam', 'Spam'),
            ('ham', 'Ham'),
            ('unsure', 'Unsure'),
        )
    )

    #def save(self, *args, **kwargs):
    #    #XXX not when created to prevent poison
    #    super(ClassifiedComment, self).save(*args, **kwargs)
    #    from moderator import classifier
    #    classifier.train(self.comment, self.cls)


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
