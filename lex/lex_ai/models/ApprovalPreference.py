from asgiref.sync import sync_to_async

from lex_ai.models.PreferenceManager import PreferenceManager


class ApprovalPreference:
    KEY = "approval_system"

    @classmethod
    async def is_enabled(cls) -> bool:
        prefs = await sync_to_async(PreferenceManager.get_preference)(cls.KEY, {
            'enabled': True,
        })
        return prefs.get('enabled', True)

    @classmethod
    async def set_enabled(cls, enabled: bool, user=None) -> None:
        current_prefs = await sync_to_async(PreferenceManager.get_preference)(cls.KEY, {})
        current_prefs['enabled'] = enabled
        await sync_to_async(PreferenceManager.set_preference)(
            cls.KEY,
            current_prefs,
            user,
            "Approval system configuration"
        )
