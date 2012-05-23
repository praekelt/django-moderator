Django Moderator
================
**Django Bayesian inference based comment moderation app.**

.. contents:: Contents
    :depth: 5

``django-moderator`` integrates Django's comments framework with SpamBayes_ to automatically classify comments into three categories, *ham*, *spam* or *unknown*, based on previous learning (see Paul Graham's `A Plan for Spam <http://www.paulgraham.com/spam.html>`_ for some background).

Comments classified as *unknown* have to be manually classified as either *spam* or *ham* via admin, thereby training the system to automatically classify similarly worded comments in future.

Comments classified as *spam* will have their ``is_removed`` field set to ``True`` and as such it will no longer be visible in comment listings.

Comments classified as *ham* will remain unchanged and as such will be visible in comment listings.

``django-moderator`` also implements a user friendly admin interface for efficiently moderating comments.


Installation
------------

#. Install or add ``django-moderator`` to your Python path.

#. Add ``moderator`` to your ``INSTALLED_APPS`` setting.

#. Add a ``MODERATOR`` setting to your project's ``settings.py`` file. This setting specifies what classifier storage backend to use (see below) and also at what levels classification will take place::
   
    MODERATOR = {
        'CLASSIFIER': 'moderator.storage.DjangoClassifier',
        'HAM_CUTOFF': 0.3,
        'SPAM_CUTOFF': 0.7,
    }


Storage Backends
----------------
``django-moderator`` includes two SpamBayes_ storage backends, ``moderator.storage.DjangoClassifier`` and ``moderator.storage.RedisClassifier`` respectively. 

.. note::
    ``moderator.storage.RedisClassifier`` is recommended for production environments as it should be much more performant than ``moderator.storage.DjangoClassifier``.


.. _SpamBayes: http://spambayes.sourceforge.net/
