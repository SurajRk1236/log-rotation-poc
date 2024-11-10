# Log Rotation Script 
This Python script automates log rotation for services like Kafka, Zookeeper, Redis, MongoDB, and Aerospike. It compresses, renames, and archives log files based on custom configurations and schedules rotations via cron expressions, allowing different configurations for environments (e.g., prod, staging, dev).


## Features
       1.     Customizable file size limits, compression types, and naming conventions
       2.     Environment-based configuration for flexibility
       3.     Cron-based scheduling for automatic rotations
       4.     Retention management to clean up older logs

## Prerequisites
       1. Install dependencies: croniter and schedule (pip3 install croniter schedule)

## Configuration
    1. {
        "services": [
            {
                "name": "kafka",
                "log_dir": "/var/log/kafka",
                "archive_dir": "/var/log/kafka/archive",
                "max_size_mb": 50,
                "retain_count": 5,
                "file_naming": "timestamp",
                "compression": "gzip",
                "cron_schedule": "0 0 * * *"
            }
        ]
    }

## Field Valus in Configuration 

       1. log_dir: Log file location
       2. archive_dir: Where rotated files go
       3. max_size_mb: Max file size before rotation
       4. retain_count: Number of rotated files to keep
       5. file_naming: timestamp, numbered, or custom
       6. compression: gzip, bzip2, or none
       7. cron_schedule: Cron expression for rotation timing

## Run Script command
        python3 log_rotate_script.py prod  **(Give the encv based on requiremnts for stage, qa)**




        

