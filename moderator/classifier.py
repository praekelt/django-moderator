from moderator.models import Word
from spambayes.classifier import Classifier
from spambayes.hammie import Hammie


class DjangoClassifier(Classifier):
    
    def __init__(self):
        Classifier.__init__(self)
        self.load()

    def load(self):
        """
        Loads state from database. State stores number of ham and spam trained.
        This is stored using the magic words 'trained state' which shouldn't change otherwise. 
        """
        try:
            word_obj = Word.objects.get(word='trained state')
        except Word.DoesNotExist:
            word_obj = Word.objects.create(word='trained state', spam_count=0, ham_count=0)

        self.nspam = word_obj.spam_count
        self.nham = word_obj.ham_count

    def store(self):
        word_obj = Word.objects.get(word='trained state')
        word_obj.spam_count = self.nspam
        word_obj.ham_count = self.nham
        word_obj.save()

    def _wordinfoget(self, word):
        word_info = self.WordInfoClass()
        try:
            word_obj = Word.objects.get(word=word)
            word_info = self.WordInfoClass()
            word_info.__setstate__((word_obj.spam_count, word_obj.ham_count))
        except Word.DoesNotExist:
            pass
        return word_info

    def _wordinfoset(self, word, record):
        try:
            word_obj = Word.objects.get(word=word)
            word_obj.spam_count=record.spamcount
            word_obj.ham_count=record.hamcount
            word_obj.save()
        except Word.DoesNotExist:
            Word.objects.create(word=word, spam_count=record.spamcount, ham_count=record.hamcount)


class SpamClassifier(DjangoClassifier):
    cls = 'spam'
spam_classifier = Hammie(bayes=SpamClassifier(), mode='w')


class NoteworthyClassifier(DjangoClassifier):
    cls = 'noteworthy'
noteworthy_classifier = Hammie(bayes=NoteworthyClassifier(), mode='w')


def get_class(comment):
    score = spam_classifier.score(comment.comment)
    print score
    if score < 0.2:
        return 'ham'
    if score > 0.8:
        return 'spam'
    #noteworthy_class = noteworthy_classifier.score(comment.comment)
    return 'unknown'

def train(comment, cls):
    if cls == 'spam':
        spam_classifier.train(comment.comment, True)
    if cls == 'ham':
        spam_classifier.train(comment.comment, False)
    spam_classifier.store()
