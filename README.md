# dnspy

Find subdomain takeovers.


# Warning

This repository is not public yet.
If you get access it means that you're part of the GitHub sponsors program.
For now, you're not allowed to release it, publish it or give access to anyone else.

Please remember that this program is still under development, bugs and changes may occur.


# Install

```
git clone https://github.com/gwen001/dnspy
cd dnspy
pip3 install -r requirements.txt
```

# How does it work

This tool is basically composed of 3 parts:

- grabber
- resolver
- interperter

Each part has a daemon and a queue file. To run a daemon do the following:

```
cd dnspy
./daemon_xxx.py
```

The daemon will run by itself and forever.
Then, as soon as a domain name is entered in the corresponding queue file, the daemon will process it.

The ```daemon_grabber.py``` basically run ```grabber_host.sh``` and feed the resolver queue file.
It's my current bash script to grab subdomains using many external tools.
Feel free to customize it or write your own.  

The ```daemon_resolver.py``` basically run ```massdns``` (so you better have it installed in your system) and feed the interpreter queue file.  

The ```daemon_interpreter.py``` will read the massdns output file and check for subdomains takeover by running ```interpreter.py```.
This script is **strongly** inspired of ```subjack``` but I added some features like the ignore list and also improved the fingerprints.
Feel free to add your own signatures.  

```
usage: interpreter.py [-h] [-s SOURCE] [-f FINGERPRINTS] [-r] [-v VERBOSE]

optional arguments:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        source file (masscan output)
  -f FINGERPRINTS, --fingerprints FINGERPRINTS
                        fingerprints file
  -r, --reresolve       force reresolve
  -v VERBOSE, --verbose VERBOSE
                        verbose mode, 0:only vulnerable (default), 1:include
                        unknown services and doubt, 2:include ignored and not
                        vulnerable, 3:debug
```

# Output legend

(screenshots after holidays)  

[?] - unknown service
[YELLOW] - there is something weird (doubt) but mostly not takeoverable
[GREEN] - possible takeover
[PINK] - takeover confirmed with an additional check
[RED] - warning, this service deserve a manual check (like S3 bucket permissions)

Whatever the color, manual check is always a good idea and should always be performed before sending a report.  


# Recommandations

Use this script on a dedicated server with a good connection.
Use screen or tmux so even if you're disconnected the daemons will still run in the background.

Manually launch the interpreter using ```qinterpreter2.sh``` so the ouput will be nicely displayed and you will be able to customize the fingerprints the way you like.


# Takover cases

1/ subdomain points to a 3rd party service app but the app is not created on the service  
resolution response: most of the time CNAME but sometimes NXDOMAIN  
ex: xxxxxx.azurewebsites.com, xxxx.s3.amazonaws.com, xxxx.herokuapp.com...  

2.1/ subdomain uses 3rd party service/DNS but the domain isn't claimed on the service  
resolution response: ?  
ex: cloudfront...

2.2/ subdomain uses 3rd party DNS but the domain isn't claimed on the service
resolution response: ?  
ex: fastly...  

3/ subdomain points to a 3rd party service but is a A or AAAA record
resolution response: ipv4 or ipv6
ex: ?  

4/ subdomain is an alias to a domain which doesn't belong to anyone, buy it!
resolution response: NXDOMAIN  


# TODO

- http requests to solve case 3/
- screenshots
- find a more appropriate name
- ?


---

Feel free to ping me on Twitter if you have any problem to use the script.  
https://twitter.com/gwendallecoguic
