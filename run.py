""" run.py - Run the Flask app """
from allerviz import app
# from livereload import Server


if __name__ == '__main__':
    # Tells Flask to run, accessible from the specified host/port pair. Note
    # that the routes are loaded because of the import above.
    app.run(host='127.0.0.1', port=3001, debug=True)
    # app.debug = True
    # # app.run(host='127.0.0.1', port=3001)

    # server = Server(app.wsgi_app)
    # # livereload on another port
    # server.serve(liveport=35729)

    # use custom host and port
    # server.serve(port=3001, host='localhost')
    # server.serve()
