from django import template
from django.conf import settings
from likes.utils import can_vote
from moderator.constants import DEFAULT_CONFIG
from secretballot.models import Vote

register = template.Library()


@register.inclusion_tag('moderator/inclusion_tags/report_comment_abuse.html',
                        takes_context=True)
def report_comment_abuse(context, obj):
    """
    Checks whether a user can report abuse (has not liked comment previously)
    or has reported abuse previously and renders appropriate response.

    If requesting user is part of the 'Moderators' group a vote equal to
    ABUSE_CUTOFF setting will be made, thereby immediately marking the comment
    as abusive.
    """
    request = context['request']
    is_moderator = bool(request.user.groups.filter(name='Moderators'))
    abuse_cutoff = getattr(settings, 'MODERATOR', DEFAULT_CONFIG)['ABUSE_CUTOFF']

    can_report = can_vote(obj, request.user, request)
    previously_reported = False
    if not can_report:
        previously_reported = Vote.objects.filter(
            object_id=obj.id,
            token=request.secretballot_token,
            vote__in=['-1', '-%s' % abuse_cutoff]
        ).count() != 0

    context.update({
        'content_obj': obj,
        'previously_reported': previously_reported,
        'can_report': can_report,
        'vote': (-1 * abuse_cutoff) if is_moderator else -1,
        'content_type': "-".join((obj._meta.app_label, obj._meta.module_name)),
    })
    return context
