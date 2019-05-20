import logging

from quart import Quart, jsonify

from rana.blueprints import auth, users, heartbeats, index
from rana.errors import RanaError
from rana.database import Database

log = logging.getLogger(__name__)


def make_app():
    app = Quart(__name__)
    app._testing = False
    logging.basicConfig(level=logging.DEBUG)
    return app


def setup_blueprints(app_):
    """Setup blueprints for the app object."""
    bps = {
        auth: -1,
        index: -1,

        users: '/users',
        heartbeats: '/users',
    }

    for bpr, suffix in bps.items():
        url_prefix = f'/api/v1{suffix or ""}'

        if suffix == -1:
            url_prefix = ''

        app_.register_blueprint(bpr, url_prefix=url_prefix)


app = make_app()
setup_blueprints(app)


@app.before_serving
async def app_before_serving():
    log.info('starting db')
    app.db = Database(app)


@app.after_serving
async def app_after_serving():
    log.info('closing db')
    await app.db.close()


@app.errorhandler(RanaError)
async def rana_error_handler(exception: RanaError):
    """Exception handler to convert RanaError exceptions into the proper
    JSON body + status code."""
    return jsonify({
        'error': exception.message
    }), exception.status_code


@app.errorhandler(500)
async def rana_generic_err(err):
    log.exception('Error on request: %r', err)
    return jsonify({
        'error': repr(err),
    }), 500
