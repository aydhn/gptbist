from typing import Any, Dict, List, Optional

class CLICommandRegistry:
    def __init__(self, settings=None):
        self.settings = settings
        self._commands = [
            {"path": "healthcheck", "module": "healthcheck"},
            {"path": "config", "module": "config"},
            {"path": "scan symbols", "module": "scanner"},
            {"path": "context build", "module": "context"},
            {"path": "review-workflow", "module": "review"},
            {"path": "qa release-gate", "module": "qa"},
            {"path": "ops status", "module": "ops"},
            {"path": "bootstrap demo", "module": "bootstrap"},
        ]

    def registered_commands(self) -> List[Dict[str, Any]]:
        return self._commands

    def command_exists(self, command_path: str) -> bool:
        return any(c["path"] == command_path for c in self._commands)

    def command_metadata(self, command_path: str) -> Optional[Dict[str, Any]]:
        for c in self._commands:
            if c["path"] == command_path:
                return c
        return None

    def commands_by_module(self, module_name: str) -> List[Dict[str, Any]]:
        return [c for c in self._commands if c.get("module") == module_name]

    def validate_registry(self) -> List[str]:
        errors = []
        if not self._commands:
            errors.append("Registry is empty")
        return errors
def get_local_ui_commands():
    return [
        {"name": "local-ui status", "description": "Check local UI status"},
        {"name": "local-ui capabilities", "description": "Detect capabilities"},
        {"name": "local-ui pages", "description": "List layout pages"},
        {"name": "local-ui preview", "description": "Preview a page"},
        {"name": "local-ui launch", "description": "Launch TUI/Fallback"},
        {"name": "local-ui shortcuts", "description": "List shortcuts"},
        {"name": "local-ui validate", "description": "Validate safety and layout"},
        {"name": "local-ui report", "description": "Generate UI report"},
        {"name": "local-ui recent", "description": "List recent runs"},
        {"name": "local-ui config", "description": "Show UI configuration"}
    ]
