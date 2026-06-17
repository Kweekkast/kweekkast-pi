from kweekkast_common.logger_component.abstract_logger import AbstractLogger


class ConsoleLogger(AbstractLogger):
    def _write(self, formatted_message: str) -> None:
        print(formatted_message)


logger = ConsoleLogger()
