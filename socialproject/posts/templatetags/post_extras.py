import re
from django import template
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

HASHTAG_RE = re.compile(r'#(\w+)')


@register.filter
def linkify_hashtags(caption):
    """
    Turns '#sunset' in a caption into a link to the hashtag feed, e.g.
    'Beautiful #sunset today' -> 'Beautiful <a href="/posts/tag/sunset">#sunset</a> today'.
    Caption text is escaped first since this filter marks its output safe.
    """
    if not caption:
        return caption

    def replace(match):
        tag = match.group(1)
        url = reverse('hashtag_feed', args=[tag])
        return f'<a class="text-indigo-500 hover:underline" href="{url}">#{escape(tag)}</a>'

    escaped = escape(caption)
    linked = HASHTAG_RE.sub(replace, str(escaped))
    return mark_safe(linked)
