# Make sure you set GH_USER and GH_TOKEN to a valid user/access token for the planck enterprise github repos

docker build --build-arg GH_USER=${GH_USER} --build-arg GH_TOKEN=${GH_TOKEN} --tag=dockerreg.planck.security/securityhub-dev  $* .
