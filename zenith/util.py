from zorro.web import decorate

def template(name):
    def decorator(fun):
        @decorates(fun)
        def wrapper(self, *args, **kw):
            result = fun(self, *args, **kw)
            assert isinstance(result, dict), \
                "Function {} must return dict".format(fun)
            return ('200 OK',
                    'Content-Type\0text/html; charset=utf-8\0',
                    self.jinja.get_template(name).render(result))
        return wrapper
    return decorator
