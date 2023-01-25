# p≡p Gate
This project provides a tool able to decrypt with p≡p incoming messages which are encrypted with an **extra key**, and pass them along unencrypted to a filtering system. Then the original message is sent encrypted to the next hop or discarded, based on the feedback of the filtering system.

## Extra key deployment
To import the extra key into the p≡p Gate it must be placed into the `keys_dir` defined in the `settings.py` file.
By default this directory is set to the `keys` folder in the root of this same project.

## Postfix configuration
The p≡p Gate uses postfix to handle the message sending and queuing, so some configuration is needed in postfix to correctly bind the email flow to the p≡p Gate:

### Define the pEp Gate in it's two modes in Postfix' master.cf as such:

```
# Incoming decryption-proxy (specific addresses routed via "transport" file)

pepgateIN unix - n n - 1 pipe

flags=DRhu user=pepgate:pepgate argv=<path to pEpGate>/pEpgate decrypt

# Outgoing encryption-proxy (specific port routed above)

pepgateOUT unix - n n - 1 pipe

flags=DRhu user=pepgate:pepgate argv=<path to pEpGate>/pEpgate encrypt
```


### Define a dedicated port where the pEpGate in encryption mode is enforced, still in master.cf:

  ```
588 inet n - y - - smtpd

-o content_filter=pepgateOUT

-o [ + whatever options you have for port 587/SUBMISSION ]
  ````

### Define a transport map in Postfix's main.cf:

```
transport_maps = regexp:/etc/postfix/transport
```


### Example of /etc/postfix/transport:

  ```
# pEpGate

/^support@pep.*/ pepgateIN:

/^noreply@pep.*/ pepgateIN:

/^no-reply@pep.*/ pepgateIN:

  ```

### Define header_checks in main.cf (pEp Gate adds an X-NextMX header to all messages, defined in nexthop.map):

 ```
header_checks = regexp:/etc/postfix/header_checks
```

### Example of /etc/postfix/header_checks:

```
/^X-NextMX: auto$/ FILTER smtp:

/^X-NextMX: (.*)$/ FILTER smtp:$1
```

  ## Monitoring

Cron can be used for basic monitoring. Here's an example to notify once per hour about mails stuck in Postfix's queue

```
0 * * * * mailq | grep -v "is empty"
```
