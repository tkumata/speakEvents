## BEGIN INIT INFO
# Provides: speakEvents
# Required-Start: $remote_fs $syslog
# Required-Stop: $remote_fs $syslog
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: Start speakEvents at boot time
# Description: Start speakEvents Server at boot time.
### END INIT INFO

#!/bin/sh
#/etc/init.d/speakEventsService.sh

export USER='pi'

eval cd ~$USER

# Check the state of the command: this'll either be start or stop
case "$1" in
  start)
    # if it's start, then start vncserver using the details below
    echo "Starting spaekEvents for $USER..."
    su $USER -c 'nohup /home/pi/bin/speakEvents/speakEvents.py > /dev/null 2&>1 &'
    echo "...done (speakEvents)"
    ;;
  stop)
    # if it's stop, then just kill the process
    echo "Stopping spaekEvents for $USER "
    su $USER -c 'kill -TERM `ps ax | pgrep -f speakEvents.py`'
    echo "...done (speakEvents)"
    ;;
  *)
    echo "Usage: /etc/init.d/speakEventsService.sh {start|stop}"
    exit 1
    ;;
esac
exit 0
