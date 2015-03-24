#!/usr/local/bin/python

import hashlib
import uuid

users=[ 'Rosa', 'Masa', 'Kristian', 'Vedran', 'Ivan', 'Pero' ]
def_pass='pass'

for u in users:
    s=uuid.uuid4().hex
    p=hashlib.sha512(s+def_pass).hexdigest()
    print 'update users set salt="'+s+'" where name="'+u+'";'
    print 'update users set passwd="'+p+'" where name="'+u+'";'
