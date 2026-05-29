class CLISmokeMatrix:
    def __init__(self, settings=None):
        self.settings = settings

    def default_cli_matrix(self) -> list:
        return []

    def commands_for_module(self, module_name) -> list[str]:
        return []

    def critical_commands(self) -> list[str]:
        return []

    def safe_json_commands(self) -> list[str]:
        return []

    def validate_cli_matrix(self) -> list[str]:
        return []
