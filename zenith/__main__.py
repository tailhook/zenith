import jinja2
from zorro import Hub
from zorro import zmq
from zorro import web
from zorro.di import DependencyInjector, has_dependencies, dependency

from .util import template


@has_dependencies
class About(web.Resource):

    jinja = dependency(jinja2.Environment, 'jinja')

    @web.page
    @template('index.html')
    def index(self):
        return {}


class Request(web.Request):

    def __init__(self, uri):
        self.uri = uri


def main():

    inj = DependencyInjector()
    inj['jinja'] = jinja2.Environment(
        loader=jinja2.FileSystemLoader('./templates'))

    site = web.Site(
        request_class=Request,
        resources=[
            inj.inject(About()),
        ])
    sock = zmq.rep_socket(site)
    sock.dict_configure({'connect': 'ipc://./run/http.sock'})


if __name__ == '__main__':
    hub = Hub()
    hub.run(main)
