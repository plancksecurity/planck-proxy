#!/bin/bash

set -xe

# Logging
rsyslogd
echo -e "\n\n=== $(date) Planck Proxy started ===\n" >> /volume/debug.log
ln -s /volume/debug.log /home/proxy/debug.log

# Generate config files from templates in /volume/
cp -pravin /volume.skel/* /volume/
cp -pravin /volume.skel/home/proxy/* /volume/home/proxy/
/env2config.py || true
chown proxy:proxy /home/proxy /volume/debug.log -R

# TODO?: Symlink /var/spool/postfix into /volume (to retain undeliverable mails across container restarts)
# TODO?: OpenDKIM + keys

# Generate lookup tables for Postfix
newaliases
postmap /etc/postfix/transport || true
postmap /etc/postfix/transport-proxy || true

# Launch Postfix
postfix start

env

# Our main loop consists of tail'ing the logs 
tail -F /var/log/mail.log /home/proxy/debug.log
