# Scheduling

The pipeline does not install a background service automatically. Schedule the repository's daily/run-daily.sh with the operating system scheduler you already use. The script reads the repository .env file, prevents overlapping runs, broadcasts only ready queued projects, then produces ahead for a later slot.

Queue planning uses local system time. Set PUBLISH_SLOTS to comma-separated 24-hour clock hours (default 10,19). The OS scheduler is separate: configure it to invoke the runner at the time you want each queue check to occur. The two schedules should agree.

## macOS launchd

Create a user LaunchAgent whose ProgramArguments call the absolute path to this clone's daily/run-daily.sh, with one channel argument (en, te, or all). Set WorkingDirectory to the clone root. Set StartCalendarInterval entries to the desired local times. Keep logs outside the repository or in ignored daily/logs/. Review the plist carefully before loading it; scheduled execution can publish queued videos.

## Linux cron

A user cron entry can call the absolute runner path, for example:

    0 10,19 * * * /absolute/path/to/clone/daily/run-daily.sh all >> /absolute/path/to/clone/daily/logs/cron.log 2>&1

Create the log directory first. Use DRY_RUN=1 while validating topic selection, rendering, and queue behavior. Remove DRY_RUN only after reviewing the account connection, upload visibility, and release gate configuration.
