import json
import logging
import jinja2

from zorro import web
from zorro.redis import Redis
from zorro.di import di, has_dependencies, dependency

from .util import template


log = logging.getLogger(__name__)


@has_dependencies
class Home(web.Resource):

    jinja = dependency(jinja2.Environment, 'jinja')

    def __init__(self, user):
        self.user = user

    @web.page
    @template('home.html')
    def index(self):
        return {
            'user': self.user,
            }


@has_dependencies
class User(web.Sticker):

    redis = dependency(Redis, 'redis')

    def __init__(self, uid):
        self.uid = uid
        self.level = 1
        self.name = None
        self.email = None

    @classmethod
    def create(cls, resolver):
        req = resolver.request
        inj = di(resolver.resource)
        if isinstance(req, web.Request):
            if 'sid' not in req.cookies:
                raise web.CompletionRedirect('/login')
            redis = inj['redis']
            uid = redis.execute("GET", 'z:session:' + req.cookies['sid'])
            if uid is None:
                raise web.CompletionRedirect('/login')
            uid = int(uid)
        elif isinstance(req, web.WebsockCall):
            marker = getattr(req, 'marker', None)
            if not marker or not marker.startswith(b'user:'):
                raise web.Forbidden()
            uid = int(marker[len('user:'):])
        else:
            raise AssertionError("Wrong request type {!r}".format(req))
        user = inj.inject(User(uid))
        user.load()
        return user

    def load(self):
        data = self.redis.execute("GET", 'z:user:{}'.format(self.uid))
        if data:
            properties = json.loads(data.decode('utf-8'))
            for k, v in properties.items():
                setattr(self, k, v)

    def save(self):
        self.redis.execute("SET", 'z:user:{:d}'.format(self.uid),
            json.dumps({
                'level': self.level,
                'name': self.name,
                'email': self.email,
                }).encode('utf-8'))
