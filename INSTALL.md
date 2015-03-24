# Installation procedure

## Minimal running setup: 
(can be modified to suit any other setup, e.g. apache instead of nginx, vhosts etc.)

### FreeBSD

**Python 2.7, pip, sqlite3, nginx**

pkg install python27  
pkg install py27-pip  
pkg install nginx  
pkg install sqlite3  


**Tornado framework & webserver**

pip install tornado

I might have forgotten some lesser packages, but pkg will tell you what else you might need to add. Then add those as well. :)

#### Configuration

OPTIONAL: Edit ./initdb.sql3 and populate/change default usernames/passwords/admin status fields. Or run with defaults.

**Recreate DB: sqlite -init ./initdb.sql3 wt.db**

**Default usernames are in the list, password is 'pass' (without '')**

Edit /usr/local/etc/nginx/nginx.conf and add the following line to default location {}:

```
        location / {
                    proxy_pass http://localhost:8888;
```  

Edit ./whoseturn/html/bootstrap/ws_reload.js and change the address with the ip/fqdn of your machine:

```
var ws = new WebSocket("ws://192.168.56.207:8888/ws");
```

#### Run

pyton ./main.py


### Debian-flavoured Linux

Change package names to the debian versions, rest is more-less same :)

oh, and: s/pkg/apt-get|aptitude/

