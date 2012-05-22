from django.db import models

class ClassifiedComment(models.Model):
    comment = models.ForeignKey('comments.Comment')
    cls = models.CharField(
        max_length=64,
        choices=(
            ('spam', 'Spam'),
            ('ham', 'Ham'),
            ('noteworthy', 'Noteworthy'),
            ('unknown', 'Unknown'),
        )
    )

    def save(self, *args, **kwargs):
        XXX not when created to prevent poison
        super(ClassifiedComment, self).save(*args, **kwargs)
        from moderator import classifier
        classifier.train(self.comment, self.cls)


class Word(models.Model):
    word = models.CharField(
        max_length=128
    )
    spam_count = models.IntegerField()
    ham_count = models.IntegerField()
