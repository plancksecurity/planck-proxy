read -p "Release tag [latest]: " tag
tag=${tag:-latest}

if [ "x${tag}" != "xlatest" ]; then
	docker tag dockerreg.planck.security/planckproxy:latest dockerreg.planck.security/planckproxy:${tag}
fi

# docker push dockerreg.planck.security/planckproxy
