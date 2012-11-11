import jinja2
from zorro import Hub
from zorro import zmq
from zorro import web
#from zorro.di import DependencyInjector

#from .auth import Auth


class About(web.Resource):

    @web.page
    def index(self):
        return "Hello World!"


class Request(web.Request):

    def __init__(self, uri):
        self.uri = uri


def main():

#    inj = DependencyInjector()
#    inj['jinja'] = jinja2.Environment(
#        loader=jinja2.FileSystemLoader('./templates'))

    site = web.Site(
        request_class=Request,
        resources=[
            About(),
        ])
    sock = zmq.rep_socket(site)
    sock.dict_configure({'connect': 'ipc://./run/http.sock'})


if __name__ == '__main__':
    hub = Hub()
    hub.run(main)
