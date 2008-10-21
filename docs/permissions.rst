.. _permissions:

=======================
Using forum permissions
=======================

SNAPboard supports four types of access permissions at the category level. They
are:

    * ``View`` — limits the visibility of the category itself
    * ``Read`` — limits the availability of the contents (topics and posts)
    * ``Post`` — limits the ability to post in existing topics
    * ``Create thread`` — limits the ability to create new discussion topics

Each permission type can be set independently to one of the following values:

    * ``Nobody`` — the permission is granted only to superusers
    * ``All`` (except for ``post`` and ``new thread`` permissions) — no
      restrictions apply
    * ``User`` — the permission is granted to any registered user
    * ``Custom`` — the permission is granted to a group of users, specified by a
      ``group`` object, as well as to any superuser.

Permission settings can be adjusted on the SNAPboard administration interface, 
on the page of their respective category. 

Groups
======

SNAPboard defines groups of user independent of those defined by Django's 
``auth`` application. Each of the four permission settings that belong to 
a category can be set to a custom ``group``. Only users who belong in that group
would be allowed the actions restricted by the permission type for that
category.

For example, if you want your boards to include a private category for selected
members, start by creating a group in the administration interface. Select any
users you want to be members of the group. You can also grant administrative
privileges for users you trust but are not allowed to access the site's
admnistration interface: it will allow them to invite users to the group,
remove users from the group and grant and remove administration privileges for
the group.

Then, create a category and set all four permission settings to ``Custom``.
Then, set the ``View group``, ``Read group``, ``Post group`` and ``Create
thread group`` settings to the group you just created. Anyone not in the
group—and not a superuser—will not be able to view the category in listings,
post into it or access any of its contents.

.. admonition:: Warning

    The administration interface in your project very likely shows two classes
    named ``Group`` whose objects can be edited. SNAPboard is concerned only
    with its own ``Group`` class, not the one provided by Django's ``auth``
    application. While both classes implement groups of users for authorization
    purposes, they are not useful in the same set of cases.

