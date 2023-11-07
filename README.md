# File Monitoring and Backup System

A Python program that monitors changes to files in a specified directory, creates shadow copies of those files, and records modifications with details such as timestamp, user, and the percentage change in text files.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [File Structure](#file-structure)
- [Contributors](#contributors)

## Introduction

This project is a file monitoring and backup system that tracks changes to files in a designated directory and maintains shadow copies of these files. It provides detailed records of file modifications, including the timestamp, user information, and the percentage change in text files.

## Features

- Monitors changes to files in a specified directory.
- Creates and maintains shadow copies of files in a separate directory.
- Records file modifications with timestamp, user information, and percentage change in text files.
- Supports the rollback of files to their previous versions.
- Provides a summary of the status of each monitored file.

## Requirements

Make sure you have the following Python packages installed:

- `watchdog`: A library for monitoring file system events.
- `pytz`: A library for handling time zones.
- `tabulate`: A library for formatting data as tables.

You can install these packages using the `requirements.txt` file:

```sh
pip install -r requirements.txt
```

## Installation

1. Clone the repo
   ```sh
   git clone https://github.com/dhruv-gundecha/filemon.git
   ```
2. Change your working directory to the project folder:
   ```sh
   cd filemon
   ```
   _Ensure that you have the required packages installed (see the "Requirements" section)._
3. Run the program:
   ```sh
   python main.py
   ```
## Usage

- Upon running the program, it will start monitoring the specified directory for file changes.
- The program will create and maintain shadow copies of the monitored files in a separate directory.
- Modifications to text files (e.g., additions, deletions) will be recorded with details such as timestamp, user, and the percentage change.
- You can check the status of monitored files and their modifications.
- Use the program to roll back files to previous versions if necessary.

## File Structure

- main.py: The main Python script that monitors and records file changes..
- requirements.txt: A list of required Python packages.
- file_records.json: A JSON file containing records of file modifications.
- master_table.json: A JSON file maintaining a master table of file modifications.
- modification_log.json: A JSON file recording file modification history.

## Contributors
| Sr No. | Name               |  git-profile     | 
| -------| -------------------| -----------------| 
| 1.     | Dhruv Gundecha     |  dhruv-gundecha  | 
| 2.     | Priyanshu Sahu     |  psahu26         |
| 3.     | Hiral Patel        |  hiral25p        |
