===============
Zenith Tutorial
===============

This tutorial describes how to create breathtaking game with the following
technologies (in no meaningful order):

* python3.3
* redis
* zorro
* jinja2
* wtforms
* zeromq
* zerogw
* JSON
* HTML5

We expect that reader is familiar with Python and HTML5. We concentrate on
zorro and zerogw as the least known tools from the above. Everything else is
touched only superficially, but in a way that's easy to grasp if you don't
used them before.


Quick Start
===========

You start by installing all of the above. That part is boring and we expect
that reader is quite familiar with most of the tools. All they have documented
installation procedure.

First we introduce the folder structure, and empty files::

  zenith
    public
      js
        game.js
      css
        main.css
    zenith
      __init__.py
      __main__.py
    templates
    config
      zerogw.yaml

Everything should be easy so far. The files will be populated step by step.


Python Boilerplate
==================

We'll start with simple hello world application. Let's fill in
``zenith/__main__.py``::

    from zorro import Hub
    from zorro import zmq
    from zorro import web


    class About(web.Resource):

        @web.page
        def index(self):
            return "Hello World!"


    class Request(web.Request):

        def __init__(self, uri):
            self.uri = uri


    def main():

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

Here the ``web.page`` denotes a page visible to the user. ``index`` is a
special page, which is dispayed for the root of the site.

``Request`` class stores the request parameters got from zerogw. So far we
need only URI. We need to configure zerogw in the same way. Will get there
shortly.

``web.Site`` is just a wrapper which does dirty work for us. There could be
more resources in the list, which are checked in turn, but we have only one so
far.

``zmq.rep_socket`` creates the ``REP`` socket (in zeromq terms), which is
replier part of request-reply pattern. That's actually what we will use the
socket for. Also remember that we use ``connect`` to configure socket, it will
be important to configure zerogw right.

``Hub`` class is the main loop abstraction. Unless you will implement some
low-level nasty things you will never interact to it directly. Just remember
to run all your code in by ``Hub().run``



Zerogw Configuration
====================

To see anything in the browser, we need to configure zerogw, so lets start
with ``zerogw.yaml``. First we configure zerogw to run on non-privileged port:

    Server:
      listen:
        - host: 127.0.0.1
          port: 8000

If you're not familiar with YAML there are few rules of thumb:

* Indentation used for nesting elements
* Words with colons at the end used to designate mappings
* Dashed are used for lists

So above is the section ``Server`` which consists of property ``listen`` which
is a list of addresses to listen. Listen address has self-descriptive ``host``
and ``port`` properties.

Now we've got to the point, where we should define how URL's are served.
Append the following into ``zerogw.yaml``::

    Routing:
      routing: !Prefix
      routing-by: !Path
      map:
        /js/*: &static
          static:
            enabled: yes
            root: ./public
            restrict-root: no
        /css/*: *static
        /*:
          zmq-forward:
            enabled: yes
            socket: !zmq.Req
            - !zmq.Bind ipc://./run/http.sock
            contents:
            - !Uri

Unlike other servers, which have fixed routing scheme (usually uses host and
url), zerogw allows routing by range of different things. This may seem
complex by first glance, but as you understand basic structure it will be
trivial.

So the section ``Routing`` denotes the root route. If we have only single rule
for urls we could write configuration here. But we need to serve both static
files and pages from python script. So we set ``routing-by`` to ``!Path``
which is same as ``!Uri`` but with ``?query=string`` stripped. This means that
child routes will be matched based on the path. We also set ``routing`` to
``!Prefix`` which means that children routes are matched by path prefix. The
actual prefixes are under the ``map:`` section.

There is ``/js/*`` prefix (where ``*`` means there might be anything) which is
served from the ``./public`` folder. Note that matched prefix is not stripped from the url when serving files. So actual files will be inside ``public/js``. Note also that ``&static`` means that the following nested structure is remembered (anchored) for future reference. It's YAML feature.

The next route ``/css/*`` just uses the same structure that was anchored by
``&static`` using ``*`` (star) character. You can reuse any part of YAML file
this way. As the actual prefix is not stripped from the path when resolved
names, the files will be served from ``public/css`` which was intended.

Static routes should be clear now except ``restrict-root`` option. When the
option is turned on zerogw checks if every path that's served is not a symlink
to the outside of the root dir. It's usually safer to keep it ``yes`` (that's
why it's default), but zerogw can't do this for relative paths. If this
paragraph is unclear just remember to set the option to ``no`` when paths are
relative, and set it to ``yes`` and set absolute path in ``root`` for
production configuration.

Now the ``/*`` route. It's fallback. In other words every request that is not
matched by other rules will fall here. The order of the rules doesn't matter.
The rule that matches longer will be used. Note, only matching path considered
here not the actual existence of the file on disk.

As you probably already guessed, the fallback route is to connect to python.
The ``!zmq.`` prefixed tags (basically the unquoted words that are prefixed by
exclamation mark are tags in YAML) are used to define zeromq socket kind. We
use ``REQ`` socket to connect to ``REP`` socket at python side. And we
``bind`` zeromq socket at zerogw side to be able to start multiple processes
that are ``connect``ed to the zerogw instance. And of course we use the same
zeromq address that we specified in python.

If you are not familiar with zeromq concepts, this may be time to do so. But
to proceed you should know that 99% percents of the cases need exactly this
kind of setup.

Next step is to run zerogw and python and verify it works::

    zerogw -c config/zerogw.yaml &
    python -m zenith

Now let's to to ``http://localhost:8000/`` and check. We should see ``Hello
World!``. You can also check some static file like
``http://localhost:8000/css/main.css``. It would be nice to put some comments
in that file, to verify it's served correctly.


