from django.core.management.base import BaseCommand, CommandError
from django.contrib.comments.models import Comment
from moderator import classifier
from moderator.models import ClassifiedComment

class Command(BaseCommand):
    help = 'Classifies comments as either spam, ham, noteworthy, or unknown using Bayesian inference.'

    def handle(self, *args, **options):
        self.stdout.write('Classifying, please wait...\n')
        unclassified_comments = Comment.objects.exclude(pk__in=[classified_comment.pk for classified_comment in ClassifiedComment.objects.all()])
        for comment in unclassified_comments:
            try:
                cls = classifier.get_class(comment)
            except ZeroDivisionError:
                cls = 'unknown'
            ClassifiedComment.objects.create(comment=comment, cls=cls)
            self.stdout.write('Classified %s as %s\n' % (comment, cls))
