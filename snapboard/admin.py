from snapboard.models import *
from django.contrib import admin

class PostAdmin(admin.ModelAdmin):
	model = Post
	list_display = ('user', 'date', 'thread', 'ip')
	list_filter = ('censor', 'freespeech', 'date')
	search_fields = ('text', 'user')
	raw_id_fields = ('thread',)
	filter_horizontal = ('private',)

class AbuseReportAdmin(admin.ModelAdmin):
	model = AbuseReport
	list_display = ('post', 'submitter')
	
class ThreadAdmin(admin.ModelAdmin):
	model = Thread
	list_display = ('subject', 'category')
	list_filter = ('closed', 'csticky', 'gsticky', 'category')

class UserBanAdmin(admin.ModelAdmin):
	model = UserBan
	list_display = ('user', 'reason')
	search_fields = ('user', 'reason')
	raw_id_fields = ('user',)

class IPBanAdmin(admin.ModelAdmin):
	model = IPBan
	list_display = ('address', 'reason')
	search_fields = ('address', 'reason')

class GroupAdmin(admin.ModelAdmin):
    model = Group
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('users', 'admins')

admin.site.register(Category)
admin.site.register(Moderator)
admin.site.register(Post, PostAdmin)
admin.site.register(AbuseReport, AbuseReportAdmin)
admin.site.register(Thread, ThreadAdmin)
admin.site.register(UserSettings)
admin.site.register(UserBan, UserBanAdmin)
admin.site.register(IPBan, IPBanAdmin)
admin.site.register(Group, GroupAdmin)

# vim: ai ts=4 sts=4 et sw=4
