(function(window) {

    var pager = document.getElementById('pager');
    var status_div = document.getElementById('connection');


    status_div.textContent = 'connecting...'
    var conn = new WebSocket('ws://localhost:8000/ws');
    var handlers = {};
    conn.onopen = function() {
        status_div.textContent = 'connected';
        send_message('auth.hello', {}, extract_cookie('sid'));
    }
    conn.onmessage = function(ev) {
        var json = JSON.parse(ev.data)
        var cmd = handlers[json.shift()];
        if(cmd) {
            cmd.apply(this, json);
        }
    }
    function send_message() {
        var data = Array.prototype.slice.call(arguments)
        conn.send(JSON.stringify(data));
    }


    var pager_btn = document.getElementById('pager_send')
    pager_btn.addEventListener('click', function() {
        var msg = prompt('Enter a message');
        if(msg) {
            send_message('pager.send', {}, msg);
        }
    });
    handlers['pager.message'] = function(username, msg) {
        pager.textContent = username + ': ' + msg;
    }

    function extract_cookie(name) {
        var lst = document.cookie.split(';');
        for(var i = 0, ni = lst.length; i < ni; ++i) {
            var pair = lst[i].split('=', 2);
            if(pair[0] == name)
                return pair[1];
        }
        return null;
    }

})(this);
