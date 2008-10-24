#!/usr/bin/python
from distutils.core import setup
setup(
    name='snapboard',
    version='0.1.0',
    author='Bo Shi',
    maintainer='SNAPboard developers',
    maintainer_email='snapboard-discuss@googlegroups.com',
    url='http://code.google.com/p/snapboard/',
    description='Bulletin board application for Django.',
    long_description='''SNAPboard is forum/bulletin board application based on the Django web 
framework. It integrates easily in any Django project.

Among its features are:

    * BBcode support
    * multiple forums with a flexible permission system
    * moderators per forum
    * editable posts
    
SNAPboard requires Django 1.0.''',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: New BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
    ],
    packages=['snapboard',]
)

# vim: ai ts=4 sts=4 et sw=4
