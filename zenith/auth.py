import wtforms
from wtforms import val
from zorro.web import (Resource,
    public_with_simpleform,
    )

from util import template, TemplateMixin


class LoginForm(wtforms.Form):
    login = wtforms.TextField('Name or Email',
        validators=[val.Required()])
    password = wtforms.PasswordField('Password',
        validators=[val.Required()])


class Register(wtforms.Form):
    name = wtforms.TextField('Name',
        validators=[val.Required(), val.Length(min=3, max=24)])
    email = wtforms.TextField('E-mail',
        validators=[val.Required(), val.Email()])
    password = wtforms.PasswordField('Password',
        validators=[val.Required()])
    cpassword = wtforms.PasswordField('Confirm Password',
        validators=[val.Required()])


class Auth(Resource, TemplateMixin):

    @template('login.html')
    @public_with_simpleform(LoginForm)
    def login(self, login, password):
        raise TemporaryRedirect('/home', set_cookie={'':''})

    @template('register.html')
    @public_with_form(RegisterForm)
    def register(self):
        pass
