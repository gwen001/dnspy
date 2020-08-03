#!/usr/bin/python

import os
import sys
import json
import time
import re
import tldextract
import argparse
import requests
import subprocess
from colored import fg, bg, attr
from multiprocessing.dummy import Pool

# disable tldextract stderr spam
from tldextract.tldextract import LOG
import logging
logging.basicConfig(level=logging.WARN)
LOG.debug('')


# disable "InsecureRequestWarning: Unverified HTTPS request is being made."
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


#
# print banner
#
def banner():
	print("""
                _
             __| |  _ __    ___   _ __    _   _       _ __    _   _
            / _` | | '_ \  / __| | '_ \  | | | |     | '_ \  | | | |
           | (_| | | | | | \__ \ | |_) | | |_| |  _  | |_) | | |_| |
            \__,_| |_| |_| |___/ | .__/   \__, | (_) | .__/   \__, |
                                 |_|      |___/      |_|      |___/

                    by @gwendallecoguic

""")
	pass



def load_fingerprints( fingerprints_file ):

    fp = open( fingerprints_file )

    t_fingerprints = json.load( fp )

    for t_service in t_fingerprints['services']:
        t_service['cname_compiled'] = []
        for cname in t_service['cname']:
            r = re.compile( r'('+cname+')' )
            t_service['cname_compiled'].append( r )
        t_services.append( t_service )

    for ignore in t_fingerprints['ignore']:
        t_ignore.append( re.compile( r'('+ignore+')' ) )

    fp.close()



def is_starting_point( line ):

    t_status = [
        'NXDOMAIN',
        'NOERROR',
        'SERVFAIL',
        'REFUSED'
    ]

    for status in t_status:
        if status in line:
            return True

    return False

    # match = re.findall( '^(NXDOMAIN|NOERROR|SERVFAIL)', line )

    # if len(match):
    #     return True
    # else:
    #     return False



def is_ignored( alias ):

    for ignore_regexp in t_ignore:
        match = re.findall( ignore_regexp, alias )
        if len(match):
            return True

    return False



def uniformize( host, str, status='NOERROR' ):

    str = str.strip()

    if not len(str):
        str_return = 'ITSOVER ' + host
    else:
        str_return = status + ' ' + host + "\n" + str.replace( 'is an alias for', 'CNAME' ).replace( 'name server', 'CNAME' )

    return str_return



def confirm_zendesk( host ):

    try:
        t_parse_host = tldextract.extract( host )
    except Exception as e:
        sys.stdout.write( "%s[-] error occurred: %s: %s%s\n" % (fg('red'),e,host,attr(0)) )
        return False

    host_domain = t_parse_host.domain + '.' + t_parse_host.suffix

    domain = t_parse_host.subdomain.replace( '.ssl', '' )
    t_datas = { 'domain': domain }
    url = 'https://www.zendesk.fr/wp-content/themes/zendesk-twentyeleven/lib/domain-check.php'
    print_debug( 'check service availability %s (%s)' % (url,domain) )

    try:
        response = requests.post( url, timeout=5, data=t_datas )
    except Exception as e:
        sys.stdout.write( "%s[-] error occurred: %s%s\n" % (fg('red'),e,attr(0)) )
        return False

    if not response or response.status_code != 200:
        return False

    t_response = response.json()

    if 'suggestion' in t_response:
        return False

    return True


def confirm_domain_availability( domain ):
    # domain = '10degressssssssssss.net'
    return confirm_domain_availability_gandi( domain )
    # return confirm_domain_availability_namecheap( domain )

def confirm_domain_availability_namecheap( domain ):

    url = 'https://rtb.namecheapapi.com/api/picks/' + domain
    print_debug( 'check domain availability %s' % url )

    try:
        response = requests.get( url, timeout=5 )
    except Exception as e:
        sys.stdout.write( "%s[-] error occurred: %s%s\n" % (fg('red'),e,attr(0)) )
        return False

    # print(response.text)
    if not response or response.status_code != 200:
        return False

    t_response = response.json()

    if 'type' in t_response and t_response['type'] == 'success' and 'picks' in t_response:
        for picks in t_response['picks']:
            if picks['domain'] == domain:
                if picks['status']['available']:
                    return True

    return False

