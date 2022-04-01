#!/bin/sh

logfile="/var/log/pEp.routetest.log"
echo "===========================================" >> ${logfile}
date +%Y-%m-%d_%H-%M-%S >> ${logfile}
echo "PID: $$" >> ${logfile}
echo "ARG: $*" >> ${logfile}
env >> ${logfile}

REFORMAIL="/usr/bin/reformail"
SENDMAIL="/usr/sbin/sendmail -i"

trap "rm -f /tmp/out.$$" 0 1 2 3 15

cat | \
$REFORMAIL -I "X-pEp-foo: 42" | \
$REFORMAIL -I "X-pEp-bar: 23" > \
/tmp/out.$$

$SENDMAIL "$@" < /tmp/out.$$

exit $?
