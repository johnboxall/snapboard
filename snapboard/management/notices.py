from django.db.models import signals
from django.utils.translation import ugettext_noop as _

# We use ugettext_noop here because we want makemessages to find the strings
# They will be translated when they are fetched from the database and 
# displayed to the user.

try:
	from notification import models as notification

	def create_notice_types(**kwargs):
		notification.create_notice_type(
				"private_post_received",
				_("Private post received"),
				_("A private message addressed to you has been posted in a discussion."))
		notification.create_notice_type(
				"new_post_in_watched_thread",
				_("New post in a watched thread"),
				_("A new message has been posted in a watched discussion."))
		notification.create_notice_type(
				"group_invitation_received",
				_("Invitation to join a group"),
				_("You have been invited to join a group."))
		notification.create_notice_type(
				"group_invitation_cancelled",
				_("Invitation to join a group cancelled"),
				_("An invitation you received to join a group has been cancelled."))
		notification.create_notice_type(
				"group_admin_rights_granted",
				_("Group admin rights granted"),
				_("You have been granted admin rights on a group."))
		notification.create_notice_type(
				"group_admin_rights_removed",
				_("Group admin rights removed"),
				_("Your admin rights on a group have been removed."))
		notification.create_notice_type(
				"new_group_admin",
				_("New group admin"),
				_("There is a new admin in a group."))
		notification.create_notice_type(
				"new_group_member",
				_("New group member"),
				_("There is a new member in a group."))

	signals.post_syncdb.connect(create_notice_types, sender=notification)
except ImportError:
	print "Skipping creation of NoticeTypes as notification app not found"

