# set -x

if [ "x"$1 != "x" ]; then
	keydbs=$(find work/$1/.pEp/ -type f -name keys.db | grep $1)
else
	keydbs=$(find work/*/.pEp/ -type f -name keys.db)
fi

for kdb in ${keydbs}; do
	echo "========================================================================="
	echo "== ${kdb} - Public keys"
	echo "========================================================================="
	sqlite3 "${kdb}" -header -column "SELECT userid, keys.primary_key, subkey \
		FROM userids JOIN keys USING(primary_key) JOIN subkeys USING(primary_key) \
		WHERE secret = 0 ORDER BY userid COLLATE NOCASE;"

	echo "========================================================================="
	echo "== ${kdb} - Secret keys"
	echo "========================================================================="
	sqlite3 "${kdb}" -header -column "SELECT userid, keys.primary_key, subkey \
		FROM userids JOIN keys USING(primary_key) JOIN subkeys USING(primary_key) \
		WHERE secret = 1 ORDER BY userid COLLATE NOCASE;"
done
