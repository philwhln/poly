import sys
import os
import logging
sys.path.append("src")
import tornado.ioloop
import tornado.web
import tornado.autoreload
import tornado.options
from tornado.options import options, define
from glupy.handlers.main import MainHandler
from glupy.handlers.twitter_oauth import TwitterHandler, LogoutHandler
from glupy.handlers.api.user import ApiUserHandler
from glupy.handlers.api.user_list import ApiUserListHandler
import pymongo
import simplejson as json
from simplejson import JSONDecodeError

mongodb_options = {
    "host": "localhost",
    "port": 27017,
    "db": "glupy"
}
stackato_services_json = os.environ.get("STACKATO_SERVICES", None)
if stackato_services_json:
    try:
        stackato_services = json.loads(stackato_services_json)
        mongodb_options = stackato_services["glu-db"]
    except JSONDecodeError as e:
        logging.warn("Could not decode STACKATO_SERVICES env. Falling back to default mongodb connection parameters.")

define("listen_port", default=None, help="run on the given port", type=int)
define("listen_addr", default=None, help="bind to given host", type=str)
define("debug", default=False, help="debug mode", type=bool)

root_dir = os.path.join(os.path.dirname(__file__), "..", "..")
application = tornado.web.Application(
    [
        (r"^/$", MainHandler),
        (r"^/login$", TwitterHandler),
        (r"^/logout$", LogoutHandler),
        (r"^/oauth/twitter", TwitterHandler),
        (r"^/api/user(?:/(?P<twitter_screen_name>[^/\s]+))?$", ApiUserHandler),
        (r"^/api/users$", ApiUserListHandler)
    ],
    template_path=os.path.join(root_dir, "templates"),
    static_path=os.path.join(root_dir, "static")
)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    application.listen(
        options.listen_port or application.settings["listen_port"],
    )
    application.settings["twitter_consumer_key"] = \
       os.environ.get("TWITTER_CONSUMER_KEY")
    application.settings["twitter_consumer_secret"] = \
        os.environ.get("TWITTER_CONSUMER_SECRET")
    application.settings["cookie_secret"] = "dsisj2ir9fjsifsinmfn232342fdsfqqa"
    application.settings["login_url"] = "/login"
    application.mongo = pymongo.MongoClient(
        host=mongodb_options["host"],
        port=mongodb_options["port"]
    )[mongodb_options["db"]]
    if mongodb_options.has_key("username"):
        application.mongo.authenticate(mongodb_options["username"], mongodb_options["password"])
    tornado.autoreload.start()
    print "Starting server"
    tornado.ioloop.IOLoop.instance().start()

