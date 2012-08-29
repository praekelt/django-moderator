from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.comments.models import Comment
from django.contrib.comments.admin import CommentsAdmin as DjangoCommentsAdmin
from django.core.urlresolvers import reverse
from django.forms.models import BaseInlineFormSet
from django.template import defaultfilters
from moderator import constants
from moderator.models import CannedReply, ClassifiedComment, CommentReply
from moderator import utils


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
    model = CommentReply
    fk_name = 'replied_to_comment'


class ClassifiedCommentInlineFormSet(BaseInlineFormSet):
    def save_existing(self, form, instance, commit=True):
        utils.classify_comment(instance.comment, instance.cls)


class ClassifiedCommentInline(admin.StackedInline):
    formset = ClassifiedCommentInlineFormSet
    extra = 0
    model = ClassifiedComment

    def has_add_permission(self, request):
        return False


class CommentAdmin(DjangoCommentsAdmin):
    list_display = ('comment_text', 'content', 'user', 'submit_date',
                    'classification', 'moderator_replied',)
    list_filter = ('submit_date', ClassificationListFilter)
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
        except ClassifiedComment.DoesNotExist:
            cls = utils.classify_comment(obj).cls
        return cls.title()
        return obj.classifiedcomment_set.get().cls.title()

    def queryset(self, request):
        qs = super(CommentAdmin, self).queryset(request)
        return qs.filter(reply_comment_set__isnull=True)


admin.site.register(CannedReply)
admin.site.unregister(Comment)
admin.site.register(Comment, CommentAdmin)
