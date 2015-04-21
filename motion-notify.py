#!/usr/bin/python2
'''
Created on 23rd February 2014

@author: Andrew Dean

Motion Notify v0.1 - uploads images and video to Google Drive and sends
notification via email. Detects whether someone is home by checking the local
network for an IP address or MAC address and only sends email if nobody is
home. Allows hours to be defined when the system will be active regardless of
network presence.

Sends an email to the user at that start of an event and uploads images
throughout the event. At the end of an event the video is uploaded to Google
Drive and a link is emailed to the user. Files are deleted once they are
uploaded.

Based on the Google Drive uploader developed by Jeremy Blythe
(http://jeremyblythe.blogspot.com) and
pypymotion (https://github.com/7AC/pypymotion) by Wayne Dyck
'''

# This file is part of Motion Notify.
#
# Motion Notify is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Motion Notify is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Motion Notify.  If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime

import os.path
import sys
import subprocess
import argparse

import ConfigParser

import logging.handlers
import traceback

# Service libs
import dropbox
from pushbullet import Pushbullet

log = logging.getLogger('MotionNotify')
hdlr = logging.handlers.RotatingFileHandler('/var/tmp/motion-notify.log',
                                            maxBytes=1048576,
                                            backupCount=3)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.INFO)


def logExceptHook(t, v, tb):
    log.error(traceback.format_exception(t, v, tb))

sys.excepthook = logExceptHook


class MotionNotify:

    def __init__(self, config_file_path, notify):
        log.info("Loading config")
        # Load config
        config = ConfigParser.ConfigParser()
        config.read(config_file_path)

        # [zone]
        self.region = config.get('zone', 'region')
        # Delete the local video file after the upload
        self.cleanup = config.get('zone', 'cleanup')

        # set sleeping hours
        self.zone_guard_start = 1
        self.zone_guard_end = 7

        # [pushbullet]
        # disable pushbullet notifications if false
        self.pushbullet_enabled = config.get('pushbullet', 'enabled')
        # pushbullet API Key - obtain from: https://www.pushbullet.com/account
        self.apikey = config.get('pushbullet', 'apikey')
        # Subject line for notification message
        self.subject = config.get('pushbullet', 'subject')
        # First line of notification message
        self.message = config.get('pushbullet', 'message')
        self.event_message = config.get('pushbullet', 'event_message')
        if self.pushbullet_enabled and notify:
            self._create_pushbullet_client()

        # [dropbox]
        # Folder in Dropbox where you want the videos to go
        self.folder = config.get('dropbox', 'folder')
        self.folder_link = config.get('dropbox', 'folder_link')
        self.access_token = config.get('dropbox', 'access_token')
        self._create_dropbox_client()

        # set defaults for LAN config - this is shakey at best
        self.network = None
        self.ip_addresses = None

        # [LAN]
        try:
            # Space separated list of IP addresses
            self.ip_addresses = config.get('LAN', 'ip_addresses').split(',')
        except ConfigParser.NoSectionError, ConfigParser.NoOptionError:
            pass

    def _create_dropbox_client(self):
        ''' Allocate a DropBox client for re-use '''
        self.dropbox = dropbox.client.DropboxClient(self.access_token)
        log.info("linked account: {}".format(self.dropbox.account_info()))

    def _upload_dropbox_file(self, filepath):
        ''' Upload any file passed to this method '''
        filename = filepath.split('/')[-1]
        dropbox_file = "/{}/{}".format(self.folder, filename)
        with open(filepath, 'rb') as f:
            response = self.dropbox.put_file(dropbox_file, f)
        return response

    def _create_pushbullet_client(self):
        self.pushbullet = Pushbullet(self.apikey)
        log.info("initialized pushbullet client")

    def _push_notice(self, msg):
        ''' Pushes a notice via pushbullet '''
        if not self.pushbullet:
            return
        self.pushbullet.push_note(self.subject.format(self.region),
                                  msg.format(self.region))

    def _system_active(self):
        if self._in_guard_window():
            log.info('In guard window - sending notifications')
            return True
        elif self._system_active_ip_based():
            return True
        else:
            return False

    def _in_guard_window(self):
        now = datetime.now()
        start = now.hour >= self.zone_guard_start
        end = now.hour < self.zone_guard_end
        return start and end

    def _system_active_ip_based(self):
        if not self.ip_addresses:
            log.info("No IP addresses configured - skipping IP check")
            return True
        addresses = self.ip_addresses
        for address in addresses:
            test_string = 'bytes from'
            results = subprocess.Popen(['ping', '-c1', address],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT
                                       ).stdout.readlines()
            for result in results:
                if test_string in result:
                    log.info('IP detected - someone is home')
                    return False
        log.info('IP inactive - nobody is home - system is active')
        return True

    def upload_media(self, media_file_path, notify):
        if self._system_active():
            self._upload_dropbox_file(media_file_path)
            self._push_notice("{} - view at {}".format(self.message,
                                                       self.folder_link))

        if self.cleanup:
            log.info("Deleting: %s", media_file_path)
            os.remove(media_file_path)

    def send_start_event(self, notify):
        """Send an email showing that the event has started"""
        if self._system_active():
            msg = "{} - view at {}".format(self.event_message,
                                           self.folder_link)
            self._push_notice(msg)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='MNotify - A notifier for Motion',
                                     description='Based on the Motion Notifier'
                                     ' scripts developed by Andrew Dean.')
    parser.add_argument('--media', '-m',
                        help="Media file path to upload")
    parser.add_argument('--config', '-c',
                        help="Specify configuration file to parse",
                        default="/etc/motion/notify.conf")
    parser.add_argument('--notify', '-n',
                        help="Enable push-bullet notifications",
                        action="store_true")

    args = parser.parse_args()

    if not os.path.exists(args.config):
        log.critical('Config file does not exist [{}]'.format(args.config))
        sys.exit(1)

    if not args.media:
        MotionNotify(args.config, args.notify).send_start_event(args.notify)
        log.info('Start event triggered')
        exit(0)

    if not os.path.exists(args.media):
        log.critical('Video file does not exist [{}]'.format(args.media))
        sys.exit(1)

    MotionNotify(args.config, args.notify).upload_media(args.media,
                                                        args.notify)
