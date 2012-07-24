from django.core.management.base import BaseCommand, CommandError
from django.contrib.comments.models import Comment
from moderator import utils
from moderator.models import ClassifiedComment


class Command(BaseCommand):
    help = 'Classifies comments as either spam or '\
           'ham using Bayesian inference.'

    def handle(self, *args, **options):
        self.stdout.write('Classifying, please wait...\n')
        classified_comments = ClassifiedComment.objects.filter(
            cls__in=['spam', 'ham']
        )
        unsure_comments = Comment.objects.exclude(
            pk__in=[classified_comment.pk
                    for classified_comment in classified_comments]
        )

        for comment in unsure_comments:
            classified_comment = utils.classify_comment(comment)
            self.stdout.write('Classified %s as %s\n'
                              % (comment, classified_comment.cls))
