#!/bin/bash

# set -x # DEBUG
set -e

# Logging
rsyslogd
echo -e "\n\n=== $(date) Planck Proxy @ $(hostname -f) started ===\n"
echo -e "\n\n=== $(date) Planck Proxy @ $(hostname -f) started ===\n" >> /home/proxy/planckproxy.log
# ln -sfn /volume/planckproxy.log /home/proxy/planckproxy.log # We (may) use "replicas" in docker-compose so if this is the global /volume logfile every container will tail -f this one
mkdir -p /volume/export

# Sync volume keys with container keys
ln -sfn /volume/home/proxy/keys /home/proxy/keys

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
cp /haproxy/haproxy.tpl /volume/haproxy/haproxy.cfg
chown proxy:proxy /home/proxy /volume/export -R

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
tail -F /var/log/mail.log /home/proxy/planckproxy.log
