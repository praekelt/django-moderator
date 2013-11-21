from optparse import make_option

from django.core.management.base import BaseCommand
from django.contrib.comments.models import Comment
from django.db.models import Q
from moderator import utils


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-c', '--count',
                    dest='count',
                    type="int",
                    default=0,
                    help='Number of comments to classify.'),
    )
    help = 'Classifies comments as either spam or '\
           'ham using Bayesian inference and user reports.'

    def handle(self, *args, **options):
        """
        Collect all comments that hasn't already been
        classified or are classified as unsure.
        Order randomly so we don't rehash previously unsure classifieds
        when count limiting.
        """
        comments = Comment.objects.filter(
            Q(classifiedcomment__isnull=True) |
            Q(classifiedcomment__cls='unsure')).order_by('?')
        if options['count']:
            comments = comments[:options['count']]
        comment_count = comments.count()

        self.stdout.write('Classifying %s comments, please wait...' %
                          comment_count)
        self.stdout.flush()

        for comment in comments:
            classified_comment = utils.classify_comment(comment)
            self.stdout.write('%s,' % classified_comment.cls[0])
            self.stdout.flush()

        self.stdout.write('\nDone!\n')
