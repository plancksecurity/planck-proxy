#!/usr/bin/env -S python3 -B

import smtplib
import email
import sys

smtp_host = "{{smtp_archive}}"
smtp_port = 587
smtp_tls  = True
smtp_user = ""
smtp_pass = ""
debug     = "{{loglevel}}" == "DEBUG"

if len(smtp_host) > 0:
	try:
		msg = email.message_from_string(sys.stdin.read())
		if debug:
			print(f"Input message:\n{msg}")

		conn = smtplib.SMTP(smtp_host, smtp_port)

		if debug:
			conn.set_debuglevel(2)

		if smtp_tls:
			conn.starttls()

		if len(smtp_user) > 0 and len(smtp_pass) > 0:
			conn.login(smtp_user, smtp_pass)

		conn.send_message(msg)

		print("Message delivered to an SMTP mirror server")
		exit(0)
	except:
		print("Message could not be delivered to an SMTP mirror server!")
		exit(1)
else:
	print("Environment variable smtp_archive is empty, sending to an SMTP mirror server skipped")
