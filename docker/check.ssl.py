#!/usr/local/bin/python -B

from datetime import datetime
import tldextract
import sys
import ssl
import os

def c(text, color=0):
	return f"\033[1;3{color}m{text}\033[0;m"

try:
	checkonly = sys.argv[1] == "checkonly"
except:
	checkonly = False

ssldir = "/volume/ssl"
if not os.path.exists(ssldir):
	print("Creating folder for SSL certificates: " + c(ssldir, 2))
	os.mkdir(ssldir)

hostname      = os.environ["hostname"]
relay_domains = os.environ["relay_domains"]
admin_addr    = os.environ["admin_addr"]

hostnames = set([hostname] + relay_domains.split(" "))
print("\nHostnames handled by this instance: " + c(", ".join(hostnames), 5))

domains = []
for h in hostnames:
	domain = tldextract.extract(h).registered_domain
	domains += [ domain ]
	if h == hostname:
		maindomain = domain

domains = sorted(set([x for x in domains if x]))
print("  - We need certificates for the following top-level domains: " + c(", ".join(domains), 3))
print("  - Primary domain (matching our own hostname): " + c(maindomain, 2) + "\n")

allfine = True
tls_server_sni_maps  = []

for d in domains:
	print("Checking for existing certificate file for domain " + c(d, 5))
	cf = "/volume/ssl/" + d + ".crt"
	dryrun = None

	if not os.path.isfile(cf):
		print("Could not find certificate file " + c(cf, 3))
		dryrun = checkonly
	else:
		print("Found certificate file " + c(cf, 3) + ", checking validity...")
		try:
			cc = ssl._ssl._test_decode_cert(cf)
			expirydate = datetime.strptime(cc["notAfter"], "%b  %d %H:%M:%S %Y %Z")
			diff = expirydate - datetime.now()

			sans = []
			for san in cc["subjectAltName"]:
				sans += [san[1]]
			print("  - Covering these hostnames: " + c(", ".join(sans), 2))

			if d not in sans or "*." + d not in sans:
				print(c("ERROR", 1) + ": Certificate doesn't cover it's own domain " + c(d, 5) + " or the wildcard subdomain")
				dryrun = checkonly
			else:
				print("    - includes our hostname " + c(d, 5) + " and the wildcard subdomain: " + c("OK", 2))

			if diff.days > 14:
				print("  - Expires in " + c(str(diff.days), 3) + " days: " + c("OK", 2))
			else:
				print("  - Expires in " + c(str(diff.days), 5) + " days: " + c("WARNING - consider renewing soon!", 3))
				dryrun = checkonly
				text  = f"The SSL certificate for the domain {d} is going to expire in {diff.days} days: consider renewing soon.\n\n"
				text += f"To do so please run:\n  docker exec -it planckproxy /check.ssl.py\n"
				text += f"from the Docker host where your PlanckProxy instance is running and follow the instructions which involves updating some DNS records."
				os.system(f"echo '{text}' | mail -s '[PlanckProxy] SSL certificate for {d} expiring soon' -a 'From: Planck Proxy <no-reply@{hostname}>' {admin_addr}")

			if diff.days < 1:
				allfine = False

		except Exception as e:
			print(c("Error inspecting certificate file", 1) + ": " + str(e))
			dryrun = checkonly
	
	if dryrun is None:
		print(c("All checks passed for domain ", 2) + c(d, 5))
		tls_server_sni_maps += [       d + " " + cf ]
		tls_server_sni_maps += [ "." + d + " " + cf ]
	elif dryrun is True:
		print(c("Please run ", 1) + c("docker exec -it planckproxy /check.ssl.py", 5) + c(" from your Docker host to generate or renew the SSL certificate file for " + c(d, 5), 1))
		allfine = False
	elif dryrun is False:
		print("Calling certbot for domain " + c(d, 5))
		keeptrying = True
		while keeptrying:
			ret = os.system(f"certbot certonly --manual --agree-tos --no-eff-email --key-type rsa --preferred-challenges=dns -m {admin_addr} -d {d},*.{d}")
			if ret != 0:
				keeptrying = input(c("Certbot failed generating a certificate for ", 1) + c(d, 5) + " - Retry? [Y/n] ") in ("", "y", "Y")
			else:
				print("Successfully generated a certificate for " + c(d, 5) + ", installing it...")
				key = open("/etc/letsencrypt/live/" + d + "/privkey.pem").read()
				crt = open("/etc/letsencrypt/live/" + d + "/fullchain.pem").read()
				open(cf, "w").write(key + crt)
				keeptrying = False

	print()

# This will be loaded by /env2config.py to populate smtp_tls_chain_files in /etc/postfix/main.cf and tls_server_sni_maps in /etc/postfix/sni
# Passing env variables from child to parent process isn't possible hence the somewhat ugly temp files
open("/tmp/tls_server_sni_maps", "w").write("\n".join(tls_server_sni_maps))
open("/tmp/smtp_tls_chain_files", "w").write("/volume/ssl/" + maindomain + ".crt")

if not allfine:
	exit(1)
