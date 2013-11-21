from unittest import TestCase

from django.contrib.auth.models import AnonymousUser
from django.contrib.comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from django.template import Template, Context
from django.test.client import RequestFactory
from likes.middleware import SecretBallotUserIpUseragentMiddleware
from likes.views import can_vote_test, like
from secretballot import views
from secretballot.models import Vote


class BaseClassifierTestCase(object):
    def setUp(self):
        if 'CLASSIFIER_CONFIG' not in self.config:
            self.config['CLASSIFIER_CONFIG'] = {}

        self.classifier = self.classifier_class(
            **self.config['CLASSIFIER_CONFIG']
        )
        self.clear()
        self.classifier = self.classifier_class(
            **self.config['CLASSIFIER_CONFIG']
        )

    def test_init(self):
        # State's counts should be loaded in the classifier.
        # On initial creation of classifier counts are 0.
        self.failUnlessEqual(self.classifier.nspam, 0)
        self.failUnlessEqual(self.classifier.nham, 0)

        # On subsequent load counts are loaded from state.
        self.classifier.nspam = 10
        self.classifier.nham = 20
        self.classifier.store()
        self.classifier = self.classifier_class(
            **self.config['CLASSIFIER_CONFIG']
        )
        self.failUnlessEqual(self.classifier.nspam, 10)
        self.failUnlessEqual(self.classifier.nham, 20)

    def test_store(self):
        state = self.classifier.get_state()
        self.failIfEqual(
            state.spam_count,
            50,
            'Internal checking test is not testing existing values'
        )
        self.failIfEqual(
            state.ham_count,
            100,
            'Internal checking test is not testing existing values'
        )

        # On store classifier counts should be saved to DB.
        self.classifier.nspam = 50
        self.classifier.nham = 100
        self.classifier.store()
        state = self.classifier.get_state()
        self.failUnlessEqual(state.spam_count, 50)
        self.failUnlessEqual(state.ham_count, 100)


class UtilsTestCase(TestCase):
    def setUp(self):
        from moderator import utils
        self.utils = utils

    def test_classify_comment(self):
        spam_comment = Comment.objects.create(
            content_type_id=1,
            site_id=1,
            comment="very bad spam"
        )
        ham_comment = Comment.objects.create(
            content_type_id=1,
            site_id=1,
            comment="awesome tasty ham"
        )
        unsure_comment = Comment.objects.create(
            content_type_id=1,
            site_id=1,
            comment="tasty spam"
        )
        generic_comment = Comment.objects.create(
            content_type_id=1,
            site_id=1,
            comment="foo bar"
        )
        abusive_comment = Comment.objects.create(
            content_type_id=1,
            site_id=1,
            comment="abusive comment"
        )

        for i in range(0, 3):
            Vote.objects.create(
                content_type=ContentType.objects.get_for_model(Comment),
                object_id=abusive_comment.id,
                token=i,
                vote=-1
            )

        # Providing unsure should create unsure classification without
        # training.
        classified_comment = self.utils.classify_comment(
            generic_comment,
            'unsure'
        )
        self.failUnlessEqual(classified_comment.cls, 'unsure')

        # Providing reported should create reported classification without
        # training, comment should be removed.
        classified_comment = self.utils.classify_comment(
            generic_comment,
            'reported'
        )
        self.failUnlessEqual(classified_comment.cls, 'reported')
        self.failUnless(classified_comment.comment.is_removed)

        # Without providing a class but with user abuse reports more or equal
        # to cutoff should create reported classification without training,
        # comment should be removed.
        classified_comment = self.utils.classify_comment(abusive_comment)
        self.failUnlessEqual(classified_comment.cls, 'reported')
        self.failUnless(classified_comment.comment.is_removed)

        # Providing ham class should create ham classification and training,
        # comment should not be removed.
        classified_comment = self.utils.classify_comment(ham_comment, 'ham')
        self.failUnlessEqual(classified_comment.cls, 'ham')
        self.failIf(classified_comment.comment.is_removed)

        # Providing spam class should create spam classification and training,
        # comment should be removed.
        classified_comment = self.utils.classify_comment(spam_comment, 'spam')
        self.failUnlessEqual(classified_comment.cls, 'spam')
        self.failUnless(classified_comment.comment.is_removed)

        # Spammy comment should now be correctly classified automatically
        # without any training, should be removed.
        comment = Comment.objects.create(
            content_type_id=1,
            site_id=1,
            comment="bad spam"
        )
        comment.total_downvotes = 0
        classified_comment = self.utils.classify_comment(comment)
        self.failUnlessEqual(classified_comment.cls, 'unsure')

        # Hammy comment should now be correctly classified automatically
        # without any training, should not be removed.
        comment = Comment.objects.create(
            content_type_id=1,
            site_id=1,
            comment="tasty ham"
        )
        comment.total_downvotes = 0
        classified_comment = self.utils.classify_comment(comment)
        self.failUnlessEqual(classified_comment.cls, 'unsure')
        self.failIf(classified_comment.comment.is_removed)

        # Hammy spammy comment should now be correctly classified automatically
        # as unsure without any training, should not be removed.
        classified_comment = self.utils.classify_comment(unsure_comment)
        self.failUnlessEqual(classified_comment.cls, 'unsure')
        self.failIf(classified_comment.comment.is_removed)

        # Should raise exception with unkown cls.
        self.assertRaises(Exception, self.utils.classify_comment,
                          unsure_comment, 'unknown_cls')

        classified_comment = self.utils.classify_comment(spam_comment, 'spam')


