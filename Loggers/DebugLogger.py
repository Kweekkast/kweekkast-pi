from Loggers import ILogger

class DebugLogger(ILogger):

    def LogMessage(self, message: str) -> int:
        print(f"[DEBUG] {message}")
        return 3