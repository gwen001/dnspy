#!/bin/bash

function usage() {
    echo "Usage: "$0" [DOMAIN]"
    if [ -n "$1" ] ; then
		echo "Error: "$1"!"
    fi
    exit
}

function clean() {
    f="$1"
    domain="$2"
    sed -i "s/^\*\.//g" "$f"
    sed -i "s/^\.//g" "$f"
    sed -i "s/^2F//ig" "$f"
    sed -i "s/^25//ig" "$f"
    sed -i "s/^3D//ig" "$f"
    sed -i "s/<br>/\n/ig" "$f"
    sed -i "s/,/\n/g" "$f"
    cat $f | perl -pe 's/\\n/\n/g' | tr '[:upper:]' '[:lower:]' | egrep "$domain$" | sort -fu > "/tmp/$f"
    mv "/tmp/$f" "$f"
}



if [ ! $# -eq 1 ] ; then
    usage
fi

domain="$1"
domain_dir="domains/$domain"

if [ ! -d $domain_dir ] ; then
    mkdir -p $domain_dir
fi

cd $domain_dir
source ~/.bash_functions

echo "## GOOGLE+GITHUB ######" >&2
o_gg_github="hosts_gg_github"
gggithub "$domain" | tee -a $o_gg_github
wc -l $o_gg_github >&2
echo

echo "## FINDOMAIN ######" >&2
findomain -t "$domain" -o
o_tmp="$domain.txt"
o_findomain="hosts_findomain"
if [ -f $o_tmp ] ; then
    cat $o_tmp >> $o_findomain
    rm $o_tmp
fi
wc -l $o_findomain >&2
echo

echo "## CERTSPOTTER ######" >&2
o_certspotter="hosts_certspotter"
certspotter "$domain" | tee -a $o_certspotter
wc -l $o_certspotter >&2
echo

echo "##### CRTSH ######" >&2
o_crtsh="hosts_crtsh"
crtsh "$domain" | tee -a $o_crtsh
wc -l $o_crtsh >&2
echo

echo "##### BUFFEROVER ######" >&2
o_bufferover="hosts_bufferover"
bufferover "$domain" | tee -a $o_bufferover
wc -l $o_bufferover >&2
echo

echo "##### THREATCROWD ######" >&2
o_threatcrowd="hosts_threatcrowd"
threatcrowd "$domain" | tee -a $o_threatcrowd
wc -l $o_threatcrowd >&2
echo

# echo "## C9 ######" >&2
# o_c99="hosts_c99"
# c99 "$domain" | tee -a $o_c99
# wc -l $o_c99 >&2
# echo

echo "## SECURITYTRAILS ######" >&2
o_securitytrails="hosts_securitytrails"
securitytrails "$domain" | tee -a $o_securitytrails
wc -l $o_securitytrails >&2
echo

# echo "## SUBLIST3R ######" >&2
# o_sublist3r="hosts_sublist3r"
# sublist3r -d "$domain" -o $o_sublist3r
# wc -l $o_sublist3r >&2
# echo

echo "## SUBFINDER ######" >&2
o_subfinder="hosts_subfinder"
subfinder -d "$domain" 2>/dev/null | tee -a $o_subfinder
wc -l $o_subfinder >&2
echo

echo "## ASSETFINDER ######" >&2
o_assetfinder="hosts_assetfinder"
assetfinder --subs-only "$domain" | tee -a $o_assetfinder
wc -l $o_assetfinder >&2
echo

echo "## GOOGLE+PASTEBIN ######" >&2
o_gg_pastebin="hosts_gg_pastebin"
ggpastebin "$domain" | tee -a $o_gg_pastebin
wc -l $o_gg_pastebin >&2
echo

echo "## GITHUB ######" >&2
o_github="hosts_github"
github-subdomains.py -d "$domain" | tee -a $o_github
wc -l $o_github >&2
echo

echo "## OSUB ######" >&2
o_osub="hosts_osub"
osub "$domain" | tee -a $o_osub
wc -l $o_osub >&2
echo

# echo "## GAU ######" >&2
# o_gau="hosts_gau"
# echo "https://$domain" | gau | awk -F '/' '{print $3}' | awk -F ':' '{print $1}' | tee -a $o_gau
# wc -l $o_gau >&2
# echo

echo "## WORDGRAB ######" >&2
o_wordgrab="raw_wordgrab"
wordgrab2 "$domain" | tee -a $o_wordgrab
wc -l $o_wordgrab >&2
echo

wordlist_amass="$(pwd)/../../subdomains-top1million-5000.txt"
# wordlist_amass="$(pwd)/../../subdomains-top1million-20000.txt"
domain_amass="wordgrab_amass"
cp $o_wordgrab $domain_amass
cat $wordlist_amass >> $domain_amass

wordlist_altdns="$(pwd)/../../altprefix_short.txt"
# wordlist_altdns="$(pwd)/../../altprefix.txt"
domain_altdns="wordgrab_altdns"
cp $o_wordgrab $domain_altdns
cat $wordlist_altdns >> $domain_altdns

echo "## AMASS 1 ######" >&2
o_amass="hosts_amass"
amass enum -active -d "$domain" -brute -w $domain_amass -src -ip -dir amass -o amass/amass.txt
cat amass/amass.txt | awk -F ']' '{print $2}'  | awk '{print $1}' | sort -fu | tee -a $o_amass
wc -l $o_amass >&2
echo

echo "## SSLSUB ######" >&2
o_sslsub="hosts_sslsub"
cat hosts_amass | parallel -j 10 "source ~/.bash_functions; sslsub {1} | egrep \"\.{1}$\" | tee -a hosts_sslsub"
wc -l $o_sslsub >&2
echo

echo "## ONEFORALL ######" >&2
o_oneforall="hosts_oneforall"
python3.6 /opt/bin/oneforall.py --target "$domain" --path ./oneforall/ --brute True --req True run
if [ -d oneforall ] ; then
  mv ./oneforall/*.txt $o_oneforall
fi
wc -l $o_oneforall >&2
echo


echo "## CLEAN HOSTS AND MERGE ######" >&2
ls -1 hosts_* | while read f
do
    clean $f $domain
done
cat hosts_* | sort -fu >> hosts
wc -l hosts >&2
echo

echo "## HUGE BRUTE FORCE ######" >&2
o_hugebf="alt_hugebf"
cat "$(pwd)/../../EnormousDNS.txt" | awk -v dom="$domain" '{print $1"."dom}' > $o_hugebf
wc -l $o_hugebf >&2
echo

echo "## ALTDNS ######" >&2
if [ -f hosts ] ; then
    altdns -i "$(pwd)/hosts" -w $domain_altdns -o "$(pwd)/alt_altdns"
    wc -l alt_altdns >&2
fi
echo

echo "## DNSGEN ######" >&2
if [ -f hosts ] ; then
    dnsgen -f "$(pwd)/hosts" -w $domain_altdns > "$(pwd)/alt_dnsgen"
    wc -l alt_dnsgen >&2
fi
echo

echo "## CLEAN ALTS AND MERGE ######" >&2
cat hosts >> alt_hosts
cat alt_* | sort -fu >> altdns
wc -l altdns >&2

echo "## THE END ######" >&2
# cd ..
