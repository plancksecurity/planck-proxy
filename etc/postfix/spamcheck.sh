#!/bin/sh

logfile="/home/spam/spamcheck.log"
echo "===========================================" >> ${logfile}
date +%Y-%m-%d_%H-%M-%S >> ${logfile}
echo "PID: $$" >> ${logfile}
echo "ARG: $*" >> ${logfile}
# env >> ${logfile}

fromtobot=$(echo $* | egrep "(sq.pep.security|test.pep.security|peptest.ch)" | wc -l)
echo "FromToBot/Whitelisted: ${fromtobot}" >> ${logfile}

SENDMAIL="/usr/sbin/sendmail -i"
SPAMLIMIT="7.1"

trap "rm -f /tmp/out.$$" 0 1 2 3 15

cat | /usr/bin/spamc -u nobody | sed 's/^\.$/../' > /tmp/out.$$

SCORE=$(egrep "^X-Spam-Status.*score=[0-9\-\.]*.*$" < /tmp/out.$$ | cut -d "," -f 2 | cut -d "=" -f 2 | cut -d " " -f 1)
if [ "x${SCORE}" = "x" ]; then
	SCORE=0
	echo "Spam filter hit mail without score. Spamassassin crashed? Just restarting..." | $SENDMAIL -s "[CRITICAL] Mailhub spam filter" mailhub.spam@0x3d.lu
	/etc/init.d/spamassassin restart
fi

echo "SCORE: ${SCORE}" >> ${logfile}

if [ ${fromtobot} -eq 1 ]; then
	echo "Message from/to bot/whitelisted domain, delivering unchecked for spam" >> ${logfile}
	$SENDMAIL "$@" < /tmp/out.$$
else
	if [ $(echo "${SCORE} > ${SPAMLIMIT}" | bc -l) -eq 1 ]; then
		echo "Is SPAM, not delivering!" >> ${logfile}
		cp -pravi /tmp/out.$$ /home/spam/$(date +%Y-%m-%d_%H-%M-%S)_${SCORE}_$$ >> ${logfile}
		echo "$SENDMAIL mailhub.spam.filtered@0x3d.lu < /tmp/out.$$" >> ${logfile}
		$SENDMAIL mailhub.spam.filtered@0x3d.lu < /tmp/out.$$
		# $SENDMAIL "$@" < /tmp/out.$$ # uncomment to deliver spam messages to the original recipient anyways (DEBUG)
	else
		echo "Is NOT spam, delivering..." >> ${logfile}
		# $SENDMAIL pep.spam@0x3d.lu < /tmp/out.$$ # DEBUG
		$SENDMAIL "$@" < /tmp/out.$$
	fi
fi

exit $?
