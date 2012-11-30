from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.comments.models import Comment
from django.contrib.comments.admin import CommentsAdmin as DjangoCommentsAdmin
from django.core.urlresolvers import reverse
from django.forms.models import BaseInlineFormSet
from django.template import defaultfilters
from moderator import constants, models, utils


class ClassificationListFilter(SimpleListFilter):
    title = "classification"
    parameter_name = "classification"

    def lookups(self, request, model_admin):
        return constants.CLASS_CHOICES

    def queryset(self, request, queryset):
        """
        Returns queryset filtered on categories and primary_category.
        """
        if self.value():
            return queryset.filter(classifiedcomment__cls=self.value())


class CommentReplyInline(admin.StackedInline):
    extra = 0
    exclude = ['reply_comment', ]
    model = models.CommentReply
    fk_name = 'replied_to_comment'


class ClassifiedCommentInlineFormSet(BaseInlineFormSet):
    def save_existing(self, form, instance, commit=True):
        utils.classify_comment(instance.comment, instance.cls)


class ClassifiedCommentInline(admin.StackedInline):
    formset = ClassifiedCommentInlineFormSet
    extra = 0
    model = models.ClassifiedComment

    def has_add_permission(self, request):
        return False


class CommentProxyAdmin(admin.ModelAdmin):
    ordering = ('-submit_date',)
    def queryset(self, request):
        return self.model.objects.filter(id__in=models.ClassifiedComment.objects.filter(cls=self.cls))


class HamCommentAdmin(CommentProxyAdmin):
    cls = 'ham'


class ReportedCommentAdmin(CommentProxyAdmin):
    cls = 'reported'


class SpamCommentAdmin(CommentProxyAdmin):
    cls = 'spam'


class UnsureCommentAdmin(CommentProxyAdmin):
    cls = 'unsure'

admin.site.register(models.HamComment, HamCommentAdmin)
admin.site.register(models.ReportedComment, ReportedCommentAdmin)
admin.site.register(models.SpamComment, SpamCommentAdmin)
admin.site.register(models.UnsureComment, UnsureCommentAdmin)


class CommentAdmin(DjangoCommentsAdmin):
    list_display = (
        'comment_text',
        'content',
        'user',
        'submit_date',
        'classification',
        'moderator_replied',
    )
    list_filter = (ClassificationListFilter, )
    inlines = [
        ClassifiedCommentInline,
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

    def classification(self, obj):
        try:
            cls = obj.classifiedcomment_set.get().cls
            return cls.title()
        except models.ClassifiedComment.DoesNotExist:
            return 'Unclassified'

    def queryset(self, request):
        qs = super(CommentAdmin, self).queryset(request)
        return qs.filter(reply_comment_set__isnull=True)


admin.site.register(models.CannedReply)
admin.site.unregister(Comment)
admin.site.register(Comment, CommentAdmin)
