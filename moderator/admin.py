from django.contrib import admin
from moderator.models import ClassifiedComment, Word


class ClassifiedCommentAdmin(admin.ModelAdmin):
    list_display = ('cls', 'comment', )
    list_display_links = ('comment', )
    list_editable = ('cls', )


class WordAdmin(admin.ModelAdmin):
    list_display = ('word', 'spam_count', 'ham_count')

admin.site.register(ClassifiedComment, ClassifiedCommentAdmin)
admin.site.register(Word, WordAdmin)
