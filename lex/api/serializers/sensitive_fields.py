"""Framework-level refusal to serialise credential-shaped columns.

BUG-F-033 / LEX-702. `auth.User` was reachable through the generic
`model_entries` API with its Django password hash in the payload, and the
least-privileged account could read the most-privileged account's hash. The
frontend's FK hover card then painted it on screen without anyone opening
devtools.

The frontend now refuses to RENDER such a field, which is the right
defence-in-depth, but the fix that matters is here: the value must not leave
the server. This module is the floor -- a project cannot expose a column
named `password` by registering a model, whatever its serializer says.

Scope, deliberately narrow
--------------------------
Matching is by exact name plus a few unambiguous suffixes. It is NOT a
substring search, which the frontend can afford on a six-field hover card
but a serializer cannot: `hash` would swallow a legitimate `content_hash`
and `auth` would swallow `author`. A field silently missing from an API
response is its own bug, so the list stays tight and every strip is logged
once so it is discoverable rather than mysterious.
"""

import logging

logger = logging.getLogger(__name__)

# Exact column names that are never serialised.
SENSITIVE_FIELD_NAMES = frozenset({
    "password",
    "password_hash",
    "secret",
    "secret_key",
    "api_key",
    "api_secret",
    "private_key",
    "access_token",
    "refresh_token",
    "id_token",
    "session_key",
    "salt",
    "token",
})

# Suffixes that make a name unambiguous whatever it is prefixed with:
# `github_token`, `stripe_api_key`, `user_password`.
SENSITIVE_FIELD_SUFFIXES = (
    "_password",
    "_secret",
    "_secret_key",
    "_token",
    "_api_key",
    "_api_secret",
    "_private_key",
)

# (model label, field name) pairs already logged, so a strip is reported once
# per process rather than once per serialised row.
_reported = set()


def is_sensitive_field_name(name):
    """True when a column of this name must never reach a response."""
    lowered = str(name).lower()
    if lowered in SENSITIVE_FIELD_NAMES:
        return True
    return lowered.endswith(SENSITIVE_FIELD_SUFFIXES)


def _report(model_label, field_name):
    key = (model_label or "<unknown>", field_name)
    if key in _reported:
        return
    _reported.add(key)
    logger.warning(
        "lex: refusing to serialise %s.%s -- the field name is credential-shaped "
        "(see lex.api.serializers.sensitive_fields). If this column is genuinely "
        "safe to publish, rename it; the denylist is not configurable by design.",
        key[0],
        field_name,
    )


def filter_sensitive_field_names(names, model_label=None):
    """Drop credential-shaped names from a serializer field list."""
    kept = []
    for name in names:
        if is_sensitive_field_name(name):
            _report(model_label, name)
        else:
            kept.append(name)
    return kept


def strip_sensitive_fields(representation, model_label=None):
    """Pop credential-shaped keys from an outgoing representation, in place.

    The second enforcement point. `filter_sensitive_field_names` keeps the
    auto-generated serializers clean, but a hand-written serializer can
    declare whatever it likes -- and `fields = "__all__"` on a model with a
    `password` column is exactly how LEX-702 happened. This runs at the
    output boundary, so a declared field does not survive either.
    """
    if not isinstance(representation, dict):
        return representation
    for name in [n for n in representation if is_sensitive_field_name(n)]:
        representation.pop(name, None)
        _report(model_label, name)
    return representation
