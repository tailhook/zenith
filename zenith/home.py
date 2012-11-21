import json
import logging

from zorro import web
from zorro.redis import Redis
from zorro.di import di, has_dependencies, dependency


log = logging.getLogger(__name__)


class Home(web.Resource):

    def __init__(self, user):
        self.user = user

    @web.page
    def index(self):
        return 'Hello, {}'.format(self.user.name)


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
        if 'sid' not in req.cookies:
            raise web.CompletionRedirect('/login')
        inj = di(resolver.resource)
        redis = inj['redis']
        uid = redis.execute("GET", 'z:session:' + req.cookies['sid'])
        if uid is None:
            raise web.CompletionRedirect('/login')
        uid = int(uid)
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
