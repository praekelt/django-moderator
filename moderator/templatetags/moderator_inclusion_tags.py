from django import template
from secretballot.models import Vote
from likes.utils import can_vote

register = template.Library()


@register.inclusion_tag('moderator/inclusion_tags/report_comment_abuse.html',
                        takes_context=True)
def report_comment_abuse(context, obj):
    """
    Checks whether a user can report abuse (has not liked comment previously)
    or has reported abuse previously and renders appropriate response.
    """
    request = context['request']

    can_report = can_vote(obj, request.user, request)
    previously_reported = False
    if not can_report:
        previously_reported = Vote.objects.filter(
            object_id=obj.id,
            token=request.secretballot_token,
            vote='-1'
        ).count() != 0

    context.update({
        'content_obj': obj,
        'previously_reported': previously_reported,
        'can_report': can_report,
        'content_type': "-".join((obj._meta.app_label, obj._meta.module_name)),
    })
    return context
