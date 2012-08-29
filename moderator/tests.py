from unittest import TestCase

from django.contrib.auth.models import AnonymousUser
from django.contrib.comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from django.core import management
from django.template import Template, Context
from django.test.client import RequestFactory
import fakeredis
from likes.middleware import SecretBallotUserIpUseragentMiddleware
from likes.views import can_vote_test
from moderator.constants import DJANGO_SAMPLE_CONFIG
from moderator.models import ClassifiedComment, ClassifierState, Word
from moderator.storage import DjangoClassifier, RedisClassifier
from secretballot import views
from secretballot.models import Vote


# Before we do anything else monkeypatch FakeRedis into RedisClassifier
RedisClassifier.redis_class = fakeredis.FakeRedis


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


class DjangoClassifierTestCase(BaseClassifierTestCase, TestCase):
    classifier_class = DjangoClassifier
    config = DJANGO_SAMPLE_CONFIG

    def clear(self):
        ClassifierState.objects.all().delete()
        Word.objects.all().delete()

    def test_get_state(self):
        # States are unique for type.
        self.classifier = self.classifier_class(
            **self.config['CLASSIFIER_CONFIG']
        )
        self.classifier = self.classifier_class(
            **self.config['CLASSIFIER_CONFIG']
        )
        self.classifier = self.classifier_class(
            **self.config['CLASSIFIER_CONFIG']
        )
        self.classifier = self.classifier_class(
            **self.config['CLASSIFIER_CONFIG']
        )
        self.failUnlessEqual(ClassifierState.objects.all().count(), 1)

        # On initial creation of state counts are 0.
        state = self.classifier.get_state()
        self.failUnlessEqual(state.spam_count, 0)
        self.failUnlessEqual(state.ham_count, 0)

        # On subsequent load counts are loaded from state.
        self.classifier.nspam = 10
        self.classifier.nham = 20
        self.classifier.store()
        state = self.classifier.get_state()
        self.failUnlessEqual(state.spam_count, 10)
        self.failUnlessEqual(state.ham_count, 20)

    def test_wordinfoget(self):
        # Without any existing words should not create Word,
        # just return word_info with zero counts.
        self.failIf(
            Word.objects.all(),
            "Internal check, no words should exist now"
        )
        word_info = self.classifier._wordinfoget('test')
        self.failUnlessEqual(word_info.spamcount, 0)
        self.failUnlessEqual(word_info.hamcount, 0)

        # With existing words should load counts from DB.
        Word.objects.create(word="test", spam_count=10, ham_count=20)
        word_info = self.classifier._wordinfoget('test')
        self.failUnlessEqual(word_info.spamcount, 10)
        self.failUnlessEqual(word_info.hamcount, 20)

    def test_wordinfoset(self):
        # Without any existing words should create Word with count from record.
        self.failIf(
            Word.objects.all(),
            "Internal check, no words should exist now"
        )
        word_info = self.classifier.WordInfoClass()
        word_info.spamcount = 200
        word_info.hamcount = 500
        self.classifier._wordinfoset('test', word_info)
        word = Word.objects.get()
        self.failUnlessEqual(word.word, 'test')
        self.failUnlessEqual(word.spam_count, 200)
        self.failUnlessEqual(word.ham_count, 500)

        # With existing word should update counts from record.
        word_info.spamcount = 222
        word_info.hamcount = 555
        self.classifier._wordinfoset('test', word_info)
        word = Word.objects.get()
        self.failUnlessEqual(word.word, 'test')
        self.failUnlessEqual(word.spam_count, 222)
        self.failUnlessEqual(word.ham_count, 555)


class RedisClassifierTestCase(BaseClassifierTestCase, TestCase):
    classifier_class = RedisClassifier
    config = {'CLASSIFIER_CONFIG': {}}

    def clear(self):
        self.classifier.redis.flushdb()

    def test_get_state(self):
        # On initial creation of state counts are 0.
        state = self.classifier.get_state()
        self.failUnlessEqual(state.spam_count, 0)
        self.failUnlessEqual(state.ham_count, 0)

        # On subsequent load counts are loaded from state.
        self.classifier.nspam = 10
        self.classifier.nham = 20
        self.classifier.store()
        state = self.classifier.get_state()
        self.failUnlessEqual(state.spam_count, 10)
        self.failUnlessEqual(state.ham_count, 20)

    def test_wordinfoget(self):
        # Without any existing words should not create Word,
        # just return word_info with zero counts.
        word_info = self.classifier._wordinfoget('test')
        self.failUnlessEqual(word_info.spamcount, 0)
        self.failUnlessEqual(word_info.hamcount, 0)

        # With existing words should load counts from Redis.
        self.classifier.redis.set('test_spam_count', '10')
        self.classifier.redis.set('test_ham_count', '20')
        word_info = self.classifier._wordinfoget('test')
        self.failUnlessEqual(word_info.spamcount, 10)
        self.failUnlessEqual(word_info.hamcount, 20)

    def test_wordinfoset(self):
        # Without any existing words should create Word with count from record.
        word_info = self.classifier.WordInfoClass()
        word_info.spamcount = 200
        word_info.hamcount = 500
        self.classifier._wordinfoset('test', word_info)

        word_info = self.classifier._wordinfoget('test')
        self.failUnlessEqual(word_info.spamcount, 200)
        self.failUnlessEqual(word_info.hamcount, 500)

        # With existing word should update counts from record.
        word_info.spamcount = 222
        word_info.hamcount = 555
        self.classifier._wordinfoset('test', word_info)
        word_info = self.classifier._wordinfoget('test')
        self.failUnlessEqual(word_info.spamcount, 222)
        self.failUnlessEqual(word_info.hamcount, 555)


