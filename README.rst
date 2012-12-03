Django Moderator
================
**Django community trained Bayesian inference based comment moderation app.**

.. contents:: Contents
    :depth: 5

``django-moderator`` integrates Django's comments framework with SpamBayes_ to classify comments into one of four categories, *ham*, *spam*, *reported* or *unsure*, based on training by users (see Paul Graham's `A Plan for Spam <http://www.paulgraham.com/spam.html>`_ for some background).

Users classify comments as *reported* using a *report abuse* mechanic. Staff users can then classify these *reported* comments as *ham* or *spam*, thereby training the algorithm to automatically classify similarly worded comments in future. Additionally comments the algorithm fails to clearly classify as either *ham* or *spam* will be classified as *unsure*, allowing staff users to manually classify them as well via admin.

Comments classified as *spam* will have their ``is_removed`` field set to ``True`` and as such will no longer be visible in comment listings.

Comments *reported* by users will have their ``is_removed`` field set to ``True`` and as such will no longer be visible in comment listings.

Comments classified as *ham* or *unsure* will remain unchanged and as such will be visible in comment listings.

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
        'ABUSE_CUTOFF': 3,
    }

   Specifically a ``HAM_CUTOFF`` value of ``0.3`` as in this example specifies that any comment scoring less than ``0.3`` during Bayesian inference will be classified as *ham*.  A ``SPAM_CUTOFF`` value of ``0.7`` as in this example specifies that any comment scoring more than ``0.7`` during Bayesian inference will be classified as *spam*. Anything between ``0.3`` and ``0.7`` will be classified as *unsure*, awaiting further manual staff user classification. Additionally an ``ABUSE_CUTOFF`` value of ``3`` as in this example specifies that any comment receiving ``3`` or more abuse reports will be classified as *reported*, awaiting further manual staff user classification. ``HAM_CUTOFF``, ``SPAM_CUTOFF`` and ``ABUSE_CUTOFF`` can be ommited in which case the default cutoffs are ``0.3``, ``0.7`` and ``3`` respectively. 


Classifier Storage Backends
---------------------------
``django-moderator`` includes two SpamBayes_ storage backends, ``moderator.storage.DjangoClassifier`` and ``moderator.storage.RedisClassifier`` respectively. 

.. note::
    ``moderator.storage.RedisClassifier`` is recommended for production environments as it should be much faster than ``moderator.storage.DjangoClassifier``.

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
        'ABUSE_CUTOFF': 3,
    }

You can also create your own backends, in which case take note that the content of ``CLASSIFIER_CONFIG`` will be passed as keyword agruments to your backend's ``__init__`` method.

Usage
-----
Once correctly configured you should use the ``traincommentclassifier`` management command to train the Bayesian inference system using a sample of existing comment objects (comments with ``is_removed`` as ``True`` will be trained as *spam*, *ham* otherwise), i.e.::

    $ ./manage.py traincommentclassifier

.. note::
    The ``traincommentclassifier`` command will remove/clear any existing classification data and start from scratch.


Then you can periodically use the ``classifycomments`` management command to automatically classify comments as either *ham*, *spam*, *reported* or *unsure* based on user reports and previous training, i.e.::

    $ ./manage.py classifycomments

Comments can be manually classified as either *ham* or *spam* via admin list view actions.


.. _SpamBayes: http://spambayes.sourceforge.net/