def confirm_domain_availability_gandi( domain ):

    if not os.environ.get('GANDI_KEY'):
        return False

    t_headers = { 'authorization':'Apikey '+os.environ.get('GANDI_KEY') }
    url = 'https://api.gandi.net/v5/domain/check?name=' + domain + '&processes=create&processes=transfer'
    print_debug( 'check domain availability %s' % url )

    try:
        response = requests.get( url, headers=t_headers, timeout=5 )
    except Exception as e:
        sys.stdout.write( "%s[-] error occurred: %s%s\n" % (fg('red'),e,attr(0)) )
        return False

    if not response or response.status_code != 200:
        return False

    t_response = response.json()

    if 'products' in t_response:
        for products in t_response['products']:
            if products['status'] == 'available':
                return True

    return False



def resolve_cname( host ):

    resolution = ''
    status = ''
    test_host = host

    while True:

        cmd = 'host ' + test_host
        args = cmd.split( ' ' )
        # print( ">>> "+cmd )

        try:
            proc = subprocess.Popen( args, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
            stdout, stderr = proc.communicate()
            stdout = stdout.decode('utf-8').strip()
        except Exception as e:
            sys.stdout.write( "%s[-] error occurred: %s%s\n" % (fg('red'),e,attr(0)) )
            return '', ''

        if not 'NXDOMAIN' in stdout:
            if not len(status):
                status = 'NOERROR'
            resolution = resolution +  stdout + "\n"
            break

        status = 'NXDOMAIN'
        cmd = 'host -t cname ' + test_host
        args = cmd.split( ' ' )
        # print( ">>> "+cmd )

        try:
            proc = subprocess.Popen( args, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
            stdout, stderr = proc.communicate()
            stdout = stdout.decode('utf-8').strip()
        except Exception as e:
            sys.stdout.write( "%s[-] error occurred: %s%s\n" % (fg('red'),e,attr(0)) )
            return '', ''

        is_alias = re.findall( r'(.*) is an alias for (.*)\.', stdout )
        # print(is_alias)

        if is_alias:
            test_host = is_alias[0][1]
            resolution = resolution +  stdout + "\n"
        else:
            break

        # save some time
        # break

    return resolution, status

# def resolve_ns( host ):

#     resolution = ''

#     for t_service in t_services:
#         if 'ns' in t_service and len(t_service['ns']):

#             for ns in t_service['ns']:
#                 cmd = 'host -t ns ' + host + ' ' + ns
#                 args = cmd.split( ' ' )
#                 # print( ">>> "+cmd )

#                 try:
#                     proc = subprocess.Popen( args, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
#                     stdout, stderr = proc.communicate()
#                     stdout = stdout.decode('utf-8').strip()
#                 except Exception as e:
#                     sys.stdout.write( "%s[-] error occurred: %s%s\n" % (fg('red'),e,attr(0)) )
#                     return

#                 resolution = host + ' name server ' + ns

#                 isto = check_fingerprint( stdout, ['REFUSED'] )
#                 if isto:
#                     return True, resolution

#     return False, ''

def resolve( host ):

    if verbose < 2:
        sys.stderr.write( 'progress: %d/%d\r' %  (t_multiproc['n_current'],t_multiproc['n_total']) )
        t_multiproc['n_current'] = t_multiproc['n_current'] + 1

    resolution, status = resolve_cname( host )
    print_debug( '>>>%s<<<' % resolution )

    resolution = uniformize( host, resolution, status )
    print_debug( '>>>%s<<<' % resolution )
    t_torecheck.append( resolution.split("\n") )


def check_fingerprint( response, t_fingerprints ):

    for fingerprint_regexp in t_fingerprints:
            match = re.findall( fingerprint_regexp, response )
            if len(match):
                return match[0]

    return False


def fingerprint( t_data ):

    host = t_data[0]
    alias = t_data[1]
    t_service = t_data[2]

    if verbose < 2:
        sys.stderr.write( 'progress: %d/%d\r' %  (t_multiproc['n_current'],t_multiproc['n_total']) )
        t_multiproc['n_current'] = t_multiproc['n_current'] + 1

    if not len(t_service['fingerprint']):
        isto = True
    else:
        isto = False

        t_scheme = ['https','http']

        for scheme in t_scheme:
                url = scheme + '://' + host.strip()
                print_debug( 'calling: %s' % url )

                try:
                    r = requests.get( url, timeout=5, verify=False )
                except Exception as e:
                    # if verbose > 2:
                    sys.stdout.write( "%s[-] error occurred: %s%s\n" % (fg('red'),e,attr(0)) )
                    continue

                isto = check_fingerprint( r.text, t_service['fingerprint'] )
                if isto:
                    break

    if isto:
        print_debug( 'fingerprint has been FOUND "%s"' % isto )
        confirm = False
        if t_service['name'] == 'zendesk':
            confirm = confirm_zendesk( alias )
        print_result( host, alias, 2, t_service, confirm )
    else:
        print_debug( 'fingerprint NOT found' )
        print_result( host, alias, 0, t_service )



def check_service( alias ):

    for t_service in t_services:
        for cname_regexp in t_service['cname_compiled']:
            match = re.findall( cname_regexp, alias )
            if len(match):
                return t_service

    return False


def checkTakeover( t_data ):

    m = re.findall( '([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:53\s+)?([0-9]{8,12}\s+)?([A-Z]{5,10})\s+([^ ]+)', t_data[0] )

    if not m:
        return False

    status = m[0][2]
    host = m[0][3].strip().strip('.')
    t_cnames = t_data[1:]

    try:
        t_parse_host = tldextract.extract( host )
    except Exception as e:
        sys.stdout.write( "%s[-] error occurred: %s: %s%s\n" % (fg('red'),e,host,attr(0)) )
        return False

    host_domain = t_parse_host.domain + '.' + t_parse_host.suffix

    print_debug( '---------------------------------------' )
    print_debug( 'HOST: %s\tSTATUS: %s' % (host,status) )

    # if status == 'SERVFAIL' or (status == 'NXDOMAIN' and len(t_data)<2):
    if status == 'SERVFAIL': # save alot of time!
        t_resolve.append( host )
        print_debug( 'resolve later' )
        return

    if status == 'ITSOVER' or len(t_data) < 2:
        print_debug( 'no data, forget it' )
        return


    for line in t_cnames:

        if not 'CNAME' in line:
            continue

        tmp = line.split( ' ' )
        alias = tmp[-1].strip('.')

        try:
            t_parse_alias = tldextract.extract( alias )
        except Exception as e:
            sys.stdout.write( "%s[-] error occurred: %s: %s%s\n" % (fg('red'),e,alias,attr(0)) )
            continue

        alias_domain = t_parse_alias.domain + '.' + t_parse_alias.suffix
        print_debug( 'ALIAS: %s' % alias )

        if alias_domain == host_domain:
            print_debug( '%s is ignored' % alias )
            print_result( host, alias, 3, {'name':''} )
            continue

        t_service = check_service( alias )

        if t_service:
            # a service is configured and found
            print_debug( 'SERVICE found: %s' % t_service['name'].upper() )
            if status == 'NXDOMAIN':
                if t_service['nxdomain']:
                    print_debug( 'host IS dead and service DOES that' )
                    print_result( host, alias, 2, t_service )
                else:
                    print_debug( 'host IS dead but service DONT DO that' )
                    print_result( host, alias, 1, t_service )
            else:
                if t_service['nxdomain']:
                    print_debug( 'host IS NOT dead but service DOES that' )
                    print_result( host, alias, 1, t_service )
                else:
                    print_debug( 'host IS NOT dead and service DONT DO that' )
                    print_debug( 'fingerprints!' )
                    t_pool.append( [host,alias,t_service] )
        else:
            # no service found
            print_debug( 'no service found' )
            ignore = is_ignored( alias )

            if ignore:
                # the domain of the alias is in the ignore list
                print_debug( '%s is ignored' % alias )
                print_result( host, alias, 3, {'name':''} )
            else:
                # the domain of the alias is NOT in the ignore list
                print_debug( '%s is NOT ignored' % alias )
                if status == 'NXDOMAIN':
                    confirm = confirm_domain_availability( alias_domain )
                    print_result( host, alias, 2, {'name':'domain'}, confirm )
                else:
                    print_result( host, alias, 2, {'name':'?'} )



def print_result( host, alias, status, t_service=[], flag=False ):

    color_alias = 'light_red'
    service = t_service['name'].upper()

    if verbose < 1 and service == '?':
        return

    if status == 2:
        # vulnerable
        if 'warning' in t_service and t_service['warning']:
            color_service = 'light_red'
        else:
            color_service = 'light_green'
    elif status == 1:
        # doubt
        if 'warning' in t_service and t_service['warning']:
            color_service = 'light_red'
        else:
            if verbose < 1:
                return
            color_service = 'light_yellow'
    elif status == 3:
        # is ignored
        color_alias = 'dark_gray'
        if 'warning' in t_service and t_service['warning']:
            color_service = 'light_red'
        else:
            if verbose < 2:
                return
            service = 'Is Ignored'
            color_service = 'white'
    else:
        # not vulnerable
        color_alias = 'dark_gray'
        if 'warning' in t_service and t_service['warning']:
            color_service = 'light_red'
        else:
            if verbose < 2:
                return
            service = 'Not Vulnerable'
            color_service = 'white'

    if flag:
        color_service = 'magenta_1'

    sys.stdout.write( '[%s%s%s] %s -> %s%s%s\n' % (fg(color_service),service,attr(0),host,fg(color_alias),alias,attr(0)) )


def print_debug( msg ):
    if verbose > 2:
        sys.stdout.write( '%s[*] %s%s\n' % (fg('dark_gray'),msg,attr(0)) )



parser = argparse.ArgumentParser()
parser.add_argument( "-s","--source",help="source file (masscan output using format: -o Sqnr)" )
parser.add_argument( "-f","--fingerprints",help="fingerprints file" )
parser.add_argument( "-r","--reresolve",help="force reresolve", action="store_true" )
parser.add_argument( "-v","--verbose",help="verbose mode, 0:only vulnerable (default), 1:include unknown services and doubt, 2:include ignored and not vulnerable, 3:debug" )
parser.parse_args()
args = parser.parse_args()

verbose = 0
t_services = []
t_ignore = []

if args.source:
    source_file = args.source
    if not os.path.isfile(source_file):
        parser.error( 'source file not found' )
else:
    parser.error( 'source file not found' )

if args.verbose:
    verbose = int(args.verbose)

if args.fingerprints:
    fingerprints_file = args.fingerprints
    if os.path.isfile(fingerprints_file):
        load_fingerprints( fingerprints_file )
    else:
        parser.error( 'fingerprints file not found' )



cmd = "wc -l " + source_file + " | awk '{print $1}'"
# print( cmd )

try:
    output = subprocess.check_output( cmd, shell=True ).decode('utf-8')
except Exception as e:
    sys.stdout.write( "%s[-] error occurred: %s%s\n" % (fg('red'),e,attr(0)) )
    sys.exit()

n_lines = int( output.strip() )


i = 0
t_data = []
t_pool = []
t_resolve = []
t_torecheck = []

sys.stdout.write( '[+] Parsing file: %s, %d lines\n' % (source_file,n_lines) )
fp = open( source_file, 'r' )

t_multiproc = {
    'n_current': 0,
    'n_total': n_lines,
}

# sys.stdout.write( '\n' )
# sys.stderr.write( 'progress: %d\r' %  i )

sys.stdout.write( '[+] Run the CNAME check\n' )

for line in fp:

    sys.stderr.write( 'progress: %d/%d\r' %  (i,n_lines) )

    if is_starting_point(line) and len(t_data):
        checkTakeover( t_data )
        t_data = []

    i = i + 1
    t_data.append( line.strip() )

checkTakeover( t_data )

fp.close()


if len(t_resolve) < 30000 or args.reresolve:
    sys.stdout.write( '[+] %d hosts to re-resolve\n' % len(t_resolve) )

    t_multiproc = {
        'n_current': 0,
        'n_total': len(t_resolve),
    }

    pool = Pool( 30 )
    pool.map( resolve, t_resolve )
    pool.close()
    pool.join()

    for t_data in t_torecheck:
        checkTakeover( t_data )
else:
    sys.stdout.write( '[-] %d is too many SERVFAIL, you should re-run the resolver\n' % len(t_resolve) )


if not len(t_pool):
    sys.stdout.write( '[-] Nothing to fingerprint\n' )
else:
    sys.stdout.write( '[+] %d hosts to fingerprint\n' % len(t_pool) )

    t_multiproc = {
        'n_current': 0,
        'n_total': len(t_pool),
    }

    pool = Pool( 30 )
    pool.map( fingerprint, t_pool )
    pool.close()
    pool.join()