class InclusionTagsTestCase(TestCase):

    def test_report_comment_abuse(self):
        # Prepare context.
        context = Context()
        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        request.META['HTTP_USER_AGENT'] = 'testing_agent'
        request.secretballot_token = SecretBallotUserIpUseragentMiddleware().\
            generate_token(request)
        comment = Comment.objects.create(
            content_type_id=1,
            site_id=1,
            comment="abuse report testing comment"
        )
        context['request'] = request
        context['comment'] = comment

        # Without having actioned anything on the comment the
        # Report Abuse action should be rendered.
        out = Template("{% load moderator_inclusion_tags %}"
                       "{% report_comment_abuse comment %}").render(context)
        self.failUnless('Report Abuse' in out)

        # Like a comment.
        views.vote(
            request,
            content_type='.'.join((comment._meta.app_label,
                                   comment._meta.module_name)),
            object_id=comment.id,
            vote=1,
            redirect_url='/',
            can_vote_test=can_vote_test
        )

        # Reset previous like and test it applied.
        Vote.objects.all().delete()

        # Without having actioned anything on the comment the
        # Report Abuse action should be rendered.
        out = Template("{% load moderator_inclusion_tags %}"
                       "{% report_comment_abuse comment %}").render(context)
        self.failUnless('Report Abuse' in out)

        # Dislike/report an abuse comment.
        views.vote(
            request,
            content_type='.'.join((comment._meta.app_label,
                                   comment._meta.module_name)),
            object_id=comment.id,
            vote=-1,
            redirect_url='/',
            can_vote_test=can_vote_test
        )

        self.assertEqual(Vote.objects.all().count(), 1)

        #repeat votes should not count
        views.vote(
            request,
            content_type='.'.join((comment._meta.app_label,
                                   comment._meta.module_name)),
            object_id=comment.id,
            vote=-1,
            redirect_url='/',
            can_vote_test=can_vote_test
        )

        self.assertEqual(Vote.objects.all().count(), 1)

    def test_report_comment_abuse_signal(self):
        # Prepare context.
        context = Context()
        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        request.META['HTTP_REFERER'] = '/'
        request.META['HTTP_USER_AGENT'] = 'testing_agent'
        request.secretballot_token = SecretBallotUserIpUseragentMiddleware().\
            generate_token(request)
        comment = Comment.objects.create(
            content_type_id=1,
            site_id=1,
            comment="abuse report testing comment"
        )
        context['request'] = request
        context['comment'] = comment
        content_type = '-'.join((comment._meta.app_label,
                                 comment._meta.module_name))

        # Reset previous like and test it applied.
        Vote.objects.all().delete()

        # Report an abuse comment - 1st
        like(
            request,
            content_type=content_type,
            id=comment.id,
            vote=-1
        )
        self.assertEqual(Vote.objects.all().count(), 1)
        self.failIf(Comment.objects.get(pk=comment.pk).is_removed)

        # Report an abuse comment - 2nd
        request.META['HTTP_USER_AGENT'] = 'testing_agent_2'
        request.secretballot_token = SecretBallotUserIpUseragentMiddleware().\
            generate_token(request)
        like(
            request,
            content_type=content_type,
            id=comment.id,
            vote=-1,
        )
        self.assertEqual(Vote.objects.all().count(), 2)
        self.failIf(Comment.objects.get(pk=comment.pk).is_removed)

        # Report an abuse comment - 3rd
        request.META['HTTP_USER_AGENT'] = 'testing_agent_3'
        request.secretballot_token = SecretBallotUserIpUseragentMiddleware().\
            generate_token(request)
        like(
            request,
            content_type=content_type,
            id=comment.id,
            vote=-1,
        )
        self.assertEqual(Vote.objects.all().count(), 3)
        self.failUnless(Comment.objects.get(pk=comment.pk).is_removed)
