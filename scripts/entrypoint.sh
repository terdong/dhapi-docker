#!/bin/bash

# Create ~/.dhapi/credentials
mkdir -p ~/.dhapi
cat << EOF > ~/.dhapi/credentials
[default]
username = "$DH_USERNAME"
password = "$DH_PASSWORD"
EOF

# Set up a cron job: Run every Sunday at 10am
echo "0 10 * * 0 /app/run_with_env.sh >> /app/output/crontab.log 2>&1" | crontab -
cron -f

# For test
# python /app/run_with_env.py
