#!/bin/python

from __future__ import print_function
from __future__ import unicode_literals

import docker
import json
import subprocess
import socket
from datetime import datetime, timedelta
from functools import wraps
from threading import Timer

c = docker.Client()

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

@throttle(seconds=0.5)
def register_avahi():
    print("Registering on Avahi...")
    global running, c
    for r in running:
        try:
            r.kill()
        except:
            pass
    running = []
    containers = c.containers()
    for cont in containers:
        info = c.inspect_container(cont['Id'])
        containername = hostname + '_' + info['Name'][1:]+'.local'
        cmd = ['avahi-publish-address', '-a', containername, info['NetworkSettings']['IPAddress']]
        r = subprocess.Popen(cmd)
        running.append(r)

# Initial setup
register_avahi()

for event_json in c.events():
    event = json.loads(event_json)
    if event['status'] in ('die', 'stop', 'create', 'start'):
        register_avahi()
