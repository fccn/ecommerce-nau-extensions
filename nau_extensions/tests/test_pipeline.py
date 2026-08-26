"""
Tests for the custom `social_core` authentication pipeline steps.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from nau_extensions.pipeline import truncate_user_details

from ecommerce.tests.testcases import TestCase

User = get_user_model()


class FakeStrategy:
    """
    Minimal `social_core` strategy, only the `setting` lookup is used.
    """

    def __init__(self, **settings_overrides):
        self.settings = settings_overrides

    def setting(self, name, default=None, backend=None):  # pylint: disable=unused-argument
        return self.settings.get(name, default)


class TruncateUserDetailsTests(TestCase):
    """
    Test the `truncate_user_details` authentication pipeline step.
    """

    def test_long_last_name_is_truncated(self):
        """
        A last name longer than the 30 characters of the ecommerce user model is
        truncated, so the SSO callback doesn't blow up with a database error.
        """
        last_name = "Nascimento Salles de Almeida Ferreira"
        result = truncate_user_details(
            FakeStrategy(), {"username": "tsalles", "last_name": last_name}, None
        )

        self.assertEqual(result["details"]["last_name"], last_name[:30])
        self.assertEqual(len(result["details"]["last_name"]), 30)
        # The other details are kept.
        self.assertEqual(result["details"]["username"], "tsalles")

    def test_truncated_value_is_saved(self):
        """
        The truncated value fits the user model, which is the whole point of the
        step - saving the original one raises a `DataError` on MySQL.
        """
        details = truncate_user_details(
            FakeStrategy(),
            {"first_name": "a" * 50, "last_name": "b" * 50, "full_name": "c" * 300},
            None,
        )["details"]
        user = User.objects.create(username="long-name", **details)
        user.full_clean(exclude=["password"])

        self.assertEqual(user.first_name, "a" * 30)
        self.assertEqual(user.last_name, "b" * 30)
        self.assertEqual(user.full_name, "c" * 255)

    def test_short_details_are_left_alone(self):
        """
        Details that already fit don't change the pipeline `details`.
        """
        details = {"first_name": "Tiago", "last_name": "Salles", "full_name": "Tiago Salles"}

        self.assertIsNone(truncate_user_details(FakeStrategy(), details, None))

    def test_unknown_and_non_string_details_are_left_alone(self):
        """
        Details without a matching user field, and the non string ones, are ignored.
        """
        details = {
            "not_an_user_field": "x" * 500,
            "is_staff": True,
            "email": None,
        }

        self.assertIsNone(truncate_user_details(FakeStrategy(), details, None))

    def test_empty_details(self):
        """
        An empty `details` is not a failure.
        """
        self.assertIsNone(truncate_user_details(FakeStrategy(), {}, None))

    def test_user_field_mapping_is_honoured(self):
        """
        A detail renamed by `USER_FIELD_MAPPING` is truncated to the length of the
        user field it ends up on, the same mapping `user_details` applies.
        """
        result = truncate_user_details(
            FakeStrategy(USER_FIELD_MAPPING={"surname": "last_name"}),
            {"surname": "b" * 50},
            None,
        )

        self.assertEqual(result["details"]["surname"], "b" * 30)

    def test_step_runs_before_the_user_is_created(self):
        """
        The step is configured before `create_user`, so both the user creation and
        the later `user_details` sync see the truncated values.
        """
        pipeline = list(settings.SOCIAL_AUTH_PIPELINE)

        self.assertIn("nau_extensions.pipeline.truncate_user_details", pipeline)
        self.assertLess(
            pipeline.index("nau_extensions.pipeline.truncate_user_details"),
            pipeline.index("social_core.pipeline.user.create_user"),
        )
