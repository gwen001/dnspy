#!/bin/bash

function usage() {
    echo "Usage: "$0" [(SUBD)OMAIN] <[any_subdomain]>"
    exit
}

if [ $# -lt 1 ] || [ $# -gt 2 ] ; then
    usage
fi

if [ $# -eq 2 ] ; then
    nosub=1
else
    nosub=0
fi


domain="$1"
domain_url="https://$1"
domain_dir="domains/$domain"

if [ ! -d $domain_dir ] ; then
    mkdir -p $domain_dir
fi

cd $domain_dir
source ~/.bash_functions


echo "## HAKRAWLER ######" >&2
o_hakrawler="urls_hakrawler"
if [ $nosub -eq 1 ] ; then
    echo $domain_url | hakrawler >> "$o_hakrawler"
else
    echo $domain_url | hakrawler -subs >> "$o_hakrawler"
fi
wc -l "$o_hakrawler" >&2

echo "## GAU ######" >&2
o_gau="urls_gau"
if [ $nosub -eq 1 ] ; then
    echo $domain_url | gau >> "$o_gau"
else
    echo $domain_url | gau --subs >> "$o_gau"
fi
wc -l "$o_gau" >&2

echo "## WAYBACK ######" >&2
o_wayback="urls_wayback"
if [ $nosub -eq 1 ] ; then
    echo $domain | waybackurls -no-subs >> "$o_wayback"
else
    echo $domain | waybackurls >> "$o_wayback"
fi
wc -l "$o_wayback" >&2

echo "## GITHUB ######" >&2
o_github="urls_github"
if [ $nosub -eq 1 ] ; then
    github-endpoints -raw -d $domain >> "$o_github"
else
    github-endpoints -raw -d $domain >> "$o_github"
fi
wc -l "$o_github" >&2


echo "## CLEAN AND MERGE ######" >&2
cat urls_* | grep "$domain" >> urls
wc -l urls >&2
echo


echo "## THE END ######" >&2
# cd ..


