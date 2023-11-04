import os
import difflib
from datetime import datetime, timedelta
import pytz
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil
import json
import tabulate
import time

# Define the directories and files for monitoring and storing data
directory_to_monitor = r'D:\AdwCleaner'
shadow_directory = r'D:\AdwCleaner_Shadow'
record_file = "file_records.json"
master_table_file = "master_table.json"
log_file = "modification_log.json"

# Create the shadow directory if it doesn't exist
if not os.path.exists(shadow_directory):
    os.makedirs(shadow_directory)


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self):
        # Initialize data structures for monitoring and logging
        self.file_content = {}
        self.initial_file_lengths = {}
        self.records = {}
        self.log = []
        self.text_file_extensions = ['.txt', '.log', '.json', '.xml','.py']


        # Load previous records if available
        if os.path.exists(record_file):
            with open(record_file, "r") as file:
                self.records = json.load(file)

        if os.path.exists(log_file):
            with open(log_file, "r") as file:
                self.log = json.load(file)

        self.master_table = {}
        if os.path.exists(master_table_file):
            with open(master_table_file, "r") as file:
                self.master_table = json.load(file)

        # Initialize the monitoring data
        for root, dirs, files in os.walk(directory_to_monitor):
            for file in files:
                file_path = os.path.join(root, file)
                self.create_shadow_copy(file_path)
                self.initial_file_lengths[file_path] = len(self.read_file_content(file_path))
                self.file_content[file_path] = self.read_file_content(file_path)

    def create_shadow_copy(self, file_path):
        shadow_path = os.path.join(shadow_directory, os.path.relpath(file_path, directory_to_monitor))

        # Create the directory structure if it doesn't exist
        shadow_dir = os.path.dirname(shadow_path)
        if not os.path.exists(shadow_dir):
            os.makedirs(shadow_dir)

        shutil.copy2(file_path, shadow_path)

    def on_modified(self, event):
        if not event.is_directory:
            file_path = event.src_path

            # Check if the file has a text file extension
            file_extension = os.path.splitext(file_path)[1]
            if file_extension in self.text_file_extensions:
                added_letters, deleted_letters = self.calculate_text_changes(file_path)
                percentage_change = self.calculate_percentage_change(file_path, added_letters, deleted_letters)

                if len(added_letters) == 0 and len(deleted_letters) == 0:
                    # No content change, so we skip logging this
                    pass
                else:
                    self.record_modification(file_path, percentage_change, added_letters, deleted_letters)
            else:
                # For binary files, simply create a shadow copy and log the modification
                self.create_shadow_copy(file_path)
                self.log_binary_modification(file_path)  # Create a separate method for binary file logging

        self.update_master_table_periodically()


    def update_master_table_periodically(self):
        global timer
        current_time = time.time()

        # Check if 5 minutes have passed since the last update
        if current_time - timer >= 20:
            timer = current_time  # Reset the timer

            for file_path in list(self.initial_file_lengths.keys()):
                shadow_path = os.path.join(shadow_directory, os.path.relpath(file_path, directory_to_monitor))
                added_letters, deleted_letters = self.calculate_text_changes1(shadow_path, file_path)
                percentage_change = self.calculate_percentage_change1(shadow_path, added_letters, deleted_letters)
                if len(added_letters) == 0 and len(deleted_letters) == 0:
                    # Record the modification
                    pass
                else:
                    self.update_master_table(shadow_path, os.getlogin(), percentage_change)

                if percentage_change > 101:
                    self.rollback_file(file_path)
                else:
                    self.create_shadow_copy(file_path)

    def list_files(self):
        # List and display the files in the monitored folder
        print("Files in the monitored folder:")
        file_list = []
        file_index = 1
        for root, dirs, files in os.walk(directory_to_monitor):
            for file in files:
                print(f"{file_index}. {file}")
                file_index += 1
                file_list.append(os.path.join(root, file))

        return file_list

    def rollback_file(self, file_path):
        shadow_path = os.path.join(shadow_directory, os.path.relpath(file_path, directory_to_monitor))
        shutil.copy2(shadow_path, file_path)

    def calculate_text_changes1(self, file_path, other_file_path):
        try:
            current_content = self.read_file_content(file_path)
            previous_content = self.file_content.get(other_file_path)

            if previous_content is None:
                self.file_content[other_file_path] = current_content
                return [], []  # No previous content to compare with

            differ = difflib.Differ()
            diff = list(differ.compare(previous_content, current_content))
            added_letters = [word[-1] for word in diff if word.startswith('+ ')]
            deleted_letters = [word[-1] for word in diff if word.startswith('- ')]

            self.file_content[other_file_path] = current_content
            return added_letters, deleted_letters
        except FileNotFoundError:
            return [], []  # No previous content to compare with

    def calculate_text_changes(self, file_path):
        try:
            current_content = self.read_file_content(file_path)
            previous_content = self.file_content.get(file_path)

            if previous_content is None:
                self.file_content[file_path] = current_content
                return [], []  # No previous content to compare with

            differ = difflib.Differ()
            diff = list(differ.compare(previous_content, current_content))
            added_letters = [word[-1] for word in diff if word.startswith('+ ')]
            deleted_letters = [word[-1] for word in diff if word.startswith('- ')]

            self.file_content[file_path] = current_content
            return added_letters, deleted_letters
        except FileNotFoundError:
            return [], []  # No previous content to compare with

    def read_file_content(self, file_path, encodings=['utf-8', 'latin-1', 'iso-8859-1']):
        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as file:
                    return file.read()
            except UnicodeDecodeError:
                continue

        # If all encodings fail, return an empty string or handle the error as needed
        return ""



    def calculate_percentage_change1(self, file_path, added_letters, deleted_letters):
        total_letters = len(added_letters) - len(deleted_letters)
        file_length = len(self.read_file_content(file_path))

        if file_length == 0:
            percentage_change = 100
        else:
            percentage_change = (total_letters / file_length) * 100

        if percentage_change < 0:
            percentage_change = 0 - percentage_change

        percentage_change = round(percentage_change, 2)

        return percentage_change

    def calculate_percentage_change(self, file_path, added_letters, deleted_letters):
        total_letters = len(added_letters) - len(deleted_letters)
        initial_file_length = self.initial_file_lengths.get(file_path, 0)

        if initial_file_length == 0:
            self.initial_file_lengths[file_path] = len(self.read_file_content(file_path))
            if len(added_letters) > 0:
                percentage_change = 100.0
            else:
                percentage_change = 0.0
        else:
            self.initial_file_lengths[file_path] = len(self.read_file_content(file_path))
            percentage_change = (total_letters / initial_file_length) * 100

        if percentage_change < 0:
            percentage_change = 0 - percentage_change

        percentage_change = round(percentage_change, 2)

        return percentage_change

    def record_modification(self, file_path, percentage_change, added_letters, deleted_letters):
        ist = pytz.timezone('Asia/Kolkata')  # Timezone for IST
        timestamp = datetime.now(ist).strftime("%d-%m-%Y %H:%M:%S")
        user_info = os.getlogin()
        process_id = os.getpid()  # Get the current process ID

        modification_record = {
            "filename": file_path,
            "lastmodified timestamp": timestamp,
            "modifying process": f"{process_id} (Modified)",
            "user": user_info,
            "last change percentage": percentage_change,
            "added_letters": "".join(added_letters),
            "deleted_letters": "".join(deleted_letters)
        }

        self.log.append(modification_record)

        with open(master_table_file, "w") as file:
            json.dump(self.master_table, file, indent=4)

        with open(log_file, "w") as file:
            json.dump(self.log, file, indent=4)

    def update_master_table(self, file_path, user_info, percentage_change):
        filename = os.path.basename(file_path)
        modifying_process = "Modified" if percentage_change < 101 else "Rolled Back"

        if filename not in self.master_table:
            self.master_table[filename] = []

        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime("%d-%m-%Y %H:%M:%S.%f")

        if self.master_table[filename] and timestamp == self.master_table[filename][-1]["last_modified_timestamp"]:
            timestamp = self.increment_timestamp(timestamp)

        readable_timestamp = datetime.now(ist).strftime("%d-%m-%Y %H:%M:%S")

        self.master_table[filename].append({
            "last_modified_timestamp": readable_timestamp,
            "modifying_process": f"{modifying_process} ({os.getpid()})",
            "user": user_info,
            "last_change_percentage": percentage_change
        })

        with open(master_table_file, "w") as file:
            json.dump(self.master_table, file, indent=4)

    def increment_timestamp(self, timestamp):
        new_timestamp = datetime.strptime(timestamp, "%d-%m-%Y %H:%M:%S.%f")
        new_timestamp += timedelta(microseconds=1)
        return new_timestamp.strftime("%d-%m-%Y %H:%M:%S.%f")

    def fetch_file_status(self, filename):
        if filename in self.master_table:
            sorted_records = sorted(self.master_table[filename], key=lambda x: x["last_modified_timestamp"],
                                    reverse=True)
            return sorted_records[:5]  # Return the 5 latest records or fewer if there are not enough
        else:
            return []

    def walk_directory(self, dir_path):
        # Recursively traverse the directory and its subdirectories
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                self.create_shadow_copy(file_path)
                self.initial_file_lengths[file_path] = len(self.read_file_content(file_path))
                self.file_content[file_path] = self.read_file_content(file_path)

    def on_created(self, event):
        if event.is_directory:
            # A new directory was created; monitor it for changes
            self.walk_directory(event.src_path)
        else:
            file_path = event.src_path

            # Create a shadow copy of the newly created file
            self.create_shadow_copy(file_path)

    # ... (other event handlers and methods)


