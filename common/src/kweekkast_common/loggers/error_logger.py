from kweekkast_common.loggers.i_logger import ILogger


class ErrorLogger(ILogger):

    def LogMessage(self, message: str) -> int:
        print(f"[ERROR] {message}")
        return 2
