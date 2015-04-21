Motion Notify Wrapper
=============

To enable, run `make install`

You will also need to tweak the following settings in `/etc/motion/motion.conf`

    on_picture_save mnotify -m %f
    on_movie_end mnotify -m %f -n
    on_event_start mnotify -n



Motion Notify is a notification system for Linux Motion providing upload to
Dropbox and PushBullet notifications when you're not home.

This carries out the following:

- Sends a push event when motion detection event starts
- Uploads images to Dropbox whilst an event is occuring
- Uploads a video to Dropbox when the event ends
- Sends a push event when the event ends - with a link to the video (possibly)
- Detects whether you're at home by looking for certain IP addresses on your LAN
- Specifies guard_hours to send notices regardless of LAN settings (useful for
    sleepers that want the warm fuzzies)

### Only receive alerts when you're not home

The script detects whether you're at home by checking the network for the
presence of certain IP addresses. IP detection uses ping - so be choosey about
devices.

> Note: that mobile phones often don't retain a constant connection to the
wireless network even though they show that they are connected. They tend to
sleep and then just reconnect occassionally to reduce battery drain.

> This means that you might get a lot of false alarms if you just use a mobile
phone IP address. Adding 2 or more devices that are only active when you're at
home will reduce false alarms - try things like your Smart TV, desktop PC etc
as well as any mobile phones.

> It's highly recommended to configure your devices to use static IP's or assign
a DHCP lease policy to prevent the IP addresses from changing.

## Dropbox Setup

Login to Dropbox and create an
[API Application](https://www.dropbox.com/developers/apps).

Copy out the `access_token` into your motion-notify.cfg.

## PushBullet Setup

Log into Pushbullet and copy out your `api_key` from your
[Account Profile](https://www.pushbullet.com/account)


### Generic setup

#### To Install

There's a WIP installer script under scripts/install.sh this is executeable
by running: `make install` from the project root.

#### Post Install Configuration

Edit the config file /etc/motion/motion-notify.cfg and enter the following:

- The name of the folder you created eg. CCTV
- The hours that you always want to recieve email alerts even when you're home
- Enter IP addresses which will be active when you're at home
- plug in API credentials obtained above
- Set Zone/Region info (handy when using a multi-node security system)


### Experiment, and file bugs if you find any!
Motion will now send alerts to you when you're devices aren't present on the
network
