#!/bin/sh

### BEGIN INIT INFO
# Provides: speakEvents
# Required-Start: $remote_fs $syslog
# Required-Stop: $remote_fs $syslog
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: Start speakEvents at boot time
# Description: Start speakEvents Server at boot time.
### END INIT INFO

#/etc/init.d/speakEventsService.sh

export USER='pi'
eval cd ~$USER

#set -eu

do_start() {
    # if it's start, then start vncserver using the details below
    MY_PID="`ps axw | pgrep -f speakEvents.py`"
    if [ "${MY_PID:-null}" = null ]; then
        echo "Starting spaekEvents for $USER..."
        su $USER -c 'nohup /home/pi/bin/speakEvents/speakEvents.py > /dev/null 2>&1 &'
        # su $USER -c 'nohup python -u /home/pi/bin/speakEvents/speakEvents.py > /tmp/speakEvents.log &'
        echo "speakEvents starts."
    else
        echo "speakEvents is running already."
    fi
}

do_stop() {
    # if it's stop, then just kill the process
    MY_PID="`ps axw | pgrep -f speakEvents.py`"
    if [ "${MY_PID:-null}" != null ]; then
        echo "Stopping spaekEvents for $USER..."
        kill -9 "$MY_PID"
        echo "speakEvents stop."
    else
        echo "speakEvents stopped already."
    fi
}

# Check the state of the command: this'll either be start or stop
case "$1" in
  start)
    do_start
    ;;
  stop)
    do_stop
    ;;
  restart)
    do_stop
    do_start
    ;;
  *)
    echo "Usage: /etc/init.d/speakEventsService.sh {start|stop|restart}"
    exit 1
    ;;
esac
exit 0
