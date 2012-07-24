Django Moderator
================
**Django community trained Bayesian inference based comment moderation app.**

.. contents:: Contents
    :depth: 5

``django-moderator`` integrates Django's comments framework with SpamBayes_ to automatically classify comments into three categories, *ham*, *spam* or *unknown*, based on training by users (see Paul Graham's `A Plan for Spam <http://www.paulgraham.com/spam.html>`_ for some background).

Users classify comments as *spam* using a *report abuse* mechanic, thereby training the algorithm to automatically classify similarly worded comments in future. Additionally comments the algorithm fails to clearly classify as either *ham* or *spam* will be classified as *unknown*, allowing staff users to be manually classify them via admin.

Comments classified as *spam* will have their ``is_removed`` field set to ``True`` and as such will no longer be visible in comment listings.

Comments classified as *ham* or *unknown* will remain unchanged and as such will be visible in comment listings.

``django-moderator`` also implements a user friendly admin interface for efficiently moderating comments.


Installation
------------

#. Install or add ``django-moderator`` to your Python path.

#. Add ``moderator`` to your ``INSTALLED_APPS`` setting.

#. Install and configure ``django-likes`` as described `here <http://pypi.python.org/pypi/django-likes>`_.

#. Add a ``MODERATOR`` setting to your project's ``settings.py`` file. This setting specifies what classifier storage backend to use (see below) and also classification thresholds::
   
    MODERATOR = {
        'CLASSIFIER': 'moderator.storage.DjangoClassifier',
        'HAM_CUTOFF': 0.3,
        'SPAM_CUTOFF': 0.7,
    }

   Specifically a ``HAM_CUTOFF`` value of ``0.3`` as in this example specifies that any comment scoring less than ``0.3`` during Bayesian inference will be classified as *ham*.  A ``SPAM_CUTOFF`` value of ``0.7`` as in this example specifies that any comment scoring more than ``0.7`` during Bayesian inference will be classified as *spam*. Anything between ``0.3`` and ``0.7`` will be classified as *unsure*, awaiting manual user classification. ``HAM_CUTOFF`` and ``SPAM_CUTOFF`` can be ommited in which case the default cutoffs are ``0.3`` and ``0.7`` respectively.


Classifier Storage Backends
---------------------------
``django-moderator`` includes two SpamBayes_ storage backends, ``moderator.storage.DjangoClassifier`` and ``moderator.storage.RedisClassifier`` respectively. 

.. note::
    ``moderator.storage.RedisClassifier`` is recommended for production environments as it should be much more performant than ``moderator.storage.DjangoClassifier``.

To use ``moderator.storage.RedisClassifier`` as your classifier storage backend specify it in your ``MODERATOR`` setting, i.e.::

    MODERATOR = {
        'CLASSIFIER': 'moderator.storage.RedisClassifier',
        'CLASSIFIER_CONFIG': {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': None,
        },
        'HAM_CUTOFF': 0.3,
        'SPAM_CUTOFF': 0.7,
    }

You can also create your own backends, in which case take note that the content of ``CLASSIFIER_CONFIG`` will be passed as keyword agruments to your backend's ``__init__`` method.

Usage
-----

Once correctly configured you'll use the ``classifycomments`` management command to automatically classify comments as either *ham*, *spam* or *unsure* based on previous training, i.e.::

    $ ./manage.py classifycomments

*Unsure* comments can be manually classified as either *ham* or *spam* via the `Classified comments <http://localhost:8000/admin/moderator/classifiedcomment/>`_ page in admin. 


.. _SpamBayes: http://spambayes.sourceforge.net/

