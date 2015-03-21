#!/usr/local/bin/python

import tornado.ioloop
import tornado.web
import tornado.websocket
import sqlite3

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, database=None, cursor=None):
        self.db=database
        self.c=cursor

    def get_current_user(self):
        return self.get_secure_cookie("user")

class MainHandler(BaseHandler):
    def get(self):
        self.c.execute('select name, points from users;')
        res=sorted(self.c.fetchall(), key=lambda i: i[1] , reverse=True)
        max_points=max(map(lambda i: i[1], res))
        self.c.execute('select name from users where calling=1;')
        calling_user=self.c.fetchall()
        self.c.execute('select * from dailyorders;')
        daily_orders=self.c.fetchall()
        self.c.execute('select name from users where admin=1')
        admins=c.fetchall()
        admin=1 if (self.current_user,) in admins else 0
        self.c.execute('select placedorder.*, group_concat(orders.forwho) from placedorder inner join orders where placedorder.id=orders.orderid group by placedorder.id order by placedorder.id desc limit 5')
        last_5_orders=self.c.fetchall()
        self.render("html/index.html", users=res, max_points=max_points, daily_orders=daily_orders, calling=calling_user, last_5_orders=last_5_orders, admin=admin)

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('user')
        self.redirect('/')

class ChoiceHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        if self.get_argument('1st'):
            self.c.execute('insert into dailyorders (name,meal) values(?,?)', (self.current_user, self.get_argument('1st')))
        if self.get_argument('2nd'):
            self.c.execute('insert into dailyorders (name,meal) values(?,?)', (self.current_user, self.get_argument('2nd')))
        if self.get_argument('3rd'):
            self.c.execute('insert into dailyorders (name,meal) values(?,?)', (self.current_user, self.get_argument('3rd')))
        self.db.commit()
        ws_force_reload()
        self.redirect('/')

class DropOrderHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.c.execute('delete from dailyorders where name=?', (self.current_user,))
        self.db.commit()
        ws_force_reload()
        self.redirect('/')

class PlaceOrderHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        tmp=self.get_arguments('orderfor')
        for_who=filter(lambda j: j!=self.current_user, tmp )

        if for_who:
            self.c.execute('insert into placedorder (who,timestamp) values (?,datetime())', (self.current_user,))
            self.c.execute('select last_insert_rowid()')
            last_id=c.fetchone()[0]
            for i in for_who:
                self.c.execute('update users set points=points+1 where name=?', (i,) )
                self.c.execute('insert into orders (orderid,forwho) values (?,?)', (last_id, i) )
                self.c.execute('delete from dailyorders where name=?',(i,))
            self.c.execute('update users set points=points-? where name=?', (len(for_who), self.current_user) )

        self.c.execute('update users set calling=(case calling when 0 then 1 when 1 then 0 end) where name=?',(self.current_user,))
        if self.current_user in tmp:
                self.c.execute('delete from dailyorders where name=?',(self.current_user,))
                #self.c.execute('insert into orders (orderid,forwho) values (?,?)', (last_id, self.current_user) )
        self.db.commit()
        ws_force_reload()
        self.redirect('/')

class CallingHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.c.execute('update users set calling=(case calling when 0 then 1 when 1 then 0 end) where name=?', (self.current_user,) )
        self.db.commit()
        ws_force_reload()
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
        self.db.commit()
        ws_force_reload()
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
        self.db.commit()
        ws_force_reload()
        self.redirect('/')

class LoginHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.redirect('/')
        self.render("html/login.html")

    def post(self):
        name=str(self.get_argument('name'))
        passwd=str(self.get_argument('passwd'))
        self.c.execute('select * from users where name=? and passwd=?', (name, passwd) )
        if self.c.fetchall():
            self.set_secure_cookie("user", self.get_argument("name"))
        else:
            self.redirect('/login')
        self.redirect("/")

wsclients=[]

def ws_force_reload():
    for i in wsclients:
        i.write_message('RELOAD')

class WebSocket(tornado.websocket.WebSocketHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

    def check_origin(self, origin):
        return True

    def open(self):
        if not self.get_secure_cookie("user"):
            print "ANON connected to ws, not allowed for pushes"
            return None
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
        (r"/ws", WebSocket),
    ], **settings)

    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
    c.close()
    db.close()
