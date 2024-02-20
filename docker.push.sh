read -p "Release tag [latest]: " tag
tag=${tag:-latest}

if [ "x${tag}" != "xlatest" ]; then
	docker tag dockerreg.planck.security/securityhub-dev:latest dockerreg.planck.security/securityhub-dev:${tag}
fi

docker push dockerreg.planck.security/securityhub-dev:${tag}
