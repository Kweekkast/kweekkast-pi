import os   

def check_and_create_dir(directory):
        if directory.exists() and directory.is_dir():
            dir_msg = "Directory exists, no directory was created."
        else:
            os.makedirs(directory, exist_ok=True)
            dir_msg = "Directory did not exist, a new directory was created."
        return dir_msg

def check_and_create_file(file):
        if file.exists() and file.is_file():
            file_msg = "Log file already exists."
            raise UserWarning(f"{file_msg}")
        else:
            file.touch()
            file_msg = "Log file does not exist yet. File created before first log event."

        return file_msg