import datetime

#TODO: add this to config file
IMAGE_BASE_PATH = "assets"
IMAGE_MODULE_DIR_PREFIX = "device_"

def datetime_string() -> str:
    return f"{date_only_string()} {time_only_string()}"


def date_only_string() -> str:
    time_format = "%Y-%m-%d"
    date = datetime.datetime.now()
    return str(date.strftime(time_format))


def time_only_string() -> str:
    time_format = "%H-%M-%S-%f"
    date = datetime.datetime.now()
    return str(date.strftime(time_format))[:-3]


def format_log_message(log_severity, sender_class: str, message: str) -> str:
    timestamp = datetime_string()
    return f"{timestamp}: {log_severity.name}: {sender_class}: {message}"

def create_image_directory(image_capture_device: int) -> str:
    return f"{IMAGE_BASE_PATH}/{IMAGE_MODULE_DIR_PREFIX}{image_capture_device}"
