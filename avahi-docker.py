#!/usr/bin/python3

import docker
import subprocess
import socket
import argparse
import signal
import itertools
from datetime import datetime, timedelta
from functools import wraps
from threading import Timer
from systemd import daemon

class throttle(object):
    """
    Decorator that prevents a function from being called more than once every
    time period.

    To create a function that cannot be called more than once a minute:

        @throttle(minutes=1)
        def my_fun():
            pass
    """
    def __init__(self, seconds=0, minutes=0, hours=0):
        self.throttle_period = timedelta(
            seconds=seconds, minutes=minutes, hours=hours
        )
        self.time_of_last_call = datetime.min
 
    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            now = datetime.now()
            time_since_last_call = now - self.time_of_last_call
 
            if time_since_last_call > self.throttle_period:
                self.time_of_last_call = now
                t = Timer(0.7, fn, args, kwargs)
                t.start()
                return None
 
        return wrapper

running = []

hostname = socket.gethostname()
c = docker.Client()

def publish(containername, ip):
    cmd = ['avahi-publish', '--no-reverse', '-a', containername, ip]
    r = subprocess.Popen(cmd)
    running.append(r)

def kill_avahis():
    global running
    for r in running:
        try:
            r.terminate()
        except:
            pass

    for r in running:
        if r.returncode is not None:
            continue
        try:
            r.wait(timeout=5)
        except TimeoutError:
            r.kill()

    running = []


@throttle(seconds=0.5)
def register_avahi():
    print("Registering on Avahi...")
    global c
    kill_avahis()
    containers = c.containers()
    for cont in containers:
        info = c.inspect_container(cont['Id'])
        hostnames = (
            hostname + '_' + info['Name'][1:]+'.local',
            info['Name'][1:] + '.' + hostname + '.local',
        )
        ips = [info['NetworkSettings']['IPAddress']]
        ip6 = info['NetworkSettings']['GlobalIPv6Address']
        if ip6:
            ips.append(ip6)
        for containername, ip in itertools.product(hostnames, ips):
            publish(containername, ip)

def list_avahi():
    for cont in c.containers():
        info = c.inspect_container(cont['Id'])
        host = info['Name'][1:]
        print("http://"+hostname+"_"+host+".local/")
        print("http://"+host+"."+hostname+".local/")

# parse args
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list", help="just list domains", action="store_true")
    args = parser.parse_args()
    if args.list:
        list_avahi()
        exit()
    else:
        register_avahi()
    return

parse_args()

def sigterm_handler(_signum, _stack_frame):
    print("Exiting...")
    daemon.notify("STOPPING=1")
    kill_avahis()
    exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)

daemon.notify("READY=1")

for event in c.events(decode=True):
    if event['status'] in ('die', 'stop', 'create', 'start'):
        register_avahi()
