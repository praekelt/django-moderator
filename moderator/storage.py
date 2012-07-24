from moderator.models import ClassifierState, Word
import redis
from spambayes.classifier import Classifier


class DjangoClassifier(Classifier):
    def __init__(self):
        Classifier.__init__(self)

        # Set state from DB stored value.
        state = self.get_state()
        self.nspam = state.spam_count
        self.nham = state.ham_count

    def get_state(self):
        """
        Retrieves classifier state from DB.
        """
        try:
            return ClassifierState.objects.get()
        except ClassifierState.DoesNotExist:
            return ClassifierState.objects.create(spam_count=0, ham_count=0)

    def store(self):
        """
        Stores classifier state in DB.
        """
        state = self.get_state()
        state.spam_count = self.nspam
        state.ham_count = self.nham
        state.save()

    def _wordinfoget(self, word):
        """
        Get word info from DB.
        If no word exists in the DB use zero values.
        """
        word_info = self.WordInfoClass()
        try:
            word_obj = Word.objects.get(word=word)
            word_info = self.WordInfoClass()
            word_info.__setstate__((word_obj.spam_count, word_obj.ham_count))
        except Word.DoesNotExist:
            pass
        return word_info

    def _wordinfoset(self, word, record):
        """
        Save word info to DB.
        If no word exists it is created with record counts.
        """
        try:
            word_obj = Word.objects.get(word=word)
            word_obj.spam_count = record.spamcount
            word_obj.ham_count = record.hamcount
            word_obj.save()
        except Word.DoesNotExist:
            Word.objects.create(
                word=word,
                spam_count=record.spamcount,
                ham_count=record.hamcount
            )


class RedisClassifier(Classifier):
    redis_class = redis.StrictRedis
    state_keys = {
        'spam': 'redis_classifier_spam_state_key',
        'ham': 'redis_classifier_ham_state_key',
    }

    def __init__(self, *args, **kwargs):
        Classifier.__init__(self)

        self.redis = self.redis_class(**kwargs)
        # Set state from Redis stored value.
        state = self.get_state()
        self.nspam = state.spam_count
        self.nham = state.ham_count

    def get_state(self):
        """
        Retrieves classifier state from Redis.
        """
        class State(object):
            def __init__(self, spam_count, ham_count):
                self.spam_count = spam_count
                self.ham_count = ham_count

        spam = self.redis.get(self.state_keys['spam'])
        ham = self.redis.get(self.state_keys['ham'])
        if spam is None:
            self.redis.set(self.state_keys['spam'], '0')
            spam = self.redis.get(self.state_keys['spam'])
        if ham is None:
            self.redis.set(self.state_keys['ham'], '0')
            ham = self.redis.get(self.state_keys['ham'])

        return State(spam_count=int(spam), ham_count=int(ham))

    def store(self):
        """
        Stores classifier state in Redis.
        """
        self.redis.set(self.state_keys['spam'], str(self.nspam))
        self.redis.set(self.state_keys['ham'], str(self.nham))

    def _wordinfoget(self, word):
        """
        Get word info from Redis.
        If no word exists in the Redis use zero values.
        Spam and ham counts are stored using Redis key formed by appending
        appended '_spam_count' and '_ham_count' to word in question.
        """
        spam_count = self.redis.get('%s_spam_count' % word)
        ham_count = self.redis.get('%s_ham_count' % word)
        if spam_count is None:
            spam_count = 0
        if ham_count is None:
            ham_count = 0

        word_info = self.WordInfoClass()
        word_info.__setstate__((int(spam_count), int(ham_count)))
        return word_info

    def _wordinfoset(self, word, record):
        """
        Save word info to Redis.
        If no word exists it is created with record counts.
        """
        self.redis.set('%s_spam_count' % word, record.spamcount)
        self.redis.set('%s_ham_count' % word, record.hamcount)
