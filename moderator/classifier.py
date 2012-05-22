from spambayes.hammie import Hammie
from django.conf import settings

DEFAULT_CONF = {
    'CLASSIFIER': 'moderator.storage.DjangoClassifier'
}

# Get conf from settings or fallback to default.
conf = getattr(settings, 'MODERATOR_BAYES_CONF', DEFAULT_CONF)

# Load classifier class from conf string.
parts = conf['CLASSIFIER'].split('.')
module_name = '.'.join(parts[:-1])
class_name = parts[-1]
mod = __import__(module_name, fromlist=[class_name, ])
bayes_class = getattr(mod, class_name)

# Create classifier using determined bayes class object instantiated with conf.
classifier = Hammie(bayes=bayes_class(conf), mode='w')
