import datetime
import logging
import sqlite3
import uuid

log = logging.getLogger()


def timestamp_(tstamp: int) -> str:
    dtm = datetime.datetime.fromtimestamp(tstamp)
    return dtm.isoformat()


def uuid_(identifier: str) -> str:
    return str(uuid.UUID(identifier))


class Database:
    """Main database class."""
    def __init__(self, app):
        self.app = app
        self.conn = sqlite3.connect('rana.db')
        sqlite3.register_adapter(uuid.UUID, str)
        app.conn = self.conn
        self.setup_tables()

    def setup_tables(self):
        """Create basic tables."""
        self.conn.executescript("""
        create table if not exists users (
            id text primary key,
            username text not null,
            password_hash text not null,

            display_name text default null,
            website text default null,

            created_at bigint not null,
            modified_at bigint default null,

            languages_used_public bool default false not null,
            logged_time_public bool default false not null,

            last_heartbeat_at bigint default null,
            last_plugin text default null,
            last_plugin_name text default null,
            last_project text default null
        );

        create table if not exists api_keys (
            user_id bigint primary key references users (id),
            key text not null
        );
        """)

        self.conn.commit()

    async def close(self):
        """Close the database."""
        log.debug('closing db')
        self.conn.commit()

        # weird things happen when i'm unconditionally
        # calling close() when testing.
        if not self.app._testing:
            self.conn.close()

    async def fetch(self, query, *args):
        """Execute a query and return the list of rows."""
        cur = self.conn.cursor()
        cur.execute(query, args)
        return cur.fetchrows()

    async def fetchrow(self, query, args):
        """Execute a query and return a single result row."""
        cur = self.conn.cursor()
        cur.execute(query, args)
        return cur.fetchone()

    async def execute(self, query, args):
        """Execute SQL."""
        self.conn.execute(query, args)
        self.conn.commit()

    async def fetch_user(self, user_id: uuid.UUID) -> dict:
        """Fetch a single user and return the dictionary
        representing the API view of them."""
        row = await self.conn.fetchrow("""
        select
            id, username, display_name, website, created_at, modified_at,
            last_heartbeat_at, last_plugin, last_plugin_name, last_project
        from users where id = ?
        """, (user_id,))

        user = {
            'id': uuid_(row[0]),
            'username': row[1],

            # no "full legal names" here uwuwuwuwu
            # trans rights
            'display_name': row[2],
            'full_name': row[2],

            'website': row[3],
            'created_at': timestamp_(row[4]),
            'modified_at': timestamp_(row[5]),

            'last_heartbeat_at': row[6],
            'last_plugin': row[7],
            'last_plugin_name': row[8],
            'last_project': row[9],

            'logged_time_public': False,
            'languages_used_public': False,

            # i do not store full name or email pls
            'email': 'uwu@uwu.com',
            'email_public': False,

            # TODO: should we put something here?
            'photo': None,

            'is_hireable': False,
            'has_premium_features': False,
            'plan': 'basic',
            'location': 'Canberra, Australia',
            'timezone': 'America/New_York'
        }

        if user['website'] is not None:
            # TODO: use urllib.parse
            user['human_readable_website'] = user['website'].lstrip('https://')

        return user
