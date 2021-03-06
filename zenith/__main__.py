import sys

import jinja2
import zorro
from zorro import Hub
from zorro import zmq
from zorro import web
from zorro import zerogw
from zorro.di import DependencyInjector, has_dependencies, dependency
from zorro import redis

from .util import template
from .auth import Auth
from .websock import Websockets, Pager, WebsockAuth


@has_dependencies
class About(web.Resource):

    jinja = dependency(jinja2.Environment, 'jinja')

    @web.page
    @template('index.html')
    def index(self):
        return {}

    @web.page
    @template('about.html')
    def about(self):
        return {
            'py_version': sys.version,
            'zorro_version': zorro.__version__,
            }


class Request(web.Request):

    def __init__(self, uri, cookie, content_type, body):
        self.uri = uri
        self.cookie = cookie
        self.content_type = content_type
        self.body = body


def main():

    inj = DependencyInjector()
    inj['jinja'] = jinja2.Environment(
        loader=jinja2.FileSystemLoader('./templates'))
    inj['redis'] = redis.Redis(host='127.0.0.1', port=6379)

    site = web.Site(
        request_class=Request,
        resources=[
            inj.inject(About()),
            inj.inject(Auth()),
        ])
    sock = zmq.rep_socket(site)
    sock.dict_configure({'connect': 'ipc://./run/http.sock'})

    sock = zmq.pub_socket()
    sock.dict_configure({'connect': 'ipc://./run/sub.sock'})
    output = zerogw.JSONWebsockOutput(sock)
    inj['output'] = output

    sock = zmq.pull_socket(inj.inject(Websockets(
        resources=[web.DictResource({
            'pager': inj.inject(Pager()),
            'auth': inj.inject(WebsockAuth()),
            })],
        output=output,
        )))
    sock.dict_configure({'connect': 'ipc://./run/fw.sock'})


if __name__ == '__main__':
    hub = Hub()
    hub.run(main)
