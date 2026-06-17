from LoggerComponent.Abstract_Logger import Abstract_Logger

class Console_Logger(Abstract_Logger):

    def _write(self, formatted_message):
        print(formatted_message)

logger = Console_Logger()