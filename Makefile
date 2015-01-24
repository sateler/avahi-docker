all:
	@echo Use make install to install

install:
	mkdir -p ~/bin/
	cp -a avahi-docker.py ~/bin/
	mkdir -p ~/.config/systemd/user/
	cp avahi-docker.service ~/.config/systemd/user/
	systemctl --user daemon-reload
	systemctl --user enable avahi-docker
	systemctl --user start avahi-docker



