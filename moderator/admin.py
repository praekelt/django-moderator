from django.contrib import admin
from django.contrib.comments.admin import CommentsAdmin as DjangoCommentsAdmin
from django.contrib.comments.models import Comment
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.template import defaultfilters
from moderator import models, utils


class CannedReplyAdmin(admin.ModelAdmin):
    list_display = ('comment', 'site', )
    list_filter = ('site', )


class CommentReplyInline(admin.StackedInline):
    extra = 1
    exclude = ['reply_comment', ]
    model = models.CommentReply
    fk_name = 'replied_to_comment'

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super(CommentReplyInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == 'canned_reply':
            comment_site = Comment.objects.get(id=request.path.split('/')[-2]).site
            field.queryset = field.queryset.filter(Q(site=comment_site) | Q(site__isnull=True))

        return field


class CommentAdmin(DjangoCommentsAdmin):
    list_display = (
        'comment_text',
        'content',
        '_user',
        'submit_date',
        'moderator_replied',
    )
    inlines = [
        CommentReplyInline,
    ]

    def content(self, obj):
        content = obj.content_object
        content_type = obj.content_type
        url = reverse('admin:%s_%s_change' % (content_type.app_label,
                                              content_type.model),
                      args=(content.id,))

        return '<a href="%s">%s</a>' % (url, content)
    content.allow_tags = True

    def moderator_replied(self, obj):
        return bool(obj.replied_to_comment_set.all())
    moderator_replied.boolean = True

    def comment_text(self, obj):
        return defaultfilters.linebreaks(obj.comment)
    comment_text.short_description = 'Comment'
    comment_text.allow_tags = True

    def _user(self, obj):
        url = reverse('admin:auth_user_change', args=(obj.user.id,))

        return '<a href="%s">%s</a>' % (url, obj.user)
    _user.allow_tags = True
    _user.short_description = 'User'


class CommentProxyAdmin(CommentAdmin):
    def queryset(self, request):
        qs = super(CommentProxyAdmin, self).queryset(request)
        return qs.filter(classifiedcomment__cls=self.cls, reply_comment_set__isnull=True)

    def mark_spam(self, modeladmin, request, queryset):
        for comment in queryset:
            utils.classify_comment(comment, cls='spam')
        self.message_user(request, "%s comment(s) successfully marked as spam." % queryset.count())
    mark_spam.short_description = "Mark selected comments as spam"

    def mark_ham(self, modeladmin, request, queryset):
        for comment in queryset:
            utils.classify_comment(comment, cls='ham')
        self.message_user(request, "%s comment(s) successfully marked as ham." % queryset.count())
    mark_ham.short_description = "Mark selected comments as ham"

    def get_actions(self, request):
        actions = {}
        for action in self.actions:
            actions[action] = (
                getattr(self, action),
                action,
                getattr(self, action).short_description,
            )
        return actions


class HamCommentAdmin(CommentProxyAdmin):
    cls = 'ham'
    actions = ['mark_spam', ]


class ReportedCommentAdmin(CommentProxyAdmin):
    cls = 'reported'
    actions = ['mark_ham', 'mark_spam', ]


class SpamCommentAdmin(CommentProxyAdmin):
    cls = 'spam'
    actions = ['mark_ham', ]


class UnsureCommentAdmin(CommentProxyAdmin):
    cls = 'unsure'
    actions = ['mark_ham', 'mark_spam', ]


admin.site.register(models.CannedReply, CannedReplyAdmin)
admin.site.unregister(Comment)
admin.site.register(Comment, CommentAdmin)
admin.site.register(models.HamComment, HamCommentAdmin)
admin.site.register(models.ReportedComment, ReportedCommentAdmin)
admin.site.register(models.SpamComment, SpamCommentAdmin)
admin.site.register(models.UnsureComment, UnsureCommentAdmin)
