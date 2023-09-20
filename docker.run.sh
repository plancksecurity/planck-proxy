docker run -d --rm -it -p 25:25 -p 587:587 -p 588:588 \
	-e admin_addr="tech@planck.security" \
	-e hostname="proxymx.planck.dev" \
	-e relay_domains="proxy.planck.dev" \
	-e mynetworks="192.168.130.17 192.168.130.0/24 192.168.249.0/24" \
	--mount type=bind,source="$(pwd)"/docker/volume,target=/volume \
	--name planckproxy \
	planckproxy.azurecr.io/proxy:andy
