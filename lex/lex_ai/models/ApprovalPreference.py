from asgiref.sync import sync_to_async

from lex_ai.models.PreferenceManager import PreferenceManager


class ApprovalPreference:
    KEY = "approval_preference"

    @classmethod
    async def is_enabled(cls) -> bool:
        prefs = await PreferenceManager.get_preference(cls.KEY, {
            'enabled': False,
        })
        return prefs.get('enabled')

    @classmethod
    async def set_enabled(cls, enabled: bool, user=None) -> None:
        current_prefs = await PreferenceManager.get_preference(cls.KEY, {})
        current_prefs['enabled'] = enabled
        await PreferenceManager.set_preference(
            cls.KEY,
            current_prefs,
            user,
            "Approval system configuration"
        )
