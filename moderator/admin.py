from django.contrib import admin
from django.template import defaultfilters
from moderator.models import ClassifiedComment


class ClassifiedCommentAdmin(admin.ModelAdmin):
    list_display = ('cls', 'comment_text', 'removed')
    list_display_links = ('removed', )
    list_editable = ('cls', )
    list_filter = ('cls', )

    def comment_text(self, obj):
        return defaultfilters.linebreaks(obj.comment.comment)
    comment_text.short_description = 'Comment'
    comment_text.allow_tags = True

    def removed(self, obj):
        return obj.comment.is_removed
    removed.boolean = True

admin.site.register(ClassifiedComment, ClassifiedCommentAdmin)
