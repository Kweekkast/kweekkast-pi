import os   

def check_and_create_dir(directory):
        if directory.exists() and directory.is_dir():
            dir_msg = f"{directory} exists, no directory was created."
        else:
            os.makedirs(directory, exist_ok=True)
            dir_msg = f"{directory} did not exist, a new directory was created."
        return dir_msg

def check_and_create_file(file):
        if file.exists() and file.is_file():
            file_msg = f"Log file:{file}, already exists."
        else:
            file.touch()
            file_msg = f"Log file: {file}, does not exist yet. File created before first log event."

        return file_msg