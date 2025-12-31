#!/bin/bash
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
# Add user specific bin if needed, though we will use full path to python
cd /Users/mike.davis/work/personal/buckethead.us
echo -n "$(date +%Y-%m-%d-%H:%M) - " >> /Users/mike.davis/work/personal/buckethead.us/monitor.log
/usr/local/bin/python3 monitor_buckethead.py >> /Users/mike.davis/work/personal/buckethead.us/monitor.log 2>&1

