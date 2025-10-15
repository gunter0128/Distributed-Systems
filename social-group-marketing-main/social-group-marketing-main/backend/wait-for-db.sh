#!/bin/bash

host="$1"
port="$2"
shift 2
cmd="$@"

until mysql -h "$host" -P "$port" -u"$DB_USER" -p"$DB_PASSWORD" -e 'SELECT 1;' > /dev/null 2>&1; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "MySQL is up - executing command"
exec $cmd