from spambayes.hammie import Hammie
from django.conf import settings
from moderator.constants import DEFAULT_CONFIG

# Get conf from settings or fallback to default.
config = getattr(settings, 'MODERATOR', DEFAULT_CONFIG)

# Load classifier class from config string.
parts = config['CLASSIFIER'].split('.')
module_name = '.'.join(parts[:-1])
class_name = parts[-1]
mod = __import__(module_name, fromlist=[class_name, ])
bayes_class = getattr(mod, class_name)

# Create classifier using determined bayes class
# object instantiated with config.
if 'CLASSIFIER_CONFIG' in config:
    classifier_config = config['CLASSIFIER_CONFIG']
else:
    classifier_config = {}
classifier = Hammie(bayes=bayes_class(**classifier_config), mode='w')
