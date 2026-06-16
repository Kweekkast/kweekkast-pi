from Loggers import ILogger

class InfoLogger(ILogger):

    def LogMessage(self, message: str) -> int:
        print(f"[INFO] {message}")
        return 0