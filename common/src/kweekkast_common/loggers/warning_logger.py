from kweekkast_common.loggers.i_logger import ILogger


class WarningLogger(ILogger):

    def LogMessage(self, message: str) -> int:
        print(f"[WARNING] {message}")
        return 1
