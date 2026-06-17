from kweekkast_common.loggers.i_logger import ILogger


class DebugLogger(ILogger):

    def LogMessage(self, message: str) -> int:
        print(f"[DEBUG] {message}")
        return 3
