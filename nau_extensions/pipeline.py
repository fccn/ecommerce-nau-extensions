"""
Custom steps for the `social_core` authentication pipeline.
"""

import logging

from django.contrib.auth import get_user_model
from django.db.models import CharField

log = logging.getLogger(__name__)


def _user_field_max_lengths():
    """
    Map of the ecommerce `User` char fields to their `max_length`.
    """
    return {
        field.name: field.max_length
        for field in get_user_model()._meta.get_fields()  # pylint: disable=protected-access
        if isinstance(field, CharField) and field.max_length
    }


def truncate_user_details(strategy, details, backend, user=None, *args, **kwargs):  # pylint: disable=unused-argument
    """
    Truncate the details received from the LMS to the `max_length` of the
    matching field of the ecommerce `User` model.

    The ecommerce `User.first_name` and `User.last_name` are capped at 30
    characters - kept short on purpose to avoid a large migration - while the
    LMS accepts longer names. Without this step, `create_user` and
    `user_details` save those values as they come and MySQL raises
    `DataError: (1406, "Data too long for column 'last_name' at row 1")`, which
    breaks the `/complete/edx-oauth2/` callback with a 500 and leaves the user
    unable to log in.

    Add this step before `social_core.pipeline.user.create_user` so that both
    the user creation and the later details sync see the truncated values.
    """
    if not details:
        return None

    # Same mapping `social_core.pipeline.user.user_details` uses to convert a
    # detail name into a user model field name.
    field_mapping = strategy.setting("USER_FIELD_MAPPING", {}, backend) or {}
    max_lengths = _user_field_max_lengths()

    truncated = {}
    for name, value in details.items():
        max_length = max_lengths.get(field_mapping.get(name, name))
        if max_length and isinstance(value, str) and len(value) > max_length:
            truncated[name] = value[:max_length]
            log.warning(
                "Truncated the '%s' user detail from %d to %d characters, "
                "the ecommerce user model does not accept a longer value.",
                name,
                len(value),
                max_length,
            )

    if not truncated:
        return None

    return {"details": dict(details, **truncated)}
