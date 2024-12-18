from django.core.cache import cache
from lex.lex_ai.models.SystemPreference import SystemPreference
from typing import Any
from asgiref.sync import sync_to_async

1

class PreferenceManager:
    CACHE_PREFIX = "system_pref_"
    CACHE_TIMEOUT = 3600  # 1 hour

    @classmethod
    async def get_preference(cls, key: str, default: Any = None) -> Any:
        try:
            pref = await sync_to_async(SystemPreference.objects.get)(key=key)
            value = pref
        except SystemPreference.DoesNotExist:
            value = default

        return value

    @classmethod
    async def set_preference(cls, key: str, value: Any, user=None, description: str = "") -> None:
        pref, created = await sync_to_async(SystemPreference.objects.update_or_create)(
            key=key,
            defaults=value
        )


