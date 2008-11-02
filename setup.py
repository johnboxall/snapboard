#!/usr/bin/python
from distutils.core import setup
setup(
    name='snapboard',
    version='0.2.1',
    author='Bo Shi',
    maintainer='SNAPboard developers',
    maintainer_email='snapboard-discuss@googlegroups.com',
    url='http://code.google.com/p/snapboard/',
    description='Bulletin board application for Django.',
    long_description='''SNAPboard is forum/bulletin board application based on the Django web 
framework. It integrates easily in any Django project.

Among its features are:

    * Editable posts with all revisions publicly available
    * Messages posted within threads can be made visible only to selected 
      users
    * BBCode, Markdown and Textile supported for post formatting
    * BBCode toolbar
    * Multiple forums with four types of permissions
    * Forum permissions can be assigned to custom groups of users
    * Group administration can be delegated to end users on a per-group basis
    * Moderators for each forum
    * User preferences
    * Watched topics
    * Abuse reports
    * User and IP address bans that don't automatically spread to other Django
      applications within the project
    * i18n hooks to create your own translations
    * Included translations: French, Russian
    
SNAPboard requires Django 1.0.''',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: New BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Communications :: BBS',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Message Boards',
    ],
    packages=['snapboard',],
    package_dir={'snapboard': 'snapboard'},
    package_data={'snapboard': [
        'media/*/*.*',
        'media/*/*/*.*',
        'templates/*.*',
        'templates/snapboard/*.*',
        'templates/notification/*.*',
        'templates/notification/*/*.*',
        ]},
)

# vim: ai ts=4 sts=4 et sw=4
