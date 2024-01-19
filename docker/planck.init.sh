#!/bin/bash

# set -x # DEBUG
set -e

# Logging
rsyslogd
echo -e "\n\n=== $(date) Planck Proxy started ===\n"
echo -e "\n\n=== $(date) Planck Proxy started ===\n" >> /volume/planckproxy.log
ln -s /volume/planckproxy.log /home/proxy/planckproxy.log
mkdir -p /volume/export

# Generate config files from templates in /volume/
cp -pravin /volume.skel/* /volume/
cp -pravin /volume.skel/home/proxy/* /volume/home/proxy/
cp -pravin /volume.skel/etc/* /volume/etc/
cp -pravin /volume.skel/etc/postfix/* /volume/etc/postfix/

# Generate/validate certificates
sslcheck=1
while [ $sslcheck -ne 0 ]; do
	set +e
	/check.ssl.py checkonly
	sslcheck=$?
	set -e
	if [ $sslcheck -eq 0 ]; then
		break
	else
		echo "SSL issues detected. Retrying in 5s..."
		sleep 5
	fi
done

# Generate config files, set permissions
/env2config.py || true
chown proxy:proxy /home/proxy /volume/export /volume/planckproxy.log -R

# Generate lookup tables for Postfix
newaliases
postmap -F /etc/postfix/sni || true
postmap /etc/postfix/transport || true
postmap /etc/postfix/transport-proxy || true

# Launch Postfix
postfix start

# Launch Cron (for regular SSL checks and alerts)
crond

# Our main loop consists of tail'ing the logs
tail -F /var/log/mail.log /volume/planckproxy.log
