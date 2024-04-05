global
	log			127.0.0.1 local2 debug emerg
	stats		socket /var/lib/haproxy/stats
	tune.ssl.default-dh-param	2048
	daemon

	ssl-default-bind-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384
	ssl-default-bind-ciphersuites TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256
	ssl-default-bind-options no-sslv3 no-tlsv10 no-tlsv11 no-tls-tickets

defaults
	mode					tcp
	log						global
	retries					5
	option                  dontlognull
	option                  redispatch

	timeout client-fin		1s
	timeout server-fin		1s
	timeout http-keep-alive 2s
	timeout queue           5s
	timeout connect         5s
	timeout check           15s
	timeout http-request    45s
	timeout tunnel			2m
	timeout client          5m
	timeout server          5m

listen stats
	bind *:8404
	mode http
	stats enable
	stats uri /
	stats refresh 60s
	stats admin if TRUE
	stats show-node

listen SMTP
	bind *:25
	mode tcp
	balance roundrobin
	option tcplog
	option tcp-check
	{{servers_25}}

listen SMTPS
	bind *:465 accept-proxy ssl crt /ssl/planck.dev.crt
	mode tcp
	balance roundrobin
	option tcplog
	option tcp-check
	{{servers_587}}

listen SMTPS_ENCRYPT
	bind *:466 accept-proxy ssl crt /ssl/planck.dev.crt
	mode tcp
	balance roundrobin
	option tcplog
	option tcp-check
	{{servers_588}}

listen SUBMISSION
	bind *:587
	mode tcp
	balance roundrobin
	option tcplog
	option tcp-check
	{{servers_587}}

listen SUBMISSION_ENCRYPT
	bind *:588
	mode tcp
	balance roundrobin
	option tcplog
	option tcp-check
	{{servers_588}}
