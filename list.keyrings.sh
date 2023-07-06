# set -x

if [ "x"$1 != "x" ]; then
	keydbs=$(find /home/PlanckGate/work/$1/.pEp/ -type f -name keys.db | grep $1)
else
	keydbs=$(find /home/PlanckGate/work/*/.pEp/ -type f -name keys.db)
fi

for kdb in ${keydbs}; do
	echo "========================================================================="
	echo "== $(echo ${kdb} | cut -d "/" -f 5)"
	echo "========================================================================="
	sqlite3 "${kdb}" -header -column "SELECT * FROM userids; SELECT primary_key, secret FROM keys; SELECT * FROM subkeys;"
done
