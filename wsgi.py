from app import app, socketio

if __name__ == "__main__":
    from eventlet import wsgi, listen
    wsgi.server(listen(('0.0.0.0', 7074)), socketio)
