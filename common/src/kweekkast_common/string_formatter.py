import datetime


def create_image_path(image_capture_device: int) -> str:
    return f"Assets/Device_{image_capture_device}/{fetch_custom_datetime_string()}.png"


def fetch_custom_datetime_string() -> str:
    time_format = "%Y-%m-%d %H-%M-%S-%f"
    date = datetime.datetime.now()
    return str(date.strftime(time_format))[:-3]


def fetch_custom_date_string() -> str:
    time_format = "%Y-%m-%d"
    date = datetime.datetime.now()
    return str(date.strftime(time_format))


def fetch_custom_time_string() -> str:
    time_format = "%H-%M-%S-%f"
    date = datetime.datetime.now()
    return str(date.strftime(time_format))[:-3]


def format_log_message(log_severity, sender_class: str, message: str) -> str:
    timestamp = fetch_custom_datetime_string()
    return f"{timestamp}: {log_severity.name}: {sender_class}: {message}"


SESSION_LOG_DIRECTORY_PATH = f"logs/{fetch_custom_date_string()}/"
SESSION_LOG_FILE_NAME = f"log_session_{fetch_custom_time_string()}.txt"
SESSION_LOG_FILE_PATH = SESSION_LOG_DIRECTORY_PATH + SESSION_LOG_FILE_NAME
