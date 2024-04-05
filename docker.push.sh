if [ $# -eq 1 ]; then
	tag=$1
else
	dt=$(docker run --rm --entrypoint /bin/sh dockerreg.planck.security/securityhub-dev -c "cat /planck.env | grep BUILD_DATE | cut -d '=' -f 2")
	read -p "Release tag [${dt}]: " tag
	tag=${tag:-${dt}}
fi

if [ "x${tag}" != "xlatest" ]; then
	docker tag dockerreg.planck.security/securityhub-dev:latest dockerreg.planck.security/securityhub-dev:${tag}
fi

docker push dockerreg.planck.security/securityhub-dev:${tag}
