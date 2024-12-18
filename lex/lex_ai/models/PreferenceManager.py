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
            value = pref.value
        except SystemPreference.DoesNotExist:
            value = default

        return value

    @classmethod
    async def set_preference(cls, key: str, value: dict, user=None, description: str = "") -> None:
        try:
            pref = await sync_to_async(SystemPreference.objects.get)(key=key)
            pref.value = value
            pref.description = description
            pref.modified_by = user
            await sync_to_async(pref.save)()
        except SystemPreference.DoesNotExist:
            await sync_to_async(SystemPreference.objects.create)(
                key=key,
                value=value,
                description=description,
                modified_by=user
            )
