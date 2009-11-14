from snapboard.models import *
from django.contrib import admin

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

class ThreadAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'category', 'sticky', 'private', 'closed')
    list_filter = ('closed', 'sticky', 'category', 'private',)
    search_fields = ('name',)
    raw_id_field = ('user', 'category')

class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'thread', 'ip')
    search_fields = ('text', 'user')
    raw_id_fields = ('thread', 'user',)
    
class WatchListAdmin(admin.ModelAdmin):
    list_display = ('user', 'thread',)
    search_fields = ('user',)





admin.site.register(Category, CategoryAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Thread, ThreadAdmin)
admin.site.register(WatchList, WatchListAdmin)
admin.site.register(UserSettings)
