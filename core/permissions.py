# =========================================================
# permissions.py
# ALITA — Action risk levels + confirmation policy
# =========================================================

from __future__ import annotations

from enum import Enum


class Risk(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# tool_name -> default risk
TOOL_RISK = {
    "screenshot": Risk.LOW,
    "read_screen": Risk.LOW,
    "project_list": Risk.LOW,
    "read_file": Risk.LOW,
    "open_app": Risk.LOW,
    "open_url": Risk.LOW,
    "system_status": Risk.LOW,
    "image_generate": Risk.MEDIUM,
    "write_file": Risk.MEDIUM,
    "run_command": Risk.HIGH,
    "delete_file": Risk.HIGH,
    "send_message": Risk.HIGH,
}


class PermissionEngine:
    def __init__(self, confirm_medium: bool = True, confirm_high_always: bool = True):
        self.confirm_medium = confirm_medium
        self.confirm_high_always = confirm_high_always
        # runtime: waiting for user yes/no
        self._pending = None  # dict or None

    def risk_for(self, tool_name: str) -> Risk:
        return TOOL_RISK.get(tool_name, Risk.MEDIUM)

    def needs_confirmation(self, tool_name: str) -> bool:
        risk = self.risk_for(tool_name)
        if risk == Risk.HIGH:
            return True if self.confirm_high_always else True
        if risk == Risk.MEDIUM:
            return bool(self.confirm_medium)
        return False

    def request_confirm(self, tool_name: str, args: dict, description: str) -> str:
        self._pending = {
            "tool": tool_name,
            "args": args or {},
            "description": description,
        }
        return (
            f"Is action needs confirmation: {description}. "
            f"Bolo 'yes' confirm ke liye, 'no' cancel ke liye."
        )

    def has_pending(self) -> bool:
        return self._pending is not None

    def pending_info(self):
        return self._pending

    def resolve(self, user_text: str):
        """
        Returns (decision, pending_dict_or_None)
        decision: 'yes' | 'no' | 'unknown'
        """
        t = (user_text or "").strip().lower()
        if not self._pending:
            return "unknown", None
        yes = t in ("yes", "y", "haan", "ha", "ok", "okay", "confirm", "kar do", "kardo")
        no = t in ("no", "n", "nahi", "na", "cancel", "mat", "stop")
        pending = self._pending
        if yes:
            self._pending = None
            return "yes", pending
        if no:
            self._pending = None
            return "no", pending
        return "unknown", pending