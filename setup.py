from setuptools import setup, find_packages

setup(
    name='django-moderator',
    version='1.0.1',
    description='Django Bayesian inference based comment moderation app.',
    long_description=open('README.rst', 'r').read() + open('AUTHORS.rst', 'r').read() + open('CHANGELOG.rst', 'r').read(),
    author='Praekelt Foundation',
    author_email='dev@praekelt.com',
    license='BSD',
    url='http://github.com/praekelt/django-moderator',
    packages=find_packages(exclude=['project', ]),
    dependency_links=[
    ],
    install_requires=[
        'django-apptemplates',
        'django-likes>=0.0.6',
        'redis',
        'spambayes',
        'unidecode',
        'django-celery',
    ],
    tests_require=[
        'fakeredis',
        'django-setuptest',
    ],
    test_suite="setuptest.setuptest.SetupTestSuite",
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: BSD License",
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    zip_safe=False,
)
