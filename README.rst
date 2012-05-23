Django Moderator
================
**Django Bayesian inference based comment moderation app.**

.. contents:: Contents
    :depth: 5

``django-moderator`` integrates Django's comments framework with `SpamBayes <http://spambayes.sourceforge.net/>`_ to automatically classify comments into three categories, *ham*, *spam* or *unknown*, based on previous learning (see Paul Graham's `A Plan for Spam <http://www.paulgraham.com/spam.html>`_ for some background).

When a comment is classified as *unknown* admin users need to intervene and classify it as either *spam* or *ham*, thereby training the system to automatically classify similarly worded comments in future.

When a comments is classified as *spam* it's ``is_removed`` field is set to ``True`` and as such it will no longer be visible in comment listings.

``django-moderator`` also implements a user friendly admin interface for efficiently moderating comments.


Installation
------------

#. Install or add ``django-moderator`` to your Python path.

#. Add ``moderator`` to your ``INSTALLED_APPS`` setting.

