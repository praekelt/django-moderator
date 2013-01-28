from django.contrib import admin
from django.contrib.admin.templatetags.admin_static import static
from django.contrib.admin.util import unquote
from django.contrib.admin.views.main import ChangeList
from django.contrib.comments.admin import CommentsAdmin as DjangoCommentsAdmin
from django.contrib.comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.template import defaultfilters
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from moderator import models, utils

csrf_protect_m = method_decorator(csrf_protect)


class CannedReplyAdmin(admin.ModelAdmin):
    list_display = ('comment', 'site', )
    list_filter = ('site', )


class CommentReplyInline(admin.StackedInline):
    extra = 1
    exclude = ['reply_comment', ]
    model = models.CommentReply
    fk_name = 'replied_to_comment'

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        """
        Limit canned reply options to those with same site as comment.
        """
        field = super(CommentReplyInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == 'canned_reply':
            comment_site = Comment.objects.get(id=request.path.split('/')[-2]).site
            field.queryset = field.queryset.filter(Q(site=comment_site) | Q(site__isnull=True))

        return field


class CommentReplyAdmin(admin.ModelAdmin):
    raw_id_fields = ("replied_to_comment", )
    exclude = ("reply_comment", )


class CommentAdmin(DjangoCommentsAdmin):
    list_display = (
        'comment_text',
        'moderator_reply',
        'content',
        '_user',
        'submit_date',
    )
    inlines = [
        CommentReplyInline,
    ]

    def queryset(self, request):
        """
        Exclude replies from listing since they are displayed inline as part of listing.
        """
        qs = super(CommentAdmin, self).queryset(request)
        return qs.filter(reply_comment_set__isnull=True)

    def get_changelist(self, request):
        """
        Used by AdminModeratorMixin.moderate_view to somewhat hackishly limit comments to only those
        for the object under review, but only if an obj attribute is found on request
        (which means the mixin is being applied and we are not on the standard changelist_view).
        """

        class ModeratorChangeList(ChangeList):
            def get_query_set(self, request):
                qs = super(ModeratorChangeList, self).get_query_set(request)
                obj = getattr(request, 'obj', None)
                if obj:
                    ct = ContentType.objects.get_for_model(obj)
                    qs = qs.filter(content_type=ct, object_pk=obj.pk)
                return qs

        return ModeratorChangeList

    def content(self, obj):
        content = obj.content_object
        content_type = obj.content_type
        url = reverse('admin:%s_%s_moderate' % (content_type.app_label,
                                              content_type.model),
                      args=(content.id,))

        return '<a href="%s">%s</a>' % (url, content)
    content.allow_tags = True

    def moderator_reply(self, obj):
        replies = obj.replied_to_comment_set.all()
        if replies:
            reply = replies[0]
            change_icon = '<img src="%s" alt="change" />' % static('admin/img/icon_changelink.gif')
            return '%s <a href="%s" target="_blank">%s</a>' % (
                change_icon,
                reverse('admin:moderator_commentreply_change', args=(reply.id, )),
                reply.reply_comment.comment
            )
        else:
            add_icon = '<img src="%s" alt="add" />' % static('admin/img/icon_addlink.gif')
            return '%s <a href="%s?replied_to_comment=%s" class="add-another" id="moderator_reply_comment_%s" onclick="return showAddAnotherPopup(this);">Add reply</a>' % (
                add_icon,
                reverse('admin:moderator_commentreply_add'),
                obj.pk,
                obj.pk
            )
    moderator_reply.allow_tags = True

    def comment_text(self, obj):
        return '<a href="%s">%s</a>' % (
            reverse('admin:comments_comment_change', args=(obj.id, )),
            defaultfilters.linebreaks(obj.comment)
        )
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


class AdminModeratorMixin(object):
    @csrf_protect_m
    @transaction.commit_on_success
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        Override change view to add extra context enabling moderate tool.
        """
        context = {
            'has_moderate_tool': True
        }
        if extra_context:
            context.update(extra_context)
        return super(AdminModeratorMixin, self).change_view(
            request=request,
            object_id=object_id,
            form_url=form_url,
            extra_context=context
        )

    def get_urls(self):
        """
        Add aditional moderate url.
        """
        from django.conf.urls import patterns, url
        urls = super(AdminModeratorMixin, self).get_urls()
        info = self.model._meta.app_label, self.model._meta.module_name
        return patterns('',
            url(r'^(.+)/moderate/$',
                self.admin_site.admin_view(self.moderate_view),
                name='%s_%s_moderate' % info),
        ) + urls

    def moderate_view(self, request, object_id, extra_context=None):
        """
        Handles moderate object tool through a somewhat hacky changelist view
        whose queryset is altered via CommentAdmin.get_changelist to only list
        comments for the object under review.
        """
        opts = self.model._meta
        app_label = opts.app_label

        view = CommentAdmin(model=Comment, admin_site=self.admin_site)

        view.list_filter = ()
        view.list_display = (
            'comment_text',
            'moderator_reply',
            '_user',
            'submit_date',
        )

        model = self.model
        obj = get_object_or_404(model, pk=unquote(object_id))
        request.obj = obj
        view.change_list_template = self.change_list_template or [
            'admin/%s/%s/moderate.html' % (app_label, opts.object_name.lower()),
            'admin/%s/moderate.html' % app_label,
            'admin/moderate.html'
        ]
        orig_has_change_permission = self.has_change_permission(request, obj)
        if not orig_has_change_permission:
            raise PermissionDenied
        extra_context = {
            'opts': opts,
            'original': obj,
            'orig_has_change_permission': orig_has_change_permission,
        }
        return view.changelist_view(request, extra_context)


admin.site.register(models.CannedReply, CannedReplyAdmin)
admin.site.unregister(Comment)
admin.site.register(Comment, CommentAdmin)
admin.site.register(models.CommentReply, CommentReplyAdmin)
admin.site.register(models.HamComment, HamCommentAdmin)
admin.site.register(models.ReportedComment, ReportedCommentAdmin)
admin.site.register(models.SpamComment, SpamCommentAdmin)
admin.site.register(models.UnsureComment, UnsureCommentAdmin)
