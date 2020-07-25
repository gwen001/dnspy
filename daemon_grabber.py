#!/usr/bin/python

import os
import sys
import time
import subprocess
from colored import fg, bg, attr


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


#
# usage
#
def usage( error="" ):
    sys.stdout.write( "Usage: %s\n" % sys.argv[0] )
    if len(error):
		sys.stdout.write( "Error: %s\n" % error )
    sys.exit(-1)


#
# remove the n first lines of the input file
#
def truncateFile( file, n_lines ):

    sys.stdout.write( "[+] removing %d lines from %s\n" % (n_lines,file) )
    cmd = "sed -i -e '1," + str(n_lines) + "d' " + file
    print( cmd )

    try:
        output = subprocess.check_output( cmd, shell=True ).decode('utf-8')
    except Exception as e:
        sys.stdout.write( "%s[-] error occurred: %s%s\n" % (fg('red'),e,attr(0)) )
        return


#
# test if the domain is a wildcard
#
def isWildcard(domain):
    return False


#
# run the subdomain grabber
#
def runGrabber( domain ):

    cmd = dnspy_dir + '/grabber_hosts.sh ' + domain
    print( cmd )

    try:
        output = subprocess.check_output( cmd, shell=True ).decode('utf-8')
    except Exception as e:
        sys.stdout.write( "%s[-] %s error occurred: %s%s\n" % (fg('red'),domain,e,attr(0)) )
        return False

    return True


#
# add domain to the resolver queue
#
def addToResolverQueue( domain ):

    cmd = 'echo ' + domain + ' >> ' + dnspy_dir + '/queue_resolver'
    print( cmd )

    try:
        output = subprocess.check_output( cmd, shell=True ).decode('utf-8')
    except Exception as e:
        sys.stdout.write( "%s[-] %s error occurred: %s%s\n" % (fg('red'),domain,e,attr(0)) )
        return False

    return True


#
# run the whole shit for a single domain
#
def runDomain( domain ):
    
    print( "handling "+domain )
    
    if isWildcard(domain):
        return

    if not runGrabber( domain ):
        return

    addToResolverQueue( domain )

    return


#
# MAIN
#
loop_sleep = 5
read_lines = 1
dnspy_dir = os.path.dirname( os.path.abspath(__file__) )
domains_dir = dnspy_dir + '/domains'
queue_file = dnspy_dir + '/queue_grabber'

if not os.path.isfile(queue_file):
    fp = open( queue_file, 'w' )
    fp.close()


n_loop = 1

while( n_loop ):

    time.sleep( loop_sleep )

    sys.stdout.write( "[*] running loop %d\n" % n_loop )
    n_loop += 1

    cmd = 'head -n ' + str(read_lines) + ' ' + queue_file
    print( cmd )

    try:
        output = subprocess.check_output( cmd, shell=True ).decode('utf-8')
    except Exception as e:
        sys.stdout.write( "%s[-] error occurred: %s%s\n" % (fg('red'),e,attr(0)) )
        continue

    output = output.strip()
    
    if not len(output):
        sys.stdout.write( "[-] %s input file is empty\n" % queue_file )
        # time.sleep( 3 )
        continue

    t_output = output.split("\n")
    sys.stdout.write( "[+] %d domains to test\n" % len(t_output) )

    for domain in t_output:
        runDomain( domain )

    truncateFile( queue_file, read_lines )
