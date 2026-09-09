"""Cluster 12k -- a credential-shaped column never reaches a response.

Intent: LEX-702. `auth.User` was reachable through the generic
`model_entries` API with its Django password hash in the payload, and the
LEAST-privileged account could read the MOST-privileged account's hash --
verified on a clean harness with a restricted `viewer` reading the admin's
record and getting HTTP 200. The FK hover card then painted
`pbkdf2_sha256$...` on screen wherever a grid held an FK to User (audit log,
history `Meta History User`, `created_by` / `edited_by`), with no tooling
required.

What makes it worth a cluster of its own is WHY the permission system did not
stop it. Field-level read scoping works correctly on that endpoint -- proven
on the harness, where `nav` is present for admin and absent for the viewer.
Two separate things bypassed it:

* `UserModelSerializer` is a plain DRF `ModelSerializer`, NOT a
  `LexSerializer`, so `can_read` / `permission_read` never run for it at all;
* `fields = "__all__"` on a model with a `password` column publishes the
  column, and a model declaring neither permission hook falls through to
  "all fields" even inside `LexSerializer`.

So the fix cannot be a permission rule. It is a name-based refusal at two
enforcement points, and these scenarios pin both, plus the allowlist that
replaced `__all__`.

Cluster 12k -- scenarios 12.49-12.53. Type: C.
Covers: lex/api/serializers/sensitive_fields.py,
        lex/api/serializers/base_serializers.py (model2serializer,
        LexSerializer.to_representation),
        lex/api/views/model_entries/mixins/ModelEntryProviderMixin.py
        (UserModelSerializer).
Run: python -m lex pytest lex/test_project/tests/serializers/test_12k_sensitive_field_denylist.py -v
"""

from __future__ import annotations

import pytest
from django.contrib.auth.models import User
from django.test import SimpleTestCase

from lex.api.serializers import LexSerializer, model2serializer
from lex.api.serializers.sensitive_fields import (
    filter_sensitive_field_names,
    is_sensitive_field_name,
    strip_sensitive_fields,
)
from lex.api.views.model_entries.mixins.ModelEntryProviderMixin import (
    USER_DISPLAY_FIELDS,
    UserModelSerializer,
)

pytestmark = pytest.mark.serializers


def _user_with_password():
    """A user carrying a real Django hash, not a placeholder string."""
    user = User(
        id=7,
        username="admin",
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        is_staff=True,
        is_superuser=True,
    )
    user.set_password("correct horse battery staple")
    return user


