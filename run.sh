#!/bin/bash

# Configuration
PYTHON_SCRIPT="realtime_original.py"
MORNING_START="0900"
MORNING_END="1130"
AFTERNOON_START="1300"
AFTERNOON_END="1500"
CHECK_INTERVAL=60  # Check every 60 seconds

# Function to check if current time is within trading hours
is_trading_time() {
    local current_time=$(date +%H%M)
    local current_day=$(date +%u)

    # Check if it's a weekday (1-5)
    if ((current_day >= 1 && current_day <= 5)); then
        if ((current_time >= MORNING_START && current_time < MORNING_END)) ||
           ((current_time >= AFTERNOON_START && current_time < AFTERNOON_END)); then
            return 0
        fi
    fi
    return 1
}

# Function to run the Python script
run_trading_script() {
    export MORNING_START="${MORNING_START:0:2}:${MORNING_START:2:2}"
    export MORNING_END="${MORNING_END:0:2}:${MORNING_END:2:2}"
    export AFTERNOON_START="${AFTERNOON_START:0:2}:${AFTERNOON_START:2:2}"
    export AFTERNOON_END="${AFTERNOON_END:0:2}:${AFTERNOON_END:2:2}"

    python3 "$PYTHON_SCRIPT"
}

# Function to get next trading session start time
get_next_session_start() {
    local current_time=$(date +%H%M)
    local current_day=$(date +%u)

    if ((current_day >= 1 && current_day <= 5)); then
        if ((current_time < MORNING_START)); then
            echo "$MORNING_START"
        elif ((current_time < AFTERNOON_START)); then
            echo "$AFTERNOON_START"
        else
            # Next day's morning session
            date -d "tomorrow $MORNING_START" +%s
            return
        fi
    else
        # Next Monday's morning session
        date -d "next Monday $MORNING_START" +%s
        return
    fi
    # Convert to epoch seconds
    date -d "today ${1:0:2}:${1:2:2}" +%s
}

# Main loop
while true; do
    if is_trading_time; then
        if ! pgrep -f "$PYTHON_SCRIPT" > /dev/null; then
            echo "Starting trading script..."
            run_trading_script &
        fi
        sleep $CHECK_INTERVAL
    else
        if pgrep -f "$PYTHON_SCRIPT" > /dev/null; then
            echo "Stopping trading script..."
            pkill -f "$PYTHON_SCRIPT"
        fi
        next_start=$(get_next_session_start)
        current_time=$(date +%s)
        sleep_duration=$((next_start - current_time))
        echo "Sleeping until next trading session ($(date -d @$next_start '+%Y-%m-%d %H:%M:%S'))"
        sleep $sleep_duration
    fi
done