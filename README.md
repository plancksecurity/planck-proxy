# p≡p Gate

This project provides a tool able to decrypt with p≡p incoming messages which are encrypted with an **extra key**, and pass them along unencrypted to a filtering system. Then the original message is sent encrypted to the next hop or discarded, based on the feedback of the filtering system.

## Requirements

### Python dependencies

You can automatically insall all the python dependencies with the following command:

`pip install -r requirements.txt`

### p≡p python adapter

In order to run the p≡p Gate you need the p≡p Engine, the p≡p Python adapter and their dependencies installed. It can be done following [this guide](https://dev.pep.foundation/Adapter/Adapter%20Build%20Instructions_Version_3.x_DRAFT)

## Usage and settings

The core of the pEp Gate is the pEpgate.py script. It is intended to be invoked by a postfix setup in order to handle the decryption of messages. See the [Postfix configuration](https://git.pep.security/pep/pEpGate/#postfix-configuration).

You can see all the available arguments and their usage running the help command `./pEpgate.py -h`

```
usage: pEpgate [-h] [--DEBUG] [--keys_dir KEYS_DIR] [--work_dir WORK_DIR] [--SMTP_HOST SMTP_HOST] [--SMTP_PORT SMTP_PORT] [--EXTRA_KEYS EXTRA_KEYS] [--settings_file SETTINGS_FILE] {encrypt,decrypt}

pEp Proxy CLI.

positional arguments:
  {encrypt,decrypt}     Mode

optional arguments:
  -h, --help            show this help message and exit
  --DEBUG               Set DEBUG mode, default is False
  --EXTRA_KEYS EXTRA_KEYS
                        FPR for the Extra Key to decrypt messages, default is "4BBCDBF5967AA2BDB26B5877C3329372697276DE"
  --keys_dir KEYS_DIR   Directory where the extra key should be imported from, default is "keys"
  --work_dir WORK_DIR   Directory where the command outputs are placed, default is "work"
  --SMTP_HOST SMTP_HOST
                        Address of the SMTP host used to send the messages. Default "80.90.47.12"
  --SMTP_PORT SMTP_PORT
                        Port of the SMTP host used to send the messages. Default "25"
  --settings_file SETTINGS_FILE
                        Route of the settings file to load, instead of the default settings route, which is <./settings.json>
```

All the arguments can also be passed onto the script as environment variables with the same name as the command. For example `./pEpgate.py SMTP_HOST=192.168.0.1` is equivalent to `SMTP_HOST="192.168.0.1" ./pEpgate.py`

Arguments take priority over environment variables, and environment variables take priority over definitions on the settings.py file.

### Debug

Enables sone debug testing features. If DEBUG is True, then the logs and the emails are kept in the `work_dir` folder after the script finishes running. The default value is False and it's not intended to be True on production usage.

### Extra key and keys dir

To import the extra key into the p≡p Gate, the keypair must be placed into the `keys_dir` defined in the `settings.py` file.
By default this directory is set to the `keys` folder in the root of this same project.
Since all the keys in the `keys_dir`will be imported, you need to specify the FPR for the extra key through the `EXTRA_KEYS` setting.

### Work dir

It's the folder where the pEpgate command will output the results. By default this directory is set to the `work` folder in the root of this same project.
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

### SMTP HOST and PORT

You must use this settings to specify the HOST and PORT of the SMTP server the p≡p Gate will use to send the messages.

## Features

### Decryption

When the p≡p Gate is provided an encrypted message and set to the mode `decrypt`, it will decrypt the message given the following conditions.

- The extra key has been properly imported and configured (see "usage and settings")
- The message has been encrypted with the extra key
- The key for the message's recipient has been imported to the p≡p Gate

If the message meets those requirements or if the original message is unencrypted it will be processed into the `work_dir/<recipient>/<sender>/`folder

Once the message is processed it will be ran through the `scan_pipes`commands. If all the commands finish successfully with a 0 exit code, then the message will be sent out using the provided SMTP configuration.

If any of the `scan_pipes` fail, the message will be re-queued on postfix, a warining email will be sent to the address in `admin_addr`setting and another one will be sent back to the email sender.

### NOENCRYPT

On `DEBUG` mode, messages containing the string 'NOENCRYPT' somewhere in the body and with positive feedback from the filtering system, will be sent unencrypted to the next MTA. The string 'NOENCRYPT' will be removed from the message itself.

## Postfix configuration

The p≡p Gate uses postfix to handle the message sending and queuing, so some configuration is needed in postfix to correctly bind the email flow to the p≡p Gate:

### master.cf

1. Define the pEp Gate in it's two modes in Postfix's master.cf as such:

```
# Incoming decryption-proxy (specific addresses routed via "transport" file)
pepgateIN unix - n n - 1 pipe
flags=DRhu user=pepgate:pepgate argv=<path to pEpGate>/pEpgate decrypt

# Outgoing encryption-proxy (specific port routed above)
pepgateOUT unix - n n - 1 pipe
flags=DRhu user=pepgate:pepgate argv=<path to pEpGate>/pEpgate encrypt
```

2. Define a dedicated port where the pEpGate in encryption mode is enforced, still in master.cf:

```
588 inet n - y - - smtpd
-o content_filter=pepgateOUT
-o [ + whatever options you have for port 587/SUBMISSION ]
```

### main.cf

1. Define a transport map in Postfix's main.cf:

```
transport_maps = regexp:/etc/postfix/transport
```

Example of /etc/postfix/transport:

```
# pEpGate
/^support@pep.*/ pepgateIN:
/^noreply@pep.*/ pepgateIN:
/^no-reply@pep.*/ pepgateIN:
```

2. Define inbound and outbound (smtp\_)header_checks in main.cf (pEp Gate adds an X-NextMX header to all messages, defined in nexthop.map):

```
header_checks      = regexp:/etc/postfix/header_checks_in
smtp_header_checks = regexp:/etc/postfix/header_checks_out
```

/etc/postfix/header_checks_in:

```
/^X-NextMX: auto$/ FILTER smtp:
/^X-NextMX: (.*)$/ FILTER smtp:$1
```

/etc/postfix/header_checks_out:

```
/^X-NextMX:.*$/ IGNORE
```

## Monitoring

Cron can be used for basic monitoring. Here's an example to notify once per hour about mails stuck in Postfix's queue

```
0 * * * * mailq | grep -v "is empty"
```

## Testing

To run the test suite [pytest](https://docs.pytest.org/) must be installed. This can be done either system-wide or using a virtualenv. pip provides an automatic installation using `pip install pytest`

To run the tests simply run the `pytest` command.

## Example integration with O365

### DNS

```
hub.peptest.ch A <IP>
hub.peptest.ch TXT v=spf1 a ~all
hub._domainkey.peptest.ch TXT v=DKIM1 <... DKIM key material>
{gate,proxy}(365).peptest.ch MX hub
{gate,proxy}(365).peptest.ch TXT v=spf1 mx ip4:80.90.47.0/28 include:spf.protection.outlook.com -all
autodiscover.{gate,proxy}365.pep.security	CNAME	autodiscover.outlook.com.
```

### On O365

Accepted domains:
_ `{gate,proxy}365.peptest.ch`, domain type: internal relay
_ `pproxy.onmicrosoft.com`, domain type: authoritative

Mail flow > Connectors:
_ "Mailhub inbound" -> identify by IP
_ "Mailhub outbound"
_ Use of connector: Use only when I have a transport rule set up that redirects messages to this connector.
_ Routing: Route email messages through these smart hosts: `hub.peptest.ch`
_ Rules:
_ Apply to all messages
_ Use the following connector: Mailhub outbound
_ Except if the subject includes "NOENCRYPT" \* or the sender's IP address is in the range <Mailhub's IP>

### On pEpProxy:

#### Postfix

/etc/postfix/main.cf:

```
virtual_mailbox_domains = gate365.peptest.ch
```

/etc/postfix/master.cf:

```
25          inet    n       -       y       -       -       smtpd
[...]
-o content_filter=pEpGateIN

# Incoming decryption-proxy (specific addresses routed via "transport" file)
pepGateIN   unix    -       n       n       -       1       pipe
    flags=DRhu user=pepgate:pepgate argv=/home/pEpGate/pEpgate decrypt

# Outgoing encryption-proxy (specific port routed above)
pepGateOUT  unix    -       n       n       -       1       pipe
    flags=DRhu user=pepgate:pepgate argv=/home/pEpGate/pEpgate encrypt
```

/etc/postfix/transport:

```
/^.*@{gate,proxy}365\.peptest\.ch/ smtp:<tenant slug>.onmicrosoft.com
```

/etc/postfix/virtual:

```
@{gate,proxy}365.peptest.ch @<tenant slug>.onmicrosoft.com
```

#### pEpGate

Configure `settings.py` and `*.map` as needed

## Helper scripts

There are some utility scrips in the `scripts` folder that can be used externally for debugging

### Decrypt

Decrypts a message using p≡p

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

Encrypts a message using p≡p

```
usage: encrypt.py [-h] [--e E] [--m M] [--debug] msg our_key dest_key

Encrypts an email message using p≡p

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
