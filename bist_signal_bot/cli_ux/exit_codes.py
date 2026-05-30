from bist_signal_bot.cli_ux.models import CLIStatus, CLIExitCode

class CLIExitCodeMapper:
    def __init__(self, settings=None):
        self.settings = settings

    def code_for_status(self, status: CLIStatus) -> int:
        mapping = {
            CLIStatus.SUCCESS: CLIExitCode.SUCCESS,
            CLIStatus.WARNING: CLIExitCode.WARNING,
            CLIStatus.FAILED: CLIExitCode.INTERNAL_ERROR,
            CLIStatus.BLOCKED: CLIExitCode.SAFETY_BLOCKED,
            CLIStatus.SKIPPED: CLIExitCode.SUCCESS,
            CLIStatus.PARTIAL: CLIExitCode.WARNING,
            CLIStatus.UNKNOWN: CLIExitCode.INTERNAL_ERROR,
        }
        return int(mapping.get(status, CLIExitCode.INTERNAL_ERROR))

    def code_for_exception(self, exc: Exception) -> int:
        exc_name = exc.__class__.__name__
        if "Safety" in exc_name or "Blocked" in exc_name:
            return int(CLIExitCode.SAFETY_BLOCKED)
        if "Confirm" in exc_name:
            return int(CLIExitCode.CONFIRM_REQUIRED)
        if "Config" in exc_name:
            return int(CLIExitCode.CONFIG_ERROR)
        if "Validation" in exc_name:
            return int(CLIExitCode.VALIDATION_ERROR)
        if "NotFound" in exc_name:
            return int(CLIExitCode.NOT_FOUND)
        if "IO" in exc_name or "Storage" in exc_name:
            return int(CLIExitCode.IO_ERROR)

        return int(CLIExitCode.INTERNAL_ERROR)

    def status_for_code(self, code: int) -> CLIStatus:
        if code == CLIExitCode.SUCCESS:
            return CLIStatus.SUCCESS
        elif code == CLIExitCode.WARNING:
            return CLIStatus.WARNING
        elif code == CLIExitCode.SAFETY_BLOCKED:
            return CLIStatus.BLOCKED
        else:
            return CLIStatus.FAILED

    def is_success(self, code: int) -> bool:
        return code == CLIExitCode.SUCCESS

    def is_blocking(self, code: int) -> bool:
        return code in [CLIExitCode.SAFETY_BLOCKED, CLIExitCode.CONFIRM_REQUIRED, CLIExitCode.INTERNAL_ERROR]
