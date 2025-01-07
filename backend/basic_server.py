# basic_server.py
import tornado.httpserver
import tornado.ioloop
import tornado.web
class RootHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello World")

application = tornado.web.Application([(r"/", RootHandler),])
if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application, ssl_options={
    "certfile": "cert.pem",
    "keyfile": "key.pem",
    "ca_certs": "fullchain.pem",
    })
    http_server.listen(443)
    tornado.ioloop.IOLoop.instance().start()