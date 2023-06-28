# planck Proxy

This project provides a tool able to decrypt with planck incoming messages which are encrypted with an **extra key**, and pass them along unencrypted to a filtering system. Then the original message is sent encrypted to the next hop or discarded, based on the feedback of the filtering system.

## Features

### Decryption

When the planck Proxy is provided an encrypted message and set to the mode `decrypt`, it will decrypt the message given the following conditions.

- The extra key has been properly imported and configured (see "usage and settings")
- The message has been encrypted with the extra key

If the message meets those requirements or if the original message is unencrypted it will be processed into the `work_dir/<recipient>/<sender>/`folder

Once the message is processed it will be ran through the `scan_pipes`commands. If all the commands finish successfully with a 0 exit code, then the message will be sent out using the provided SMTP configuration.

If any of the `scan_pipes` fail, the message will be re-queued on postfix, a warining email will be sent to the address in `admin_addr`setting and another one will be sent back to the email sender.

## Installation

The planck proxy can be installed as a command line command with pip from the tarball or wheel file.

`pip install path/to/planck-proxy-X.Y.Z-py3-none-any.whl` or `pip install path/to/planck-proxy-X.Y.Z.tar.gz`

### Development mode

The package can be installed for development mode with the editable flag.

`pip install -e .`

### Building

Distribution files can be built with the standard build command, using the settings on `pyproject.toml`:

`python -m build`

Output will be found inside the `dist` folder.

## Requirements

### Python developer dependencies

You can automatically insall all the python dependencies with the following command:

`pip install -r requirements_dev.txt`

### planck python wrapper

In order to run the planck proxy you need the planck core, the planck python wrapper adapter and their dependencies installed. It can be done following [this guide](https://dev.pep.foundation/Adapter/Adapter%20Build%20Instructions_Version_3.x_DRAFT)

## Usage and settings

The core of the planck proxy is the planckProxy.py script. It is intended to be invoked by a postfix setup in order to handle the decryption of messages. See the [Postfix configuration](https://git.planck.security/planck/planck-proxy/#postfix-configuration).

You can see all the available arguments and their usage running the help command `planckproxy -h`

```
usage: planckproxy [-h] [--DEBUG] {decrypt} settings_file

planck Proxy CLI.

positional arguments:
  {decrypt}      Mode
  settings_file  Route for the "settings.json" file.

optional arguments:
  -h, --help     show this help message and exit
  --DEBUG        Set DEBUG mode, default is False
```
### settings_file
This file provides the settings for the planck proxy. This is an example for the settings:

```
{
    "home":             "/home/proxy/",

    "work_dir":         "work",

    "keys_dir":         "keys",

    "logfile":          "debug.log",

    "SMTP_HOST":        "127.0.0.1",
    "SMTP_PORT":        "10587",

    "sq_bin":           "/usr/local/bin/sq",

    "admin_addr":       "someone@yourcompany.tld",

    "dts_domains":      [ "yourcompany.tld" ],

    "DEBUG":            false,

    "scan_pipes": [
        {"name": "SpamAssassin", "cmd": "spamc --check -"},
        {"name": "ClamAV", "cmd": "clamdscan --verbose -z -"}
    ]
}
```
#### home
Home directory for the proxy execution. `work_dir` and `keys_dir` are exepcted to be there or will be created there otherwise.

#### work_dir

It's the folder where the `planckproxy` command will output the results. By default this directory is set to the `work` folder in the current working directory.
Working directory, will be populated with a structure like this:

```
├── <Recipient address>
│   ├── <Sender address>
│   │   ├── <Date/Time>
│   │   │   ├── debug.html
│   │   │   ├── debug.log
│   │   │   ├── in.{decrypt|encrypt}.original.eml
│   │   │   ├── in.{decrypt|encrypt}.parsed.eml
│   │   │   └── in.{decrypt|encrypt}.processed.eml
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

To import the extra key into the planck Proxy, the keypair must be placed into the `keys_dir` defined in the `settings.py` file.
By default this directory is set to the `keys` folder inside the `home`directory.

#### logfile

Name for the logfile


#### SMTP HOST and PORT

You must use this settings to specify the HOST and PORT of the SMTP server the planck Proxy will use to send the messages.

#### sq_bin

Path to the `sq`command. This is part of the [sequoia](https://sequoia-pgp.org/) library which is a requirement to run the planck stack.

#### admin_addr

Address for the sysadmin. This address will recieve email notifications if any errors occur.

#### dts_domains

This is a debug feature. If the sender of a message enabled "Return receipt" on its email client and the sender address is part of the dts_domains list, an email with the proxy log output will be sent back to the sender.

#### Debug

Enables sone debug testing features. If DEBUG is True, then the logs and the emails are kept in the `work_dir` folder after the script finishes running. The default value is False and it's not intended to be True on production usage.

#### scan_pipes

List of the filters the proxy will apply to all messages. Each item in the list must contain a dictionary with the following:
- name: Verbosa name of the filter. Eg. "Spamassassin"
- cmd: CLI Command needed to invoke the filter. The message will be passed into the command as a piped stdin argument. Eg. "spamc --check -"


## Sample configuration


### User accounts
We need a proxy user to run the service and own the work dir.

```
sudo adduser proxy
cd /home/proxy/
mdkir work
mkdir keys
chown proxy:proxy . -R
```

### Settings
The proxy must be configured to send messages on a custom port to avoid entering into a loop state, otherwise emails forwarded by the proxy would be put again into the proxy due to the transport configuration. So on the `settings.json` file we use `10587`, which has a custom definition on Postfix's `master.cf`

We also need to define a `home` setting. The planckproxy command will be executed by postfix, but we want to use the proxy home to create the work folders and import the keys.

```
{
    "home":             "/home/proxy/",

    "SMTP_HOST":        "127.0.0.1",
    "SMTP_PORT":        "10587",

    "sq_bin":           "/usr/local/bin/sq",

    "admin_addr":       "someone@yourcompany.tld",

    "dts_domains":      [ "yourcompany.tld" ],

    "DEBUG":            false,

    "scan_pipes": [
        {"name": "SpamAssassin", "cmd": "spamc --check -"},
    ]
}
```

### Postfix

The planck Proxy uses postfix to handle the message sending and queuing, so some configuration is needed in postfix to correctly bind the email flow to the planck Proxy.

#### main.cf

Following there's an example of a minimal `/etc/postfix/main.cf` file. This will route all default smtp traffic through the transport map transport(line 31). `192.168.130.0/24 192.168.249.0/24` are the netwoks allowed to send messages to the proxy, in this example the VLAN 130 (DMZ) and 249 (Servers). Those are defined on line 19.

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
Create or add the following to the `/etc/postfix/transport`, which routes all the emails to the target mailbox server (`192.168.130.17`). We need to specifically map emails from our domain here, otherwise postfix will ignore reinjected messages.

```
/^root@.*/                                                     local:
/.*@proxy\.planck\.dev/                         smtp:[192.168.130.17]
/.*@.*/                                                         smtp:
````

Then run `postmap transport`

#### transport-proxy
Create or add the following to the `/etc/postfix/transport-proxy`, which routes all the emails to the `planckproxy` section on `master.cf` (line 35 on `master.cf` on this example)

```
/.*@.*/                                 planckproxy:
```

Then run `postmap transport-proxy`


#### master.cf
Add the following to `/etc/postfix/master.cf` This sets smtp transport for ports `587`, `588` and `10587`, allowing only traffic for our networks, which have been configured on `main.cf`. It also sets a custom transport map `transport-proxy` for them. Finally sets the emails coming from the `planckprocy` service to be piped into the `planckproxy decrypt` command.

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

Cron can be used for basic monitoring. Here's an example to notify once per hour about mails stuck in Postfix's queue

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

### Decrypt

Decrypts a message using planck

```
usage: decrypt.py [-h] [--key KEY] [--m M] msg

positional arguments:
  msg                  Path to the email to decrypt

optional arguments:
  -h, --help           show this help message and exit
  --key KEY            key to decrypt
  --m M, --home_dir M  Location of the home folder
```

### Encrypt

Encrypts a message using planck

```
usage: encrypt.py [-h] [--e E] [--m M] [--debug] msg our_key dest_key

Encrypts an email message using planck

positional arguments:
  msg                   Path to the email to encrypt
  our_key               path to the private key of the message sender
  dest_key              path to the pub key of the message recipient

optional arguments:
  -h, --help            show this help message and exit
  --e E, --extra_key E  path to the public extra key
  --m M, --home_dir M   Location of the temporary home folder
  --debug               Keep the home folder and output debug info
```

### Delete keys from keyring

Delete a user key from another user's Database

```
usage: deletekeyfromkeyring.py [-h] [--WORK_DIR WORK_DIR] keyring address

positional arguments:
  keyring              Email of user whose DB to delete from
  address              Email of user whose key to delete

optional arguments:
  -h, --help           show this help message and exit
  --WORK_DIR WORK_DIR  Location of the work folder
```

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
