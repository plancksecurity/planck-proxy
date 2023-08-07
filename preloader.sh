# Store stdin to temp file and redirect stderr (the Planck engine's logs) to a file so it doesn't pollute what's returned to Postfix

msg=/tmp/$$.eml
log=/home/PlanckGate/debug.engine.log

echo "PlanckGate preloader PID $$ BEGIN" >> ${log}
tee ${msg} > /dev/null # stdin to file
/home/PlanckGate/loader $1 < ${msg} >> ${log} 2>&1
ret=$?
rm -f ${msg}
echo "RET: ${ret}" >> ${log}
echo "PlanckGate preloader PID $$ DONE" >> ${log}

exit ${ret}
