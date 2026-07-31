#!/usr/bin/env bash
# databases.sh — extended database discovery (MS SQL / Oracle / MySQL / Sybase).
# Emits normalized JSON for each DB engine found on the host, with instance-of
# links to the server. Credentials via env (vaulted): DB_*_USER/PASS.
# Usage: databases.sh <host> [engine]   engine ∈ mssql|oracle|mysql|sybase|auto
set -u
HOST="${1:-server}"
ENGINE="${2:-auto}"

jstr() { printf '"%s"' "$(printf '%s' "$1" | tr -d '\r' | sed 's/"/\\"/g')"; }

emit() { # engine version instances
  printf '{"key":"db:%s:%s","type":"db","name":%s,"fqdn":%s,"mgmtIp":%s,"source":"sql",' "$2" "$HOST" "$(jstr "$2-$HOST")" "$(jstr "$HOST")" "$(jstr "$HOST")"
  printf '"attrs":{"engine":%s,"version":%s,"instances":[%s]},' "$(jstr "$2")" "$(jstr "$3")" "$4"
  printf '"links":[{"from":"db:%s:%s","to":"host:%s","rel":"instance-of"}]}\n' "$2" "$HOST" "$HOST"
}

# --- MS SQL (1433) ---
if [ "$ENGINE" = "auto" ] || [ "$ENGINE" = "mssql" ]; then
  if command -v sqlcmd >/dev/null 2>&1; then
    VER=$(sqlcmd -S "$HOST" ${MSSQL_USER:+-U "$MSSQL_USER"} ${MSSQL_PASS:+-P "$MSSQL_PASS"} -h-1 -W -Q "SET NOCOUNT ON; SELECT @@VERSION" 2>/dev/null | head -1)
    DBS=$(sqlcmd -S "$HOST" ${MSSQL_USER:+-U "$MSSQL_USER"} ${MSSQL_PASS:+-P "$MSSQL_PASS"} -h-1 -W -Q "SET NOCOUNT ON; SELECT name FROM sys.databases" 2>/dev/null | awk '{printf "%s%s",(NR>1?",":""),"\""$1"\""}')
    [ -n "$VER" ] && emit "$HOST" "mssql" "$VER" "${DBS:-}"
  fi
fi

# --- Oracle (1521) ---
if [ "$ENGINE" = "auto" ] || [ "$ENGINE" = "oracle" ]; then
  if command -v sqlplus >/dev/null 2>&1; then
    VER=$(echo "select banner from v\$version where rownum=1;" | sqlplus -s "${ORACLE_CONN:-system@$HOST:1521/ORCL}" 2>/dev/null | head -1)
    [ -n "$VER" ] && emit "$HOST" "oracle" "$VER" ""
  fi
fi

# --- MySQL (3306) ---
if [ "$ENGINE" = "auto" ] || [ "$ENGINE" = "mysql" ]; then
  if command -v mysql >/dev/null 2>&1; then
    VER=$(mysql -h "$HOST" ${MYSQL_USER:+-u "$MYSQL_USER"} ${MYSQL_PASS:+-p"$MYSQL_PASS"} -Nse "SELECT VERSION();" 2>/dev/null)
    DBS=$(mysql -h "$HOST" ${MYSQL_USER:+-u "$MYSQL_USER"} ${MYSQL_PASS:+-p"$MYSQL_PASS"} -Nse "SHOW DATABASES;" 2>/dev/null | awk '{printf "%s%s",(NR>1?",":""),"\""$1"\""}')
    [ -n "$VER" ] && emit "$HOST" "mysql" "$VER" "${DBS:-}"
  fi
fi

# --- Sybase ASE (4100) ---
if [ "$ENGINE" = "auto" ] || [ "$ENGINE" = "sybase" ]; then
  if command -v isql >/dev/null 2>&1; then
    VER=$(isql -S "$HOST:4100" ${SYBASE_USER:+-U "$SYBASE_USER"} ${SYBASE_PASS:+-P "$SYBASE_PASS"} -b <<'SQL' 2>/dev/null
select @@version
go
SQL
)
    [ -n "$VER" ] && emit "$HOST" "sybase" "$VER" ""
  fi
fi
