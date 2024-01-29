## planck Security hub

This project provides a tool able to decrypt with planck incoming messages which are encrypted with an **extra key**, and pass them along unencrypted to a filtering system. Then the original message is sent encrypted to the next hop or discarded, based on the feedback of the filtering system.

## Features

### Decryption

When the planck security hub is provided an encrypted message and set to the mode `decrypt`, it will decrypt the message given the following conditions.

*   The extra key has been properly imported and configured (see "usage and settings")
*   The message has been encrypted with the extra key

If the message meets those requirements or if the original message is unencrypted it will be processed into the `work_dir/<recipient>/<sender>/` folder

Once the message is processed it will be ran through the `scan_pipes`commands. If all the commands finish successfully with a 0 exit code, then the message will be sent out using the provided SMTP configuration. And exported into the `export` folder

If any of the `scan_pipes` fail, the message will be re-queued on postfix, a warining email will be sent to the address in `admin_addr`setting and another one will be sent back to the email sender.

## Building

This software can be either delivered as a standalone Docker image or as a python package.

### Building the Python package

Distribution files can be built with the standard build command, using the settings on `pyproject.toml`:

`python -m build`

Output will be found inside the `dist` folder.

### Building the Docker image

1.  In order to build the Docker image, Docker must be installed in your machine. It can be downloaded [here](https://docs.docker.com/get-docker/).
2.  A local copy of the Proxy can be obtained from the official repository at [plancksecurity/planck-proxy](https://github.com/plancksecurity/planck-proxy)
3.  Environment variables GH_USER and GH_TOKEN need to be set with the secrets provided by a member of the development team so that the Docker image can access repositories on GitHub.

    `export GH_USER=XXXX export GH_TOKEN=XXXX`

4.  The Docker image for the `:latest` version can be built using the following command:

    `docker build --build-arg GH_USER=${GH_USER} --build-arg GH_TOKEN=${GH_TOKEN} --tag=dockerreg.planck.security/planckproxy $* .`

5.  To log into the Planck Docker registry, use the following command:

    `docker login dockerreg.planck.security`

6.  The code can be pushed to the Docker registry using the following command:

    `docker push dockerreg.planck.security/planckproxy`

7.  To build the Docker image for a specific release version (X.Y.Z in this example), the following command must be used:

    `docker build --build-arg GH_USER=${GH_USER} --build-arg GH_TOKEN=${GH_TOKEN} --tag=dockerreg.planck.security/planckproxy:X.Y.Z $* .`

8.  To push the code for the release version to the Docker registry, use the following command:

    `docker push dockerreg.planck.security/planckproxy:X.Y.Z`

9.  The uploaded Docker images can be viewed at [https://dockerreg.planck.security/browser/repo/planckproxy](https://dockerreg.planck.security/browser/repo/planckproxy)

## Installation

This software can be either installed as a standalone Docker image or as a python package. The python package does rely on having Postfix installed in the target system and a proper configuration (see [Postfix configuration](https://github.com/plancksecurity/planck-proxy?tab=readme-ov-file#postfix) below). The Docker image comes bundled with a Postfix instance and it's already pre-configured.

### Python package installation

In order to run the planck security hub as a package you need the planck core, the [planckPythonWrapper](https://github.com/plancksecurity/foundation-planckPythonWrapper) adapter and their dependencies installed. It can be done following [this guide](https://dev.pep.foundation/Adapter/Adapter%20Build%20Instructions_Version_3.x_DRAFT) or by cloning [this project](https://github.com/plancksecurity/foundation-planckCoreStack) and following the provided instructions.

The planck security hub can be installed as a command line command with pip from the tarball or wheel file.

`pip install path/to/planck-proxy-X.Y.Z-py3-none-any.whl` or `pip install path/to/planck-proxy-X.Y.Z.tar.gz`

#### Development mode

There are some extra python dependencies which may be needed for testing and other development features that can be installed with the following command:

`pip install -r requirements_dev.txt`

The package can be installed for development mode with the editable flag. This enables modifying the python code without having to re-build the command.

`pip install -e path/to/this/local/repo`

### Docker installation

If the Planck Security Hub Docker image wasn't built locally, it an be pulled dockerhub repository. Someone on the dev team will need to provide the login credentials.

```
docker login dockerreg.planck.security
docker pull dockerreg.planck.security/planckproxy:latest
```

After the Docker image is on the local machine, the container can be executed. There is a `docker.run.sh.example` script available for configuration. This script can be edited to align with the required network settings.

Please refer to the [Service manual installation page](https://help.planck.security/articles/#!planck-security-hub-service-manual-3-0-1/installation) to see how to integrate the docker into your email server.

## Usage and settings

The core of the planck security hub is the `planckProxy.py` script. It is intended to be invoked by a postfix setup in order to handle the decryption of messages. See the [Postfix configuration](https://github.com/plancksecurity/planck-proxy?tab=readme-ov-file#postfix).

All the available arguments and their usage can be printed running the help command `planckproxy -h`

```

usage: planckproxy [-h] [-f FILE] [-l LOGLEVEL] {decrypt} settings_file

planck Proxy CLI.

positional arguments:
  {decrypt}             Mode
  settings_file         Route for the "settings.json" file

optional arguments:
  -h, --help            Show this help message and exit
  -f FILE, --file FILE  Route for the file to analyze
  -l LOGLEVEL, --loglevel LOGLEVEL
                        Set log legvel, default is INFO
```

### settings_file

This file provides the settings for the planck proxy. This is an example for the settings:

```
{
    "home":             "/home/proxy/",

    "work_dir":         "work",

    "keys_dir":         "keys",

    "export_dir":       "/home/proxy/export",

    "export_log_level": "DEBUG",

    "SMTP_HOST":        "127.0.0.1",

    "SMTP_PORT":        "10587",

    "sq_bin":           "/usr/local/bin/sq",

    "admin_addr":       "someone@yourcompany.tld",

    "dts_domains":      [ "yourcompany.tld" ],

    "scan_pipes": [
        {"name": "SpamAssassin", "cmd": "spamc --check -"},
        {"name": "ClamAV", "cmd": "clamdscan --verbose -z -"}
    ]
}
```

#### home

Path to the home directory for the proxy execution. `work_dir`and `keys_dir` are exepcted to be there or will be created there otherwise.

#### work_dir

It is the name of the folder where the `planckproxy` command will use to store the databaes and working files. By default this directory is set to the `work` subfolder in the current `home` directory.

It will be populated with a structure like this:

```
├── <Recipient address>
│   ├── <Sender address>
│   │   ├── <Date/Time>
│   │   │   ├── planckproxy.html
│   │   │   ├── planckproxy.log
│   │   │   ├── in.decrypt.original.eml
│   │   │   ├── in.decrypt.parsed.eml
│   │   │   └── in.decrypt.processed.eml
│   │   ├── <Another Date/Time>
│   │   │   ├── [...]
│   ├── <Another Sender address>
│   │   ├── <Date/Time>
│   │   │   ├── [...]
│   ├── .pEp
│   │   ├── keys.db
│   │   ├── management.db
│   ├── sec.<recipient address>.key (maybe several)
│   └── pub.<sender address>.key (likely several)
├── <Another Recipient address>
│   ├── <Sender address>
│   │   ├── [...]
```

#### keys_dir

Name of the subfolder to `home` where the the secret key for the security hub must be placed so it can be imported properly.

By default this directory is set to the `keys` folder inside the `home` directory.

#### export_dir

Path to the folder where the `planckproxy` command will output the results. It will be populated with a structure like this:

```
├── <Sender address>
│   ├── <Date/Time>
│   │   ├── planckproxy.log
│   │   └── in.decrypt.processed.eml
│   ├── <Another Date/Time>
│   │   ├── planckproxy.log
│   │   └── in.decrypt.processed.eml
│   [...]
├── <Another Sender address>
│   ├── <Date/Time>
│   │   ├── [...]
│   [...]
```

#### SMTP HOST and PORT

This following settings must be used to specify the HOST and PORT of the SMTP server the planck security hub will use to send the messages.

#### sq_bin

Path to the `sq`command. This is part of the [sequoia](https://sequoia-pgp.org/) library. It is used to inspect the keychain and give extra feedback on the `DEBUG` level logs. If this command is not present the corresponding part of the logs will be skipped.

#### admin_addr

Address for the sysadmin. This address will recieve email notifications if any errors occur.

#### dts_domains

This is a debug feature. If the sender of a message enables "Return receipt" on its email client and the sender address is part of the `dts_domains` list, an email with the proxy log output will be sent back to the sender.

#### scan_pipes

List of the filters the security hub will apply to all messages. Each item in the list must contain a dictionary with the following:

*   name: Verbose name of the filter. Eg. "Spamassassin"
*   cmd: CLI Command needed to invoke the filter. The message will be passed into the command as a piped stdin argument. Eg. "spamc --check -"

### file

The `planckproxy` command will read the `stdin` for a message to decrypt by default, but since in some cases this may not be possible, the optional `-f` or `--file` argument can be used to provide the path to an email file which will be used as the input for the command.

### log level

By default the logs are set to `INFO`, but the parameter `-l` or `--loglevel` can be used to specify the detail of the information shown on the logs:

| Level | Meaning |
| --- | --- |
| DEBUG | Detailed information, typically of interest only when diagnosing problems. |
| INFO | Confirmation that things are working as expected. |
| WARNING | An indication that something unexpected happened, or indicative of some problem in the near future. The software is still working as expected. |
| ERROR | Due to a more serious problem, the software has not been able to perform some function. |

## Sample configuration

### User accounts

A proxy user is needed to run the service and own the `work` directory.

```
sudo adduser proxy
cd /home/proxy/
mdkir work
mkdir keys
chown proxy:proxy . -R
```

### Settings

The security hub must be configured to send messages on a custom port to avoid entering into a loop state, otherwise emails forwarded by the security hub would be put again into the inbound queue due to the transport configuration. So on the `settings.json` file we the SMTP port is defined as `10587`, which has a custom definition on Postfix's `master.cf`

```
{
    "home":             "/home/proxy/",

    "export_dir":       "/home/proxy/export",

    "SMTP_HOST":        "127.0.0.1",

    "SMTP_PORT":        "10587",

    "sq_bin":           "/usr/local/bin/sq",

    "admin_addr":       "someone@yourcompany.tld",

    "dts_domains":      [ "yourcompany.tld" ],

    "scan_pipes": [
        {"name": "SpamAssassin", "cmd": "spamc --check -"},
    ]
}
```

### Postfix

The planck security hub uses Postfix to handle the message sending and queuing, so some configuration is needed in postfix to correctly bind the email flow.

#### main.cf

Following there is an example of a minimal `/etc/postfix/main.cf` file. This will route all default smtp traffic through the transport map transport(line 31). `192.168.130.0/24 192.168.249.0/24` are the netwoks allowed to send messages to the security hub, in this example the VLAN 130 (DMZ) and 249 (Servers). Those are defined on line 19.

```
smtpd_banner = $myhostname ESMTP $mail_name (Debian/GNU)
biff = no

append_dot_mydomain = no
readme_directory = no
compatibility_level = 2

smtpd_tls_cert_file=/etc/ssl/certs/ssl-cert-snakeoil.pem
smtpd_tls_key_file=/etc/ssl/private/ssl-cert-snakeoil.key
smtpd_tls_security_level=may

smtp_tls_CApath=/etc/ssl/certs
smtp_tls_security_level=may
smtp_tls_session_cache_database = btree:${data_directory}/smtp_scache

myorigin = /etc/mailname
myhostname = proxymx.planck.dev
mydestination = $myhostname, proxymx.planck.dev, localhost
mynetworks = 127.0.0.0/8 192.168.130.17 192.168.130.0/24 192.168.249.0/24

smtpd_relay_restrictions = permit_mynetworks,reject

alias_maps = hash:/etc/aliases
alias_database = hash:/etc/aliases

mailbox_size_limit = 0
recipient_delimiter = +
inet_interfaces = all
inet_protocols = all

transport_maps = regexp:/etc/postfix/transport
planckproxy_destination_recipient_limit = 1
planckproxy_destination_concurrency_limit = 4
```

#### transport

Create or add the following to the `/etc/postfix/transport`, which routes all the emails to the target mailbox server (`192.168.130.17`). Emails for our current domain must be specifically mapped, otherwise postfix will ignore reinjected messages.

```
/^root@.*/                                                     local:
/.*@proxy\.planck\.dev/                         smtp:[192.168.130.17]
/.*@.*/                                                         smtp:
```

Then run `postmap transport`

#### transport-proxy

Create or add the following to the `/etc/postfix/transport-proxy`, which routes all the emails to the `planckproxy` section on `master.cf` (line 35 on `master.cf` on this example)

```
/.*@.*/                                 planckproxy:
```

Then run `postmap transport-proxy`

#### master.cf

Add the following to `/etc/postfix/master.cf` This sets smtp transport for ports `587`, `588` and `10587`, allowing only traffic for our networks, which have been configured on `main.cf`. It also sets a custom transport map `transport-proxy` for them. Finally sets the emails coming from the `planckproxy` service to be piped into the `planckproxy decrypt` command.

```
# ==========================================================================
# service type  private unpriv  chroot  wakeup  maxproc command + args
#               (yes)   (yes)   (no)    (never) (100)
# ==========================================================================

25        inet  n       -       y       -       -       smtpd
  -o syslog_name=postfix/smtp-25

587       inet  n       -       y       -       -       smtpd
  -o syslog_name=postfix/smtp-587
  -o smtpd_tls_security_level=encrypt
  -o tls_preempt_cipherlist=yes
  -o smtpd_reject_unlisted_recipient=no
  -o smtpd_recipient_restrictions=
  -o smtpd_client_restrictions=permit_mynetworks,reject
  -o smtpd_relay_restrictions=permit_mynetworks,reject
  -o transport_maps=regexp:/etc/postfix/transport-proxy

588       inet  n       -       y       -       -       smtpd
  -o content_filter=planckproxy
  -o syslog_name=postfix/smtp-588
  -o smtpd_tls_security_level=encrypt
  -o smtpd_reject_unlisted_recipient=no
  -o smtpd_recipient_restrictions=
  -o smtpd_client_restrictions=permit_mynetworks,reject
  -o smtpd_relay_restrictions=permit_mynetworks,reject
  -o transport_maps=regexp:/etc/postfix/transport-proxy

# Planck Proxy reinjection port
10587     inet  n       -       y       -       -       smtpd
  -o syslog_name=postfix/smtp-10587
  -o smtpd_relay_restrictions=permit_mynetworks,permit_sasl_authenticated,reject
  -o smtpd_recipient_restrictions=permit_mynetworks,permit_sasl_authenticated,reject_unauth_destination

# Planck Proxy service configuration
planckproxy unix - n n - 1 pipe
  flags=DRhu user=planck argv=/opt/planck-proxy/src/proxy/planckProxy.py decrypt /home/planck/settings.json
```

## Monitoring

Cron can be used for basic monitoring. Here is an example to notify once per hour about mails stuck in Postfix's queue

```
0 * * * * mailq | grep -v "is empty"
```

#### Sample filter Spamassassin

[Spamassassin](https://spamassassin.apache.org/) is an open-source spam filter used as an example for this setup, but any CLI based system can work with the planck proxy.

Install sapmassassin and start the service

```
apt install spamassassin
/etc/init.d/spamassassin start
```

## Testing

To run the test suite [pytest](https://docs.pytest.org/) must be installed. This can be done either system-wide or using a virtualenv. pip provides an automatic installation using `pip install pytest`

To run the tests simply run the `pytest` command.

## Helper scripts

There are some utility scrips in the `scripts` folder that can be used externally for debugging

### Messages cleanup

Deletes all files in subfolders of a specified directory that were created more than a specified number of days ago. If a subfolder in the directory is empty after deleting .eml and .log files, it is also deleted.

```
usage: messages_cleanup.py [-h] [--work_dir WORK_DIR] [--days DAYS] [--verbose]

optional arguments:
  -h, --help           show this help message and exit
  --work_dir WORK_DIR  the path to the folder containing the subfolders with .eml files
  --days DAYS          the number of days before which to delete the .eml files
  --verbose, -v        Print output data
```
