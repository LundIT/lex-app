from django.core.cache import cache
from lex.lex_ai.models.SystemPreference import SystemPreference
from typing import Any

1

class PreferenceManager:
    CACHE_PREFIX = "system_pref_"
    CACHE_TIMEOUT = 3600  # 1 hour

    @classmethod
    def get_preference(cls, key: str, default: Any = None) -> Any:
        cache_key = f"{cls.CACHE_PREFIX}{key}"
        value = cache.get(cache_key)

        if value is None:
            try:
                pref = SystemPreference.objects.get(key=key)
                value = pref
                cache.set(cache_key, value, cls.CACHE_TIMEOUT)
            except SystemPreference.DoesNotExist:
                value = default

        return value

    @classmethod
    def set_preference(cls, key: str, value: Any, user=None, description: str = "") -> None:
        cache_key = f"{cls.CACHE_PREFIX}{key}"

        pref, created = SystemPreference.objects.update_or_create(
            key=key,
            defaults=value
        )

        cache.set(cache_key, value, cls.CACHE_TIMEOUT)


