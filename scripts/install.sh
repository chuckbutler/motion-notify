#!/bin/bash

set -eu

pipinstalled=$(which pip)

if [ -z $pipinstalled ]; then
    echo "Unable to locate pip. Is it installed?"
    echo "To install on Ubuntu/Debian systems: sudo apt-get install python-pip"
    exit 0
fi

echo "Installing predependencies for: Dropbox, Pushbullet"
sudo pip install -r requirements.txt -q

if [ -f motion-notify.py ]; then
    echo "Copying motion-notify to /usr/local/bin/mnotify"
    sudo cp motion-notify.py /usr/local/bin/mnotify
    sudo chmod 755 /usr/local/bin/mnotify
fi

# Attempt to run a SED script on the proper settings in motion.conf on behalf
# of the user

if [ ! -f /etc/motion/motion.conf ]; then
   echo " "
   echo "Unable to locate /etc/motion/motion.conf - is motion installed?"
   echo "To install on Ubuntu/Debian systems: sudo apt-get install motion"
   echo " "
   echo "You may re-run this command after installing motion to complete setup"
   exit 0
fi


if [ -f config/motion-notify.cfg.example ]; then
    echo "Copying config/motion-notify.cfg.example to /etc/motion/motion-notify.cfg"
    cp config/motion-notify.cfg.example /etc/motion/motion-notify.cfg
fi


echo "Shall I attempt to update /etc/motion/motion-notify.cfg to call mnotify? [Y/n]"

read doit

if [[ -z $doit ]]; then
  doit='Y'
fi

if [[ $doit == 'y' || $doit == 'Y' ]]; then
    set -x
    sed -i .bak 's/; on_event_start value/on_event_start /usr/local/bin/mnotify/ -n' /etc/motion/motion.conf
    sed -i .bak 's/; on_picture_save value/on_picture_save /usr/local/bin/mnotify -m %f' /etc/motion/motion.conf
    sed -i .bak 's/; on_movie_end value/on_movie_end /usr/local/bin/mnotify -m %f -n' /etc/motion/motion.conf
fi

set +x

echo "Completed, please verify edits in /etc/motion/motion.conf"
echo "When you've verified the edits to motion.conf - promptly edit the"
echo "motion-notify.cfg configuration file to setup the zone, dropbox key"
echo "and pushbullet key."
echo " "
echo "If you find any issues with this software, please file a bug:"
echo "https://github.com/chuckbutler/motion-notify/issues"
echo " "
echo "This is FREE software provided to you under the GPLv3 License. See:"
echo "doc/LICENSE for additional information"
