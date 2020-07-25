#!/bin/bash

function usage() {
    echo "Usage: "$0" [FILE]"
    if [ -n "$1" ] ; then
		echo "Error: "$1"!"
    fi
    exit
}


if [ ! $# -eq 1 ] ; then
    usage
fi

resolve_file="$1"

if [ ! -f $resolve_file ] ; then
    usage "resolve file not found: $resolve_file"
fi

tmp_file="/tmp/$(date '+%s')"

sed -i -E "s/^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]{1,3}[[:space:]]+[0-9]+[[:space:]]+//g" $resolve_file
sed -i -E "s/\.[[:space:]]+A$//g" $resolve_file
egrep "NXDOMAIN|NOERROR|SERVFAIL|CNAME" $resolve_file > $tmp_file
mv $tmp_file $resolve_file
 