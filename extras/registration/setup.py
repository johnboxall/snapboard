#!/usr/bin/python
from distutils.core import setup
setup(
    name='sbextra.registration',
    version='0.1',
    author='Julien Demoor',
    maintainer='SNAPboard developers',
    maintainer_email='snapboard-discuss@googlegroups.com',
    url='http://code.google.com/p/snapboard/',
    description='Templates for django-registration 0.5 designed for SNAPboard',
    long_description='''SNAPboard is forum/bulletin board application based on the Django web 
framework. This package contains templates for django-registration that are 
designed to integrate with SNAPboard.''',
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
    packages=['sbextras.registration',],
    package_dir={'sbextras.registration': ''},
    package_data={'sbextras.registration': [
        'templates/*/*.*',
        'locale/*/*/*.*',
        ]},
)

# vim: ai ts=4 sts=4 et sw=4
