#!/bin/bash

set -xe

# Logging
rsyslogd
echo -e "\n\n=== $(date) Planck Proxy started ===\n" >> /volume/planckproxy.log
ln -s /volume/planckproxy.log /home/proxy/planckproxy.log
mkdir -p /volume/export

# Generate config files from templates in /volume/
cp -pravin /volume.skel/* /volume/
cp -pravin /volume.skel/home/proxy/* /volume/home/proxy/
cp -pravin /volume.skel/etc/* /volume/etc/
cp -pravin /volume.skel/etc/postfix/* /volume/etc/postfix/
/env2config.py || true
chown proxy:proxy /home/proxy /volume/export /volume/planckproxy.log -R

# Generate lookup tables for Postfix
newaliases
postmap /etc/postfix/transport || true
postmap /etc/postfix/transport-proxy || true

# Launch Postfix
postfix start

# Launch Cron (for regular SSL checks and alerts)
crond

# Our main loop consists of tail'ing the logs
tail -F /var/log/mail.log /volume/planckproxy.log