if __name__ == "__main__":
    event_handler = FileChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=directory_to_monitor, recursive=True)
    observer.start()

    # Walk the initial directory to handle its files and subdirectories
    event_handler.walk_directory(directory_to_monitor)

    timer = time.time()  # Initialize the global timer

    try:
        while True:
            event_handler.list_files()
            user_choice = input("Enter the number of the file to check status, or 'q' to quit: ")
            if user_choice == 'q':
                break
            elif user_choice.isdigit():
                file_list = []
                for root, dirs, files in os.walk(directory_to_monitor):
                    for file in files:
                        file_list.append(file)

                print("filelist", file_list)
                file_index = int(user_choice) - 1
                if 0 <= file_index < len(file_list):
                    filename_to_check = file_list[file_index]
                    file_status = event_handler.fetch_file_status(filename_to_check)
                    if file_status:
                        print(f"Status for '{filename_to_check}':")
                        headers = ["Last Modified Timestamp", "Modifying Process", "User", "Last Change Percentage"]
                        table_data = [[record["last_modified_timestamp"], record["modifying_process"],
                                       record["user"], f"{record['last_change_percentage']}%"] for record in
                                      file_status]
                        print(tabulate.tabulate(table_data, headers, tablefmt="grid"))
                    else:
                        print(f"No status records found for '{filename_to_check}'")
                else:
                    print("Invalid file number. Please enter a valid number.")
            else:
                print("Invalid input. Please enter a valid number or 'q' to quit.")
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
