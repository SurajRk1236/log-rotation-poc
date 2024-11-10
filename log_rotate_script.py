import os
import json
import gzip
import shutil
import datetime
import schedule
from pathlib import Path
from croniter import croniter
from time import sleep
import argparse

# Directory where configuration files are stored
CONFIG_DIR = 'config/'

# Compression types
COMPRESSION_GZIP = 'gzip'
COMPRESSION_BZIP2 = 'bzip2'
COMPRESSION_NONE = 'none'

# File naming conventions
NAMING_TIMESTAMP = 'timestamp'
NAMING_NUMBERED = 'numbered'
NAMING_CUSTOM = 'custom'

# Default settings
DEFAULT_LOG_EXTENSION = '.log'
DEFAULT_DELAY_CHECK_INTERVAL = 5  # in seconds


def get_file_size_mb(file_path):
    return os.path.getsize(file_path) / (1024 * 1024)


def generate_filename(base_name, file_naming, custom_name=None):
    timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    if file_naming == NAMING_TIMESTAMP:
        return f"{base_name}-{timestamp}{DEFAULT_LOG_EXTENSION}"
    elif file_naming == NAMING_NUMBERED:
        return f"{base_name}-{timestamp}{DEFAULT_LOG_EXTENSION}"
    elif file_naming == NAMING_CUSTOM and custom_name:
        return f"{custom_name}-{timestamp}{DEFAULT_LOG_EXTENSION}"
    else:
        raise ValueError("Invalid file naming convention specified")


def compress_file(file_path, compression):
    if compression == COMPRESSION_GZIP:
        with open(file_path, 'rb') as f_in, gzip.open(f"{file_path}.gz", 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        os.remove(file_path)
    elif compression == COMPRESSION_BZIP2:
        shutil.make_archive(file_path, 'bztar', root_dir=os.path.dirname(file_path),
                            base_dir=os.path.basename(file_path))
        os.remove(file_path)
    elif compression == COMPRESSION_NONE:
        pass  # No compression needed
    else:
        raise ValueError("Invalid compression type specified")


def cleanup_old_files(archive_dir, retain_count):
    files = sorted(Path(archive_dir).iterdir(), key=os.path.getmtime, reverse=True)
    for file in files[retain_count:]:
        file.unlink()


def rotate_logs(service_config):
    log_dir = service_config['log_dir']
    archive_dir = service_config['archive_dir']
    max_size_mb = service_config['max_size_mb']
    retain_count = service_config['retain_count']
    file_naming = service_config['file_naming']
    compression = service_config['compression']
    custom_name = service_config.get('custom_name', None)

    os.makedirs(archive_dir, exist_ok=True)

    for log_file in Path(log_dir).glob(f"*{DEFAULT_LOG_EXTENSION}"):
        if log_file.is_file() and get_file_size_mb(log_file) >= max_size_mb:
            base_name = log_file.stem
            new_file_name = generate_filename(base_name, file_naming, custom_name)
            new_file_path = Path(archive_dir) / new_file_name

            # Move and compress the file
            shutil.move(str(log_file), new_file_path)
            compress_file(new_file_path, compression)

            # Create a new empty log file
            log_file.touch()
            print(f"Rotated log for {service_config['name']}: {log_file} -> {new_file_path}")

    # Cleanup old files
    cleanup_old_files(archive_dir, retain_count)
    print(f"Cleanup completed for {service_config['name']}, retaining {retain_count} files.")


def schedule_service_rotation(service_config):
    cron_schedule = service_config['cron_schedule']
    iterator = croniter(cron_schedule, datetime.datetime.now())

    def task():
        rotate_logs(service_config)

    # Calculate the delay for the next execution based on cron
    next_run = iterator.get_next(datetime.datetime)
    delay = (next_run - datetime.datetime.now()).total_seconds()

    # Schedule the rotation
    schedule.every(delay).seconds.do(task)
    print(f"Scheduled log rotation for {service_config['name']} at {next_run}")


def load_config(env):
    config_path = os.path.join(CONFIG_DIR, f"{env}.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file for environment '{env}' not found at {config_path}")

    with open(config_path, 'r') as f:
        return json.load(f)


def main(env):
    config = load_config(env)

    for service_config in config['services']:
        schedule_service_rotation(service_config)

    # Run the scheduled tasks
    # TODO or else we can try using Semaphore which will will do pub sub manner
    while True:
        schedule.run_pending()
        sleep(DEFAULT_DELAY_CHECK_INTERVAL)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Log Rotation Script")
    parser.add_argument('env', type=str, help="Environment to load configuration for (e.g., prod, staging, dev)")
    args = parser.parse_args()

    main(args.env)
