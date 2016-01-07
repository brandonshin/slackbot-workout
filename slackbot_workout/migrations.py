from loggers import PostgresConnector

class UsernameToUserIdMigration(PostgresConnector):
    def __init__(self, dbname, tablename, api, **kwargs):
        super(UsernameToUserIdMigration, self).__init__()
        self.debug = 'debug' in kwargs and kwargs['debug'] == True
        self.kwargs = kwargs
        self.kwargs.update({'dbname': dbname})
        self.tablename = tablename
        self.user_cache = {}

        self.initialize_user_cache(api)

    def initialize_user_cache(self, api):
        members = api.users.list().body['members']
        for member in members:
            self.user_cache[member['name']] = member['id']

    def migrate(self):
        def migrate_command(cursor):
            cursor.execute("SELECT DISTINCT username FROM {}".format(self.tablename))
            rows = cursor.fetchall()
            for row in rows:
                username = row[0][1:]
                user_id = self.user_cache[username] if username in self.user_cache else 'none'
                cursor.execute("""
                    UPDATE {}
                    SET username = %s WHERE username = %s
                """.format(self.tablename), (user_id, "@" + username))
        self.with_connection(migrate_command)


