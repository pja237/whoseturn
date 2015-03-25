#!/usr/local/bin/python

import tornado.ioloop
import tornado.web
import tornado.websocket
import sqlite3
import re
import uuid
import hashlib

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, database=None, cursor=None):
        self.db=database
        self.c=cursor
        self.admin=0

    def get_current_user(self):
        return self.get_secure_cookie("user")

    def wt_get_main_table(self):
        c.execute('select name, points, calling from users;')
        res=sorted(c.fetchall(), key=lambda i: i[1] , reverse=True)
        data=dict(map(lambda i: (i[0],[ i[1],i[2] ]), res))
        return data

    def wt_get_hist_table(self):
        self.c.execute('select placedorder.*, group_concat(orders.forwho) from placedorder inner join orders where placedorder.id=orders.orderid group by placedorder.id order by placedorder.id desc limit 5')
        data=self.c.fetchall()
        return data

    def wt_get_order_table(self):
        c.execute('select * from dailyorders;')
        data=c.fetchall()
        ret={x:map(lambda i: i[1], filter(lambda i: i[0]==x, data)) for x in set(map(lambda i: i[0], data))}
        return ret

    def wt_get_selected_place(self):
        c.execute('select name,phone,web from restaurants where selected=1;')
        data=c.fetchone()
        return data

class MainListHandler(BaseHandler):
    def get(self):
        self.c.execute('select name, points, calling from users;')
        res=sorted(self.c.fetchall(), key=lambda i: i[1] , reverse=True)
        max_points=max(map(lambda i: i[1], res))
        self.write({'oid':'RELOAD','data':dict(map(lambda i: (i[0],[ i[1],i[2] ]), res))})

class MainHandler(BaseHandler):
    def get(self):
        # main table
        self.c.execute('select name, points from users;')
        res=sorted(self.c.fetchall(), key=lambda i: i[1] , reverse=True)
        max_points=max(map(lambda i: i[1], res))
        # calling users
        self.c.execute('select name from users where calling=1;')
        calling_user=self.c.fetchall()
        # daily orders
        self.c.execute('select * from dailyorders;')
        daily_orders=self.c.fetchall()
        # admin state
        self.c.execute('select name from users where admin=1')
        admins=c.fetchall()
        admin=1 if (self.current_user,) in admins else 0
        self.admin=1 if (self.current_user,) in admins else 0
        # places
        self.c.execute('select id,name,phone,web from restaurants')
        places=c.fetchall()
        self.c.execute('select id,name,phone,web from restaurants where selected=1')
        sel_place=c.fetchone()
        # can't remember why i do this :D
        self.wt_get_order_table()
        self.render("html/index.html", sel_place=sel_place, places=places, users=res, max_points=max_points, daily_orders=daily_orders, calling=calling_user, last_5_orders=self.wt_get_hist_table(), admin=admin)

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('user')
        self.redirect('/')

class ChoiceHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        # re.sub('[^\w\ ]','',a)
        if self.get_argument('1st'):
            self.c.execute('insert into dailyorders (name,meal) values(?,?)', (self.current_user, re.sub('[^\w\ ]', '', self.get_argument('1st'))) )
        if self.get_argument('2nd'):
            self.c.execute('insert into dailyorders (name,meal) values(?,?)', (self.current_user, re.sub('[^\w\ ]', '', self.get_argument('2nd'))) )
        if self.get_argument('3rd'):
            self.c.execute('insert into dailyorders (name,meal) values(?,?)', (self.current_user, re.sub('[^\w\ ]', '', self.get_argument('3rd'))) )
        self.db.commit()
        ws_bcast_msg('REFRESH_ORDERS', self.wt_get_order_table(), self.current_user)
        self.redirect('/')


class DropOrderHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.c.execute('delete from dailyorders where name=?', (self.current_user,))
        self.db.commit()
        ws_bcast_msg('REFRESH_ORDERS', self.wt_get_order_table(), self.current_user)
        self.redirect('/')

class PlaceOrderHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        tmp=self.get_arguments('orderfor')
        for_who=filter(lambda j: j!=self.current_user, tmp )

        if for_who:
            self.c.execute('insert into placedorder (who,timestamp) values (?,datetime())', (self.current_user,))
            self.c.execute('select last_insert_rowid()')
            last_id=self.c.fetchone()[0]
            for i in for_who:
                self.c.execute('update users set points=points+1 where name=?', (i,) )
                self.c.execute('insert into orders (orderid,forwho) values (?,?)', (last_id, i) )
                self.c.execute('delete from dailyorders where name=?',(i,))
            self.c.execute('update users set points=points-? where name=?', (len(for_who), self.current_user) )

        self.c.execute('update users set calling=(case calling when 0 then 1 when 1 then 0 end) where name=?',(self.current_user,))
        self.c.execute('update restaurants set selected=0')
        if self.current_user in tmp:
                self.c.execute('delete from dailyorders where name=?',(self.current_user,))
                #self.c.execute('insert into orders (orderid,forwho) values (?,?)', (last_id, self.current_user) )
        self.db.commit()
        ws_bcast_msg('REFRESH_MAIN', self.wt_get_main_table(), self.current_user)
        ws_bcast_msg('REFRESH_ORDERS', self.wt_get_order_table(), self.current_user)
        ws_bcast_msg('REFRESH_HIST', self.wt_get_hist_table(), self.current_user)
        ws_bcast_msg('REFRESH_PLACE', self.wt_get_selected_place(), self.current_user)
        self.redirect('/')

class CallingHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.c.execute('update users set calling=(case calling when 0 then 1 when 1 then 0 end) where name=?', (self.current_user,) )
        self.db.commit()
        ws_bcast_msg('REFRESH_MAIN', self.wt_get_main_table(), self.current_user)
        self.redirect('/')

class UserIncHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self,user):
        self.c.execute('select name from users where admin=1')
        admins=c.fetchall()
        admin=1 if (self.current_user,) in admins else 0
        if admin:
            self.c.execute('update users set points=points+1 where name=?', (user,) )
            # adding log trace
            self.c.execute('insert into placedorder (who,timestamp) values (?,datetime())', (self.current_user,))
            self.c.execute('select last_insert_rowid()')
            last_id=c.fetchone()[0]
            self.c.execute('insert into orders (orderid,forwho) values (?,?)', (last_id, user+" : admin +1") )

        else:
            self.render('html/fuckoff.html')
            return
        self.db.commit()
        ws_bcast_msg('REFRESH_MAIN', self.wt_get_main_table(), self.current_user)
        ws_bcast_msg('REFRESH_HIST', self.wt_get_hist_table(), self.current_user)
        self.redirect('/')

class UserDecHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self,user):
        self.c.execute('select name from users where admin=1')
        admins=c.fetchall()
        admin=1 if (self.current_user,) in admins else 0
        if admin:
            self.c.execute('update users set points=points-1 where name=?', (user,) )
            # adding log trace
            self.c.execute('insert into placedorder (who,timestamp) values (?,datetime())', (self.current_user,))
            self.c.execute('select last_insert_rowid()')
            last_id=c.fetchone()[0]
            self.c.execute('insert into orders (orderid,forwho) values (?,?)', (last_id, user+" : admin -1") )
        else:
            self.render('html/fuckoff.html')
            return
        self.db.commit()
        ws_bcast_msg('REFRESH_MAIN', self.wt_get_main_table(), self.current_user)
        ws_bcast_msg('REFRESH_HIST', self.wt_get_hist_table(), self.current_user)
        self.redirect('/')

class LoginHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.redirect('/')
            return
        self.render("html/login.html")

    def post(self):
        name=re.sub('[^\w\ ]', '', str(self.get_argument('name')))
        passwd=str(self.get_argument('passwd'))
        self.c.execute('select salt,passwd from users where name=?', (name, ) )
        db_data=c.fetchone()
        if db_data:
            (db_salt,db_pass)=db_data
        else:
            self.redirect('/login')
        if db_pass==hashlib.sha512(db_salt+passwd).hexdigest():
            # OK, password MATCHES
            self.set_secure_cookie("user", self.get_argument("name"))
        else:
            self.redirect('/login')
            return
        self.redirect("/")

class ChangePassHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('html/password.html')

    @tornado.web.authenticated
    def post(self):
        if not self.get_argument('old_pass') or not self.get_argument('new_pass'):
            self.redirect('/changepass')
            return

        o_pass=self.get_argument('old_pass')
        n_pass=self.get_argument('new_pass')

        self.c.execute('select salt,passwd from users where name=?', (self.current_user, ) )
        db_data=c.fetchone()
        (db_salt,db_pass)=db_data
        if db_pass!=hashlib.sha512(db_salt+o_pass).hexdigest():
            # OLD PASS DOESN'T MATCH, WE HAVE A POTENTIAL CASE OF MESNATA, ABORT AND LOG OUT!
            self.clear_cookie('user')
            self.redirect('/')
            return

        new_salt=uuid.uuid4().hex
        new_pass=hashlib.sha512(new_salt+n_pass).hexdigest()
        self.c.execute('update users set salt=? where name=?', (new_salt, self.current_user))
        self.c.execute('update users set passwd=? where name=?', (new_pass, self.current_user))
        self.db.commit()
        self.redirect('/')

class PlaceSelHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, place):
        place=re.sub('[^\w\ ]', '', place)
        if place=="None":
            self.c.execute('update restaurants set selected=0')
            self.db.commit()
        else:    
            self.c.execute('update restaurants set selected=1 where id=?', (place,) )
            self.db.commit()
            self.c.execute('update restaurants set selected=0 where id!=?', (place,) )
            self.db.commit()
        ws_bcast_msg('REFRESH_PLACE', self.wt_get_selected_place(), self.current_user)
        self.redirect('/')

wsclients=[]

def ws_bcast_msg(msg,data,who):
    for i in wsclients:
        i.write_message({'oid':msg, 'who':who, 'adm':i.admin, 'data':data, 'calling':i.wt_am_calling()})

class WebSocket(tornado.websocket.WebSocketHandler):
    def initialize(self, database=None, cursor=None):
        self.db=database
        self.c=cursor
        self.admin=0
        self.calling=0

    def wt_am_calling(self):
        self.c.execute('select calling from users where name=?', (self.current_user,))
        calling=self.c.fetchone()[0]
        self.calling=calling
        return calling

    def get_current_user(self):
        return self.get_secure_cookie("user")

    def check_origin(self, origin):
        return True

    def open(self):
        if not self.get_secure_cookie("user"):
            print "ANON connected to ws, not allowed for pushes"
            return None
        self.c.execute('select name from users where admin=1')
        admins=c.fetchall()
        self.admin=1 if (self.current_user,) in admins else 0
        wsclients.append(self)
        print "WS: add client"+str(self)
        #self.write_message('Wellcome to websocket world!')

    def on_close(self):
        if not self.get_secure_cookie("user"):
            print "ANON closing down ws, that's fine"
            return None
        wsclients.remove(self)
        print "WS: remove client"+str(self)

    def on_message(self, message):
        print "WS: recieved msg:"+message


settings={ 
'autoreload':True, 
'debug':True, 
'static_path':'./html/bootstrap/',
'login_url':'/login',
"cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__"
}


if __name__ == "__main__":
    db=sqlite3.connect('wt.db')
    c=db.cursor()
    params=dict(database=db, cursor=c)

    application = tornado.web.Application([
        (r"/", MainHandler, params),
        (r"/login", LoginHandler, params),
        (r"/calling", CallingHandler, params),
        (r"/choice", ChoiceHandler, params),
        (r"/droporder", DropOrderHandler, params),
        (r"/placeorder", PlaceOrderHandler, params),
        (r"/logout", LogoutHandler, params),
        (r"/user/(.*)/increment", UserIncHandler, params),
        (r"/user/(.*)/decrement", UserDecHandler, params),
        (r"/place/(.*)/select", PlaceSelHandler, params),
        (r"/main_list", MainListHandler, params),
        (r"/changepass", ChangePassHandler, params),
        (r"/ws", WebSocket, params),
    ], **settings)

    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
    c.close()
    db.close()
