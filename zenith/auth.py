import jinja2
import wtforms
import hashlib
import os
from wtforms import validators as val
from zorro import web
from zorro.di import has_dependencies, dependency
from zorro.redis import Redis

from .util import form, template


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


@has_dependencies
class RegisterForm(wtforms.Form):
    name = wtforms.TextField('Name',
        validators=[val.Required(), val.Length(min=3, max=24)])
    email = wtforms.TextField('E-mail',
        validators=[val.Required(), val.Email()])
    password = wtforms.PasswordField('Password',
        validators=[val.Required()])
    cpassword = wtforms.PasswordField('Confirm Password',
        validators=[val.Required(), val.EqualTo('password')])

    redis = dependency(Redis, 'redis')

    def validate_name(self, field):
        uid = self.redis.execute('HGET', 'z:names', field.data)
        if uid is not None:
            raise ValueError("Login exists")

    def validate_email(self, field):
        uid = self.redis.execute('HGET', 'z:names', field.data)
        if uid is not None:
            raise ValueError("This email is already registered")


@has_dependencies
class Auth(web.Resource):

    jinja = dependency(jinja2.Environment, 'jinja')
    redis = dependency(Redis, 'redis')

    @template('login.html')
    @form(LoginForm)
    @web.page
    def login(self, login, password):
        raise web.CompletionRedirect('/loginok')

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
