import jinja2
import wtforms
from wtforms import validators as val
from zorro import web
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
        validators=[val.Required()])


@has_dependencies
class Auth(web.Resource):

    jinja = dependency(jinja2.Environment, 'jinja')

    @template('login.html')
    @form(LoginForm)
    @web.page
    def login(self, login, password):
        raise web.CompletionRedirect('/loginok')

    @template('register.html')
    @form(RegisterForm)
    @web.page
    def register(self, name, email, password, cpassword):
        return web.CompletionRedirect('/registerok')
