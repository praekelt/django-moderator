Django Moderator
================
**Django community trained Bayesian inference based comment moderation app.**

.. contents:: Contents
    :depth: 5

``django-moderator`` integrates Django's comments framework classify comments into one of four categories, *ham*, *spam*, *reported* or *unsure*.

Users classify comments as *reported* using a *report abuse* mechanic. Staff users can then classify these *reported* comments as *ham* or *spam*.

Comments classified as *spam* will have their ``is_removed`` field set to ``True`` and as such will no longer be visible in comment listings.

Comments *reported* by users will have their ``is_removed`` field set to ``True`` and as such will no longer be visible in comment listings.

Comments classified as *ham* or *unsure* will remain unchanged and as such will be visible in comment listings.

``django-moderator`` also implements a user friendly admin interface for efficiently moderating comments.


Installation
------------

#. Install or add ``django-moderator`` to your Python path.

#. Add ``moderator`` to your ``INSTALLED_APPS`` setting.

#. Configure ``django-likes`` as described `here <http://pypi.python.org/pypi/django-likes>`_.

#. Configure ``django-celery`` and add ``moderator.tasks`` to the ``CELERY_IMPORTS = (..., 'moderator.tasks')``

#. Add a ``MODERATOR`` setting to your project's ``settings.py`` file. This setting specifies what classifier storage backend to use (see below) and also classification thresholds::

    MODERATOR = {
        'ABUSE_CUTOFF': 3,
    }

   `ABUSE_CUTOFF`` value of ``3`` as in this example specifies that any comment receiving ``3`` or more abuse reports will be classified as *reported*, awaiting further manual staff user classification.

#. Optionally, if you want an additional **moderate** object tool on admin change views, configure ``django-apptemplates`` as described `here <http://pypi.python.org/pypi/django-apptemplates>`_ , include ``moderator`` as an ``INSTALLED_APP`` before ``django.contrib.admin`` and add ``moderator.admin.AdminModeratorMixin`` as a base class to those admin classes you want the tool available for.

Additional Settings
-------------------
#. By default moderator comment replies are posted chronologically **after** the comment being replied to. If however you need replies to be posted **before** the comment being replied to(for example if you display your comments reverse cronologically), you can specify ``REPLY_BEFORE_COMMENT`` as ``True``, i.e.::

    MODERATOR = {
        ...
        'REPLY_BEFORE_COMMENT': True,
        ...
    }


