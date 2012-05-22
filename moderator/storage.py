from moderator.models import ClassifierState, Word
from spambayes.classifier import Classifier
from spambayes.hammie import Hammie


class DjangoClassifier(Classifier):
    def __init__(self):
        Classifier.__init__(self)
        # Retrieve classifier state from DB.
        state = self.get_state()

        # Set state from stored value.
        self.nspam = state.spam_count
        self.nham = state.ham_count

    def get_state(self):
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

classifier = Hammie(bayes=DjangoClassifier(), mode='w')