class Cluster12k_SensitiveFieldDenylist(SimpleTestCase):
    """The name of a column is enough to disqualify it from a response."""

    # -- 12.49 ---------------------------------------------------------
    def test_12_49_user_serializer_never_emits_the_password_hash(self):
        """The reported exposure, closed: no hash, no privilege flags.

        This is the scenario the issue was filed on. Asserted against a
        REAL `set_password` hash rather than a sentinel, because the whole
        bug was that the genuine value round-tripped.
        """
        user = _user_with_password()
        self.assertTrue(
            user.password.startswith("pbkdf2_"),
            "Guard on the fixture itself -- if set_password stops producing a "
            "hash this test would pass for the wrong reason.",
        )

        payload = UserModelSerializer(user).data

        self.assertNotIn("password", payload)
        self.assertNotIn(
            "is_superuser",
            payload,
            "Not a secret, but it tells an attacker which account is worth "
            "attacking first, and no frontend surface reads it.",
        )
        self.assertNotIn("is_staff", payload)
        self.assertNotIn("user_permissions", payload)

        # Still useful: the display fields the audit / history / hover-card
        # surfaces actually need.
        for field in ("username", "first_name", "last_name", "email"):
            self.assertIn(field, payload)
        self.assertEqual(payload["short_description"], "Ada Lovelace - ada@example.com")

    # -- 12.50 ---------------------------------------------------------
    def test_12_50_user_serializer_is_an_allowlist_not_all(self):
        """`Meta.fields` must stay an explicit tuple, never `"__all__"`.

        The distinction is the fix, not a stylistic preference. This
        serializer is reached by `issubclass(model_class, User)`, so a
        project's own user model lands here too -- under `"__all__"` any
        column it adds is published the day it is added. An allowlist makes
        a new column invisible until someone chooses to expose it.

        There WAS a test asserting `Meta.fields == "__all__"`. It encoded
        the bug, and pinning the inverse is the point of this scenario.
        """
        fields = UserModelSerializer.Meta.fields
        self.assertNotEqual(fields, "__all__")
        self.assertIsInstance(fields, tuple)
        self.assertNotIn("password", fields)
        for field in USER_DISPLAY_FIELDS:
            self.assertIn(field, fields)

    # -- 12.51 ---------------------------------------------------------
    def test_12_51_auto_generated_serializers_drop_the_column(self):
        """`model2serializer` must not publish what `_meta.fields` hands it.

        The generic registration path: a project registers `auth.User` (or
        anything with a `token` column) and gets a serializer built from
        every concrete field. Also covers a caller passing `fields`
        explicitly -- naming `password` by hand is no more allowed than
        inheriting it.
        """
        auto = model2serializer(User)
        self.assertNotIn("password", auto.Meta.fields)
        self.assertIn("username", auto.Meta.fields)

        explicit = model2serializer(User, fields=["username", "password"])
        self.assertNotIn("password", explicit.Meta.fields)
        self.assertIn("username", explicit.Meta.fields)

    # -- 12.52 ---------------------------------------------------------
    def test_12_52_a_declared_sensitive_field_is_stripped_on_output(self):
        """The output boundary catches what a hand-written serializer declares.

        `model2serializer` cannot help here -- the field is declared, not
        inherited. This is the case that makes the fix a floor rather than a
        default: `fields = "__all__"` on a model with a `password` column is
        exactly how LEX-702 happened, and it must not work even when written
        deliberately.

        Note what is NOT asserted: that the field is absent from
        `serializer.fields`. It is present there -- DRF built it. Only the
        emitted representation is clean, which is the boundary that matters.
        """
        class Rogue(LexSerializer):
            class Meta:
                model = User
                fields = ("id", "username", "password")

        user = _user_with_password()
        data = Rogue(user, context={}).data

        self.assertIn("password", Rogue().fields, "DRF still builds the field")
        self.assertNotIn("password", data, "but it must not survive to the wire")
        self.assertEqual(data["username"], "admin")

    # -- 12.53 ---------------------------------------------------------
    def test_12_53_matching_is_narrow_enough_to_be_safe(self):
        """Credential names match; legitimate lookalikes must not.

        A silently missing field is its own bug, so this is deliberately NOT
        a substring search. The frontend's hover-card denylist can afford
        `hash` and `auth` as substrings because it only picks six fields to
        show; a serializer cannot, because `content_hash` and `author` are
        ordinary columns and dropping them would break real features.
        """
        for name in (
            "password", "PASSWORD", "Password",      # case-insensitive
            "token", "salt", "api_key", "private_key", "secret",
            "user_password", "github_token", "stripe_api_key",
        ):
            with self.subTest(sensitive=name):
                self.assertTrue(is_sensitive_field_name(name))

        for name in (
            "content_hash", "hash_algorithm",        # 'hash' is not a match
            "author", "authorised_by", "authority",  # 'auth' is not a match
            "tokenizer", "salted_caramel",           # prefix-only lookalikes
            "username", "email", "nav",
        ):
            with self.subTest(safe=name):
                self.assertFalse(
                    is_sensitive_field_name(name),
                    f"{name} is an ordinary column -- dropping it would be a "
                    f"new bug, not a fix.",
                )

        # The two helpers agree with the predicate.
        self.assertEqual(
            filter_sensitive_field_names(["nav", "password", "author"]),
            ["nav", "author"],
        )
        self.assertEqual(
            strip_sensitive_fields({"nav": 1, "api_key": "x", "author": "a"}),
            {"nav": 1, "author": "a"},
        )
        # Non-dict input is returned untouched rather than raising.
        self.assertEqual(strip_sensitive_fields(None), None)