class ManagementCommandTestCase(TestCase):
    def setUp(self):
        from moderator import utils
        from moderator.classifier import classifier
        self.utils = utils
        # Reset words and counts
        classifier.bayes.redis.flushdb()
        classifier.bayes.nspam = 0
        classifier.bayes.nham = 0
        classifier.store()
        Word.objects.all().delete()
        ClassifiedComment.objects.all().delete()
        Comment.objects.all().delete()

    def test_classifycomments(self):

        # Initial comment setup.
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
            comment="awesome spam"
        )
        untrained_comment = Comment.objects.create(
            content_type_id=1,
            site_id=1,
            comment="foo bar"
        )

        # Initial training
        self.utils.train(spam_comment, True)
        self.utils.train(ham_comment, False)

        management.call_command('classifycomments')

        self.failUnlessEqual(ClassifiedComment.objects.all().count(), 4,
                             "We should now have 4 classified comments")

        # Comment previously trained as spam should be classed as spam.
        ClassifiedComment.objects.get(comment=spam_comment, cls='spam')

        # Comment previously trained as ham should be classed as ham.
        ClassifiedComment.objects.get(comment=ham_comment, cls='ham')

        # Comment containing words previously trained as both
        # spam and ham should be classed as unsure.
        ClassifiedComment.objects.get(comment=unsure_comment, cls='unsure')

        # Comment containing words not previously trained should be
        # classed as unsure.
        ClassifiedComment.objects.get(comment=untrained_comment, cls='unsure')


