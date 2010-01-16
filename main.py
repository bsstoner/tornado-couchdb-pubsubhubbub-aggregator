import logging
import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import os.path
import uuid

from datetime import datetime

# For pubsub subscriptions
import feedparser

try:
    import couchdb
except ImportError:
    raise ImproperlyConfigured, "Could not load couchdb dependency.\
    \nSee http://code.google.com/p/couchdb-python/"

from tornado.options import define, options

define("port", default=8001, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            #(r"/auth/login", AuthLoginHandler),
            #(r"/auth/logout", AuthLogoutHandler),
            #(r"/feeds/([^/]+)", FeedEntriesHandler),
            #(r"/feeds/add", FeedAddHandler),
            (r"/feeds/getupdates", ClientUpdatesHandler),
            (r"/feeds/update/?", FeedUpdateHandler),
        ]
        settings = dict(
            cookie_secret="43oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            login_url="/auth/login",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static")
            #xsrf_cookies=True
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    @property
    def dbserver(self):
        return couchdb.client.Server("http://localhost:5984")

class MessageMixin(object):
    waiters = []
    cache = []
    cache_size = 200

    def wait_for_messages(self, callback, cursor=None):
        cls = MessageMixin
        if cursor:
            index = 0
            for i in xrange(len(cls.cache)):
                index = len(cls.cache) - i - 1
                if cls.cache[index]["id"] == cursor: break
            recent = cls.cache[index + 1:]
            if recent:
                callback(recent)
                return
        cls.waiters.append(callback)

    def new_messages(self, messages):
        cls = MessageMixin
        logging.info("Sending new message to %r listeners", len(cls.waiters))
        for callback in cls.waiters:
            try:
                callback(messages)
            except:
                logging.error("Error in waiter callback", exc_info=True)
        cls.waiters = []
        cls.cache.extend(messages)
        if len(cls.cache) > self.cache_size:
            cls.cache = cls.cache[-self.cache_size:]


class MainHandler(BaseHandler):

    def get(self):
        db = self.dbserver['entries']
        entries_all = []
        for row in db.view("_view/entries/all_docs",count=20,descending=True):
            entries_all.append(row.value)
        self.render("index.html", entries=entries_all)#MessageMixin.cache)
    
    def post(self):
        f = self.get_argument('feedname')
        furl = self.get_argument('feedurl')

        db = self.dbserver['feeds']
        db.create({'name':f,'feed_url':furl})
        self.redirect("/")

class FeedUpdateHandler(BaseHandler, MessageMixin):
    
    def get(self):
        c = self.get_argument('hub.challenge')
        self.set_status(200)
        self.set_header("Content-Type", "text/plain")
        self.write(c)
        
    def post(self):
        feed = feedparser.parse(self.request.body)
        db = self.dbserver['entries']
        latest_es = []
        for e in feed.entries:
            entry_dict = {'title':e.title,
                          'link':e.link,
                          'receive_time':str(datetime.now()),
                          'full_entry':str(e)}
            
            e_id = db.create(entry_dict)
            entry_dict['_id'] = e_id
            latest_es.append(entry_dict)
            
        self.new_messages(latest_es)
        
        self.set_status(200)
        self.set_header("Content-Type", "text/plain")
        self.write('OK')

class ClientUpdatesHandler(BaseHandler, MessageMixin):
    @tornado.web.asynchronous
    def post(self):
        cursor = self.get_argument("cursor", None)
        self.wait_for_messages(self.async_callback(self.on_new_messages),
                               cursor=cursor)

    def on_new_messages(self, messages):
        # Closed client connection
        if self.request.connection.stream.closed():
            return
        self.finish(dict(messages=messages))

        
def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
