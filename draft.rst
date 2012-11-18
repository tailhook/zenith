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
    run

The ``run`` folder is there for temporary files created at server runtime
(It's not called ``tmp`` because I'm using latter for my own temporary files.
Nevermind, it's just personal preference)

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

If you are not familiar with python3, the ``__main__.py`` is the file that's
got run when package (``python -m zenith``) is executed.

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


Version Control Everything
==========================

If you haven't put your code into version control, it's time to run ``git
init``. We aren't going to annoy you each time, but commiting at least after
each step of the tutorial is going to save you a lot of time. It will also let
you remember how to implement the feature X in the future when you'll write
some real project.


Jinja Templates
===============

We aren't going to write all the HTML in the python code. So let's do some
jinja templating. Let's start with base template ``templates/base.html``::

    <!DOCTYPE html>
    <head>
        <title>{% block title %}Zenith{% endblock %}</title>
        <link rel="stylesheet" href="/css/main.css">
    </head>
    <body>
        <h1>{{ self.title() }}</h1>
        {% block body %}{% endblock %}
        <footer>Zenith (c) Your Name Here</footer>
    </body>

And the start page of our project ``templates/index.html::

    {% extends file="base.html"%}
    {% block title %}Welcome to Zenith!{% endblock %}
    {% block body %}
    <ul>
        <li><a href="/login">Login</a></li>
        <li><a href="/register">Login</a></li>
        <li><a href="/about">about</a></li>
    </ul>
    {% endblock body %}

Now let's tie the pieces together. The ``zenith/__main__.py`` should now look
like the following (highlighted lines are new):

.. code-block:: python
   :emphasize-lines: 1,5,10,13,16,18,29-31
   :linenos:

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

There are two things changed here. All over the place we've added dependency
injection (DI). It works by declaring a dependency for the class (line 10 and
13), and by calling ``inject`` method (line 36) on a special object called
DependencyInjector. The latter holds a mapping of components which can be
declared as dependencies is any class. We'll show how dependencies got
propagated later on.

In this example it's unclear why we use DI instead of just passing the object
to the constructor, but in bigger application this saves a lot of code.

The ``template`` decorator renders jinja template, here is how it looks like
in ``zenith/util.py``::

    from zorro import web

    def template(name):
        def decorator(fun):
            @web.postprocessor(fun)
            def wrapper(self, resolver, data):
                return ('200 OK',
                        'Content-Type\0text/html; charset=utf-8\0',
                        self.jinja.get_template(name).render(data))
            return wrapper
        return decorator

Now you can restart the python process and see nice web page instead of plain
``Hello World!``.

To make project real, we need an ``/about`` page. Add the following to
``About`` class in ``zenith/__main__.py``::

    import zorro
    import sys

    class About(web.Resource):
    ...
        @web.page
        @template('about.html')
        def about(self):
            return {
                'py_version': sys.version,
                'zorro_version': zorro.__version__,
                }

The ``templates/about.html`` might look like the following::

    {% extends "base.html"%}
    {% block title %}Zenith Tutorial!{% endblock %}
    {% block body %}
    Powered by:
    <ul>
        <li>Python {{ py_version }}</li>
        <li>Zorro {{ zorro_version }}</li>
    </ul>
    {% endblock body %}

After restarting python you can point your browser to
``http://localhost:8000/about`` and check the result.

Now, you know how to add pages and pass variables into template. Now let's
proceed to make forms which we need to implement authentication.


Forms
=====

We need a separate resource for ``/login`` and ``/register`` pages. So let's create ``zenith/auth.py``::

    import jinja2
    import wtforms
    from wtforms import validators as val
    from zorro.web import Resource
    from zorro.di import has_dependencies, dependency

    from .util import form, template


    class LoginForm(wtforms.Form):
        login = wtforms.TextField('Name or Email',
            validators=[val.Required()])
        password = wtforms.PasswordField('Password',
            validators=[val.Required()])


    class RegisterForm(wtforms.Form):
        name = wtforms.TextField('Name',
            validators=[val.Required(), val.Length(min=3, max=24)])
        email = wtforms.TextField('E-mail',
            validators=[val.Required(), val.Email()])
        password = wtforms.PasswordField('Password',
            validators=[val.Required()])
        cpassword = wtforms.PasswordField('Confirm Password',
            validators=[val.Required(), val.EqualTo('password')])


    @has_dependencies
    class Auth(web.Resource):

        jinja = dependency(jinja2.Environment, 'jinja')

        @template('login.html')
        @form(LoginForm)
        @web.page
        def login(self, login, password):
            raise web.CompletionRedirect('loginok')

        @template('register.html')
        @form(RegisterForm)
        @web.page
        def register(self, name, email, password, cpassword):
            raise web.CompletionRedirect('registerok')

To make it basically work, we need to implement a ``form`` decorator::

    def form(form_class):
        def decorator(fun):
            @web.decorator(fun)
            def form_processor(self, resolver, meth, *args, **kw):
                form = form_class(resolver.request.legacy_arguments)
                if kw and form.validate():
                    return meth(**form.data)
                else:
                    return dict(form=form)
            return form_processor
        return decorator

It's a bit complex, so we'll try to explain most lines:

* ``@web.decorator`` is mostly like ``functools.wraps`` except it doesn't
  replace the actual function. It works by informing ``zorro.web`` framework
  to call the decorator instead the specified method on request processing
  (the ``web.preprocessor`` shown before does similar thing, except it called
  after processing is finished). We'll show why this is useful shortly
* ``legacy_arguments`` is an object with ``MultiDict`` interface which is
  needed for ``wtforms``. We call it ``legacy`` because it creates more
  problems than it solves (comparing to using just dict for arguments)
* If the form is validated we pass the clean form values to the actual method,
  otherwise we just return the form in the dict, so that ``template``
  decorator will render page with specified form inside
* The ``meth`` argument must be called instead of actual function to allow
  apropriate chaining of the decorators

Now we need to implement some rendering for the forms. We'll do this with a
macro. Let's put the following into ``templates/form.html``:

    {% macro render_form(form, method='POST', submit_text="Submit") %}
    <form method="{{ method }}">
    <ul>
    {% for field in form %}
        <li>{{ field.label }} {{ field }}
            {% if field.errors %}
                <ul>
                    {% for er in field.errors %}
                        <li>{{ er }}</li>
                    {% endfor %}
                </ul>
            {% endif %}
            </li>
    {% endfor %}
    </ul>
    <input type="submit" value="{{ submit_text }}">
    </form>
    {% endmacro %}

That was easy. Let's design ``login.html``:

    {% extends "base.html"%}
    {% from "form.html" import render_form %}
    {% block title %}Sign In{% endblock %}
    {% block body %}
    {{ render_form(form, method="GET") }}
    {% endblock body %}

To see some result immediately we use ``GET`` method, of course it's wrong for
the real work, but we'll fix it shortly.  We give ``register.html`` as an exercise to the reader.

Finally to tie all pieces together, let's put ``Auth`` resource into the list
of resources the site is going to invoke (``zenith/__main__.py``). Example::

    from .auth import Auth
    ...
        site = web.Site(
            request_class=Request,
            resources=[
                inj.inject(About()),
                inj.inject(Auth()),
            ])

After restarting server we can now go to ``http://localhost:8000/login`` and
see the form. After filling some data into the form you should be redirected
to ``http://localhost:8000/loginok`` and see ``404 Not Found`` there. It's
normal we'll fix it in the following sections.


POST Requests
=============

Let's take a look at our written request class again::

    class Request(web.Request):

        def __init__(self, uri):
            self.uri = uri

It only holds ``URI`` of the request, but to process form with ``method=POST`` we also need ``Content-Type`` header and body of the post request. Let's configure zerogw to send those fields to us. Fix the ``config/zerogw.yaml`` so that our default route looks like (highlighted lines are new):

.. code-block:: yaml
   :emphasize-lines: 7,8

    zmq-forward:
      enabled: yes
      socket: !zmq.Req
      - !zmq.Bind ipc://./run/http.sock
      contents:
      - !Uri
      - !Header Content-Type
      - !PostBody

Now if we restart the server all requests will crash. To fix the situation we should update our ``Request`` object::

    class Request(web.Request):

        def __init__(self, uri, content_type, body):
            self.uri = uri
            self.content_type = content_type
            self.body = body

Note, the order of arguments for request object is the same as the order of
fields in zerogw config. Note also that for keyword arguments and
``legacy_arguments`` to work with forms, the names of the properties on the
requested object must be exactly as written above (there are actually 4
reserved fields on request object, we'll learn fourth one later).

We are ready to consume ``POST`` forms now. Let's remove the ``method="GET"``
hack from ``login.html`` and ``register.html`` and check whether ``POST`` forms
work.


Adding Redis
============

We want to keep users in redis database. Note that redis must be configured
well to run persistently. It's not that important for the tutorial, so we
assume you have redis configured and running.

First we put redis connection into dependency injector, so any class can use
it as dependency (``zenith/__main__.py``)::

    from zorro import redis

    def main():
        ...
        inj['redis'] = redis.Redis(host='127.0.0.1', port=6379)
        ...

As you may have different applications residing on your local development
redis, we will use ``z:`` prefix for all our data. Usually data scheme is
aggreed on before starting to code, but we will describe it step by step to
make tutorial a bit easier.

We start with login form. To keep data structures compact we have users
denoted by integer user id or ``uid``. At ``z:names`` we  keep a mapping
(redis hash) of the name and email to uid. Each user has two hash entries one
for name and one for email, so it can be logged in both by name and by email.
At ``z:user:<uid>:password`` we store a salted and hashed password. That's all
we need so far. Let's update ``LoginForm`` to check for password::

    @has_dependencies
    class LoginForm(wtforms.Form):
        login = wtforms.TextField('Name or Email',
            validators=[val.Required()])
        password = wtforms.PasswordField('Password',
            validators=[val.Required()])

        redis = dependency(Redis, 'redis')

        def validate_password(self, field):
            uid = self.redis.execute('HGET', 'z:names', self.login.data)
            if uid is None:
                raise ValueError("Name or password is wrong")
            uid = int(uid)
            pw = self.redis.execute('GET', 'z:user:{}:password'.format(uid))
            if pw is None:
                raise ValueError("Name or password is wrong")
            assert pw[0] == b'A'[0], 'Algorithm for storing password is wrong'
            assert len(pw) == 65, 'Wrong password length'
            hash = pw[1:33]
            salt = pw[33:]
            if hashlib.sha256(field.data.encode('utf-8') + salt).digest() != hash:
                raise ValueError("Name or password is wrong")

To make the validation work, we need to propagate dependency injection to the
form. It should be done in our ``form`` decorator:

.. code-block:: python
   :emphasize-lines: 8

    from zorro.di import di

    def form(form_class):
        def decorator(fun):
            @web.decorator(fun)
            def form_processor(self, resolver, meth, *args, **kw):
                form = form_class(resolver.request.legacy_arguments)
                di(self).inject(form)
                if kw and form.validate():
                    return meth(**form.data)
                else:
                    return dict(form=form)
            return form_processor
        return decorator

The ``di`` function extracts dependency injector from the object, so the
``di(self).inject`` mantra is a common pattern to propagate dependencies to
other objects. Note the object that we extract dependency injector from
(``Auth`` instance in this case), doesn't need to have every dependency which
is propagated though it. Actually in most cases ``di(self)`` returns the exact
instance of ``DependencyInjector`` that we created in ``__main__.py``.

Now in any real project it's time to write few unit tests for the password
checking. However, for the sake of keeping tutorial shorter we do not include
unittests here. So let's implement user registration to test our code. First
check login and email for duplicates::

    @has_dependencies
    class RegisterForm(wtforms.Form):
        # ... fields
        redis = dependency(Redis, 'redis')

        def validate_name(self, field):
            uid = self.redis.execute('HGET', 'z:names', field.data)
            if uid is not None:
                raise ValueError("Login exists")

        def validate_email(self, field):
            uid = self.redis.execute('HGET', 'z:names', field.data)
            if uid is not None:
                raise ValueError("This email is already registered")

Next, create a counter ``z:last_uid`` which is incremented on each
registration to make user id. Then carefully update ``z:names``. Here is the
code::


    class Auth(web.Resource):
        redis = dependency(Redis, 'redis')

        # ...

        @template('register.html')
        @form(RegisterForm)
        @web.page
        def register(self, name, email, password, cpassword):
            uid = self.redis.execute("INCR", 'z:last_uid')
            ok = self.redis.execute("HSETNX", 'z:names', name, uid)
            if not ok:
                raise FormError("name", "Login exists")
            ok = self.redis.execute("HSETNX", 'z:names', email, uid)
            if not ok:
                self.redis.execute("HDEL", 'z:names', name)
                raise FormError("email", "This email is already registered")
            salt = os.urandom(32)
            hash = hashlib.sha256(password.encode('utf-8') + salt).digest()
            pw = b'A' + hash + salt
            self.redis.execute('SET', 'z:user:{}:password'.format(uid), pw)
            raise web.CompletionRedirect('/registerok')

This is enough to test whether everything works. The only thing is left is
``FormError``. It's there, because it's possible that between validating the
form and setting ``z:names`` other user with the same name is registered. The
only way to check this is to use ``HSETNX`` instead ``HSET`` and check the
result. Note also, that if email is conflicted we clear the name from the
hash (so somebody can still use the name), but we don't rollback ``uid``. It's
not easy to explain all the complexity of solving race conditions in the
tutorial, but it's clear that spurious increments of ``last_uid`` don't hurt.

The ``FormError`` exception should be catched in our ``form`` decorator:

.. code-block:: python
    :emphasize-lines: 1-5,14,16-18

    class FormError(Exception):

        def __init__(self, field, message):
            self.field = field
            self.message = message

    def form(form_class):
        def decorator(fun):
            @web.decorator(fun)
            def form_processor(self, resolver, meth, *args, **kw):
                form = form_class(resolver.request.legacy_arguments)
                di(self).inject(form)
                if kw and form.validate():
                    try:
                        return meth(**form.data)
                    except FormError as e:
                        form[e.field].errors.append(e.message)
                        return dict(form=form)
                else:
                    return dict(form=form)
            return form_processor
        return decorator

As you can see, we just add a message to the error list for the apropriate
field. If you are curious how to reproduce the race condition, just put
``zorro.sleep(10)`` at the start of the ``register`` method.

Now it's time restart the server and go to ``http://localhost:8000/register``
and ``http://localhost:8000/login`` and verify that everything works.
Remember, you'll still get 404 on successful login/registration, but by
redirect to ``/loginok`` or ``/registerok`` you can understand that everything
works well.

