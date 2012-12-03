from zorro import zerogw, web
from zorro.di import has_dependencies, dependency


@has_dependencies
class Pager(web.Resource):

    output = dependency(zerogw.JSONWebsockOutput, "output")

    @web.method
    def send(self, text):
        self.output.publish('pager', ['pager.message', text])


class Websockets(web.Websockets):

    def handle_connect(self, call):
        self.output.subscribe(call, b'pager')
