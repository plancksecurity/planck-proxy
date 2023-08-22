FROM alpine:3.18.3

# Install necessary packages and dependencies
# vim is not a dependency but nice to have
RUN apk --no-cache add docker python3 postfix vim

# Copy the proxy files
COPY ./src/* /opt/planck-proxy/

# Set custom main.cf parameters using postconf
RUN postconf -e 'smtpd_banner = $myhostname ESMTP $mail_name (Debian/GNU)' \
    && postconf -e 'biff = no' \
    && postconf -e 'append_dot_mydomain = no' \
    && postconf -e 'readme_directory = no' \
    && postconf -e 'compatibility_level = 2' \
    && postconf -e 'smtp_tls_chain_files = /etc/ssl/certs/_.planck.dev.bundled.crt' \
    && postconf -e 'smtp_tls_CApath = /etc/ssl/certs' \
    && postconf -e 'smtp_tls_session_cache_database = btree:${data_directory}/smtp_scache' \
    && postconf -e 'smtpd_tls_chain_files = /etc/ssl/certs/_.planck.dev.bundled.crt' \
    && postconf -e 'smtpd_tls_security_level = may' \
    && postconf -e 'myorigin = /etc/mailname' \
    && postconf -e 'myhostname = proxymx.planck.dev' \
    && postconf -e 'mydestination = $myhostname, proxymx.planck.dev, localhost' \
    && postconf -e 'mynetworks = 127.0.0.0/8 192.168.130.17 192.168.130.0/24 192.168.249.0/24' \
    && postconf -e 'smtpd_relay_restrictions = permit_mynetworks permit_sasl_authenticated defer_unauth_destination' \
    && postconf -e 'relay_domains = proxy.planck.dev' \
    && postconf -e 'alias_maps = hash:/etc/aliases' \
    && postconf -e 'alias_database = hash:/etc/aliases' \
    && postconf -e 'mailbox_size_limit = 0' \
    && postconf -e 'recipient_delimiter = +' \
    && postconf -e 'inet_interfaces = all' \
    && postconf -e 'inet_protocols = all' \
    && postconf -e 'transport_maps = regexp:/etc/postfix/transport' \
    && postconf -e 'planckproxy_destination_recipient_limit = 1' \
    && postconf -e 'planckproxy_destination_concurrency_limit = 4'

# Set custom Postfix master.cf service entries using postconf

# ==========================================================================
# service type  private unpriv  chroot  wakeup  maxproc command + args
#               (yes)   (yes)   (no)    (never) (100)
# ==========================================================================

RUN echo '25        inet  n       -       y       -       -       smtpd' >> /etc/postfix/master.cf
RUN echo '  -o syslog_name=postfix/smtp-25' >> /etc/postfix/master.cf

RUN echo '587       inet  n       -       y       -       -       smtpd' >> /etc/postfix/master.cf
RUN echo '  -o syslog_name=postfix/smtp-587' >> /etc/postfix/master.cf
RUN echo '  -o smtpd_tls_security_level=encrypt' >> /etc/postfix/master.cf
RUN echo '  -o tls_preempt_cipherlist=yes' >> /etc/postfix/master.cf
RUN echo '  -o smtpd_reject_unlisted_recipient=no' >> /etc/postfix/master.cf
RUN echo '  -o smtpd_recipient_restrictions=' >> /etc/postfix/master.cf
RUN echo '  -o smtpd_client_restrictions=permit_mynetworks,reject' >> /etc/postfix/master.cf
RUN echo '  -o smtpd_relay_restrictions=permit_mynetworks,reject' >> /etc/postfix/master.cf
RUN echo '  -o transport_maps=regexp:/etc/postfix/transport-proxy' >> /etc/postfix/master.cf

RUN echo '588       inet  n       -       y       -       -       smtpd' >> /etc/postfix/master.cf
RUN echo '  -o content_filter=planckproxy' >> /etc/postfix/master.cf
RUN echo '  -o syslog_name=postfix/smtp-588' >> /etc/postfix/master.cf
RUN echo '  -o smtpd_tls_security_level=encrypt' >> /etc/postfix/master.cf
RUN echo '  -o smtpd_reject_unlisted_recipient=no' >> /etc/postfix/master.cf
RUN echo '  -o smtpd_recipient_restrictions=' >> /etc/postfix/master.cf
RUN echo '  -o smtpd_client_restrictions=permit_mynetworks,reject' >> /etc/postfix/master.cf
RUN echo '  -o smtpd_relay_restrictions=permit_mynetworks,reject' >> /etc/postfix/master.cf
RUN echo '  -o transport_maps=regexp:/etc/postfix/transport-proxy' >> /etc/postfix/master.cf

RUN echo '# Planck Proxy reinjection port' >> /etc/postfix/master.cf
RUN echo '10587     inet  n       -       y       -       -       smtpd' >> /etc/postfix/master.cf
RUN echo '  -o syslog_name=postfix/smtp-10587' >> /etc/postfix/master.cf
RUN echo '  -o smtpd_relay_restrictions=permit_mynetworks,permit_sasl_authenticated,reject' >> /etc/postfix/master.cf
RUN echo '  -o smtpd_recipient_restrictions=permit_mynetworks,permit_sasl_authenticated,reject_unauth_destination' >> /etc/postfix/master.cf

RUN echo 'planckproxy unix - n n - 1 pipe' >> /etc/postfix/master.cf
RUN echo '  flags=DRhu user=proxy argv=/opt/planck-proxy/src/proxy/planckProxy.py decrypt /home/proxy/settings.json' >> /etc/postfix/master.cf

# Configure the main transport map
RUN echo '/^root@.*/ local:\n\
 /.@proxy.planck.dev/ smtp:[192.168.130.17]\n\
  /.@.*/ smtp:' >> /etc/postfix/transport

RUN postmap /etc/postfix/transport

# Configure the porxy transport map
RUN touch /etc/postfix/transport-proxy
RUN echo '/.*@.*/ planckproxy:/.*@.*/' >> /etc/postfix/transport-proxy

RUN postmap /etc/postfix/transport-proxy

# Add the "proxy" user without a password
RUN adduser --disabled-password proxy

# Create the workdir and set permissions
RUN mkdir /home/proxy/work
WORKDIR /home/proxy/work
RUN chown proxy:proxy . -R

# Copy the settings file
COPY ./docker/docker-settings.json /home/proxy/settings.json

# Start Postfix service
CMD ["postfix", "start-fg"]
