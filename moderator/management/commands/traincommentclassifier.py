from django.core.management.base import BaseCommand
from django.contrib.comments.models import Comment
from moderator import utils


class Command(BaseCommand):
    help = 'Reinitializes(wipes) Baysian inference classifier and trains '\
            'existing removed comments as being spam.'

    def handle(self, *args, **options):
        utils.clear()
        removed_comments = Comment.objects.filter(is_removed=True)
        self.stdout.write('Learing from %s comments, please wait...\n' % len(removed_comments))
        for comment in removed_comments:
            utils.train(comment, is_spam=True)
            self.stdout.write('"%s" learned as spam...\n' % comment.comment)
        self.stdout.write('Done!\n')