class UtilsTestCase(TestCase):
    def setUp(self):
        from moderator import utils
        from moderator.classifier import classifier
        self.utils = utils
        self.classifier = classifier
        # Reset words and counts to zero.
        self.classifier.bayes.redis.flushdb()
        self.classifier.bayes.nspam = 0
        self.classifier.bayes.nham = 0
        self.classifier.store()

    def test_train(self):
        self.failUnlessEqual(self.classifier.bayes.nham, 0,
                             "No ham has been trained yet, should be 0")
        self.failUnlessEqual(self.classifier.bayes.nspam, 0,
                             "No spam has been trained yet, should be 0")

        comment = Comment.objects.create(
            content_type_id=1,
            site_id=1,
            comment="very bad spam"
        )
        self.utils.train(comment, True)

        # Now we should have word info for each word in the comment,
        # each having spam count of 1 and ham count of 0.
        word_info = self.classifier.bayes._wordinfoget('very')
        self.failUnlessEqual(word_info.spamcount, 1)
        self.failUnlessEqual(word_info.hamcount, 0)
        word_info = self.classifier.bayes._wordinfoget('bad')
        self.failUnlessEqual(word_info.spamcount, 1)
        self.failUnlessEqual(word_info.hamcount, 0)
        word_info = self.classifier.bayes._wordinfoget('spam')
        self.failUnlessEqual(word_info.spamcount, 1)
        self.failUnlessEqual(word_info.hamcount, 0)

        self.failUnlessEqual(self.classifier.bayes.nham, 0,
                             "No ham has been trained yet, should still be 0")
        self.failUnlessEqual(self.classifier.bayes.nspam, 1,
                             "Spam has been trained, should be 1")

        comment = Comment.objects.create(
            content_type_id=1,
            site_id=1,
            comment="awesome tasty ham"
        )
        self.utils.train(comment, False)

        # Now we should have word info for each word in the comment,
        # each having ham count of 1 and spam count of 0.
        word_info = self.classifier.bayes._wordinfoget('awesome')
        self.failUnlessEqual(word_info.spamcount, 0)
        self.failUnlessEqual(word_info.hamcount, 1)
        word_info = self.classifier.bayes._wordinfoget('tasty')
        self.failUnlessEqual(word_info.spamcount, 0)
        self.failUnlessEqual(word_info.hamcount, 1)
        word_info = self.classifier.bayes._wordinfoget('ham')
        self.failUnlessEqual(word_info.spamcount, 0)
        self.failUnlessEqual(word_info.hamcount, 1)

        self.failUnlessEqual(
            self.classifier.bayes.nham,
            1,
            "Ham has been trained, should still 1"
        )
        self.failUnlessEqual(
            self.classifier.bayes.nspam,
            1,
            "No more spam has been trained, should still be 1"
        )

        # Training should store state
        state = self.classifier.bayes.get_state()
        self.failUnlessEqual(state.spam_count, 1)
        self.failUnlessEqual(state.ham_count, 1)

    def test_get_class(self):
        # Initial comment setup.
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
            comment="awesome spam"
        )
        untrained_comment = Comment.objects.create(
            content_type_id=1,
            site_id=1,
            comment="foo bar"
        )

        # Initial training
        self.utils.train(spam_comment, True)
        self.utils.train(ham_comment, False)

        # Comment previously trained as spam should be classed as spam.
        self.failUnlessEqual(self.utils.get_class(spam_comment), 'spam')

        # Comment previously trained as ham should be classed as ham.
        self.failUnlessEqual(self.utils.get_class(ham_comment), 'ham')

        # Comment containing words previously trained as both
        # spam and ham should be classed as unsure.
        self.failUnlessEqual(self.utils.get_class(unsure_comment), 'unsure')

        # Comment containing words not previously trained should be
        # classed as unsure.
        self.failUnlessEqual(self.utils.get_class(untrained_comment), 'unsure')

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
        self.failIf(self.classifier.bayes.nspam)
        self.failIf(self.classifier.bayes.nham)
        self.failUnlessEqual(classified_comment.cls, 'unsure')

        # Providing reported should create reported classification without
        # training, comment should be removed.
        classified_comment = self.utils.classify_comment(
            generic_comment,
            'reported'
        )
        self.failIf(self.classifier.bayes.nspam)
        self.failIf(self.classifier.bayes.nham)
        self.failUnlessEqual(classified_comment.cls, 'reported')
        self.failUnless(classified_comment.comment.is_removed)

        # Without providing a class but with user abuse reports more or equal
        # to cutoff should create reported classification without training,
        # comment should be removed.
        classified_comment = self.utils.classify_comment(abusive_comment)
        self.failUnlessEqual(self.classifier.bayes.nspam, 0)
        self.failIf(self.classifier.bayes.nham)
        self.failUnlessEqual(classified_comment.cls, 'reported')
        self.failUnless(classified_comment.comment.is_removed)

        # Providing ham class should create ham classification and training,
        # comment should not be removed.
        classified_comment = self.utils.classify_comment(ham_comment, 'ham')
        self.failUnlessEqual(self.classifier.bayes.nspam, 0)
        self.failUnlessEqual(self.classifier.bayes.nham, 1)
        self.failUnlessEqual(classified_comment.cls, 'ham')
        self.failIf(classified_comment.comment.is_removed)

        # Providing spam class should create spam classification and training,
        # comment should be removed.
        classified_comment = self.utils.classify_comment(spam_comment, 'spam')
        self.failUnlessEqual(self.classifier.bayes.nspam, 1)
        self.failUnlessEqual(self.classifier.bayes.nham, 1)
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
        self.failUnlessEqual(self.classifier.bayes.nspam, 1)
        self.failUnlessEqual(self.classifier.bayes.nham, 1)
        self.failUnlessEqual(classified_comment.cls, 'spam')
        self.failUnless(classified_comment.comment.is_removed)

        # Hammy comment should now be correctly classified automatically
        # without any training, should not be removed.
        comment = Comment.objects.create(
            content_type_id=1,
            site_id=1,
            comment="tasty ham"
        )
        comment.total_downvotes = 0
        classified_comment = self.utils.classify_comment(comment)
        self.failUnlessEqual(self.classifier.bayes.nspam, 1)
        self.failUnlessEqual(self.classifier.bayes.nham, 1)
        self.failUnlessEqual(classified_comment.cls, 'ham')
        self.failIf(classified_comment.comment.is_removed)

        # Hammy spammy comment should now be correctly classified automatically
        # as unsure without any training, should not be removed.
        classified_comment = self.utils.classify_comment(unsure_comment)
        self.failUnlessEqual(self.classifier.bayes.nspam, 1)
        self.failUnlessEqual(self.classifier.bayes.nham, 1)
        self.failUnlessEqual(classified_comment.cls, 'unsure')
        self.failIf(classified_comment.comment.is_removed)

        # Should raise exception with unkown cls.
        self.assertRaises(Exception, self.utils.classify_comment,
                          unsure_comment, 'unknown_cls')


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

        # With having liked a comment nothing should be rendered.
        out = Template("{% load moderator_inclusion_tags %}"
                       "{% report_comment_abuse comment %}").render(context)
        self.failUnlessEqual(out, '\n')

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

        # With having reported abuse an acknowledgement should be rendered.
        out = Template("{% load moderator_inclusion_tags %}"
                       "{% report_comment_abuse comment %}").render(context)
        self.failUnless('Abuse Reported' in out)
