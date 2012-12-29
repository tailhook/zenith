from zorro import zerogw, web
from zorro.di import di, has_dependencies, dependency
from zorro.redis import Redis

from .home import User


@has_dependencies
class Pager(web.Resource):

    output = dependency(zerogw.JSONWebsockOutput, "output")

    @web.method
    def send(self, user: User, text: str):
        self.output.publish('pager', ['pager.message', user.name, text])


@has_dependencies
class WebsockAuth(web.Resource):

    redis = dependency(Redis, "redis")
    output = dependency(zerogw.JSONWebsockOutput, "output")

    @web.method
    def hello(self, conn: web.WebsockCall, sid: str):
        uid = self.redis.execute("GET", 'z:session:' + sid)
        if uid:
            uid = int(uid)
            self.output.set_cookie(conn, 'user:{}'.format(uid))
            user = User(uid)
            di(self).inject(user)
            user.load()
            return {'uid': uid, 'name': user.name}


class Websockets(web.Websockets):

    def handle_connect(self, call):
        self.output.subscribe(call, b'pager')
