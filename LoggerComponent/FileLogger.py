from LoggerComponent.Abstract_Logger import Abstract_Logger

class File_Logger(Abstract_Logger):

    def __init__(self):
        self.filePath = "log.txt"

    def _write(self, formatted_message):
        with open(self.filePath, "a") as file:
            file.write(formatted_message + "\n")