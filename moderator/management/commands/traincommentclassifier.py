from django.core.management.base import BaseCommand
from django.contrib.comments.models import Comment
from moderator import models, utils

SAMPLE_COUNT = 10000


class Command(BaseCommand):
    help = 'Reinitializes Baysian inference classifier and trains sample of'\
           'existing comments as ham(if not removed) or spam(if removed).'\
           'WARNING: All previous classification data will be reset(wiped).'

    def handle(self, *args, **options):
        # Clear previous classifications.
        utils.clear()
        models.ClassifiedComment.objects.all().delete()

        # Collect sample of ham and spam comments.
        ham_comments = Comment.objects.filter(
            is_removed=False
        ).order_by('?')[:SAMPLE_COUNT]
        spam_comments = Comment.objects.filter(
            is_removed=True
        ).order_by('?')[:SAMPLE_COUNT]
        comments = list(ham_comments) + list(spam_comments)
        comment_count = len(comments)

        self.stdout.write('Learning from %s comments, please wait...' % comment_count)
        self.stdout.flush()

        perc = 0
        ham = []
        spam = []

        # Train and group ham and spam comments as such.
        for i, comment in enumerate(comments):
            new_perc = int(i / (comment_count / 100.0))
            if new_perc > perc:
                perc = new_perc
                self.stdout.write('.')
                self.stdout.flush()
            if comment.is_removed:
                utils.train(comment, is_spam=True)
                spam.append(models.ClassifiedComment(
                    comment=comment,
                    cls='spam',
                ))
            else:
                utils.train(comment, is_spam=False)
                ham.append(models.ClassifiedComment(
                    comment=comment,
                    cls='ham',
                ))

        # Bulk create classified comment objects for trained objects.
        self.stdout.write('\nCreating classification objects, please wait...\n')
        self.stdout.flush()
        models.ClassifiedComment.objects.bulk_create(ham)
        models.ClassifiedComment.objects.bulk_create(spam)

        self.stdout.write('Done!\n')
