avahi-docker
============

Registers running instances with avahi, for easy local usage of ran containers.

Requirements:

* python-docker
* avahi-utils

Installation
===========


    mkdir -p ~/bin/
    cp -a avahi-docker.py ~/bin/
    # Optional systemd autostarting
    mkdir -p ~/.config/systemd/user/
    cp avahi-docker.service ~/.config/systemd/user/
    systemctl --user daemon-reload
    systemctl --user enable avahi-docker
    systemctl --user start avahi-docker

Now your local running docker containers are available at eg, `http://hostname_my_container_name.local` or 
`http://my_container_name.myhostname.local`



