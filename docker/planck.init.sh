#!/bin/bash

set -xe

# Logging
rsyslogd
echo -e "\n\n=== $(date) Planck Proxy started ===\n" >> /volume/planckproxy.log
ln -s /volume/planckproxy.log /home/proxy/planckproxy.log
mkdir -p /home/proxy/export
mkdir -p /volume/export
ln -s /home/proxy/export /volume

# Generate config files from templates in /volume/
cp -pravin /volume.skel/* /volume/
cp -pravin /volume.skel/home/proxy/* /volume/home/proxy/
cp -pravin /volume.skel/etc/* /volume/etc/
cp -pravin /volume.skel/etc/postfix/* /volume/etc/postfix/
/env2config.py || true
chown proxy:proxy /home/proxy /volume/export /volume/planckproxy.log -R

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
tail -F /var/log/mail.log /home/proxy/planckproxy.log
