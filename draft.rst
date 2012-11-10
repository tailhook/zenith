===============
Zenith Tutorial
===============

This tutorial describes how to create breathtaking game with the following
technologies (in no meaningful order):

* python3.3
* redis
* zorro
* jinja2
* zeromq
* zerogw
* YAML
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
    config
      zerogw.yaml

Everything should be easy so far. The files will be populated step by step.


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

Now we've got to the point, where we should define how URL's are served. For
nowe configure only static, from the ``public`` directory. Add the following
into the ``zerogw.yaml``::

    Routing:
      static:
        enabled: yes
        root: ./public
        restrict-root: no

Everything should be clear except ``restrict-root`` option. When the option is
turned on zerogw checks if every path that's served is not a symlink to the
outside of the root dir. It's usually safer to keep it ``yes`` (that's why
it's default), but zerogw can't do this for relative paths. If this paragraph
is unclear just remember to set the option to ``no`` when paths are relative,
and set it to ``yes`` and set absolute path in ``root`` for production
configuration.

Next step is to run zerogw and verify it works::

    zerogw -c config/zerogw.yaml

Now let's to to http://localhost:8000/css/main.css and check. It would be nice
to put some comments in that file, to verify it's served correctly.


