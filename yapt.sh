#!/bin/bash

script_home=$(pwd)
script_name="$script_home/yapt.py"
pid_file="$script_home/yapt.pid"
#python_bin=$(which python2.7)

# returns a boolean and optionally the pid
running() {
    local status=false
    if [[ -f $pid_file ]]; then
        # check to see it corresponds to the running script
        local pid=$(< "$pid_file")
        local cmdline=/proc/$pid/cmdline
        # you may need to adjust the regexp in the grep command
        if [[ -f $cmdline ]] && grep -q "$script_name" $cmdline; then
            status="true $pid"
        fi
    fi
    echo $status
}

start() {
    echo "starting $script_name"
    #nohup python2.7 "$script_name" &
    #$python_bin "$script_name" &
    /usr/local/bin/python2.7 "$script_name" &
    echo $! > "$pid_file"
}

stop() {
    # `kill -0 pid` returns successfully if the pid is running, but does not
    # actually kill it.
    #for pid in $(ps -ef | awk '/yapt.py/ {print $2}'); do kill -9 $pid; done
    if [ -f  "$pid_file" ]; then
        kill -0 $1 && kill $1
        kill $(ps aux | grep '[y]apt.py' | awk '{print $2}')
        rm "$pid_file"
        echo "stopped"
    else
        echo "not running"
    fi

}

read running pid < <(running)

case $1 in
    start)
        if $running; then
            echo "$script_name is already running with PID $pid"
        else
            start
        fi
        ;;
    stop)
        stop $pid
        ;;
    restart)
        stop $pid
        start
        ;;
    status)
        if $running; then
            echo "$script_name is running with PID $pid"
        else
            echo "$script_name is not running"
        fi
        ;;
    *)  echo "usage: $0 <start|stop|restart|status>"
        exit
        ;;
esac