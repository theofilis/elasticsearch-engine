from django.core.exceptions import ImproperlyConfigured

from .creation import DatabaseCreation
from .serializer import Decoder, Encoder
from pyes import ES

from djangotoolbox.db.base import NonrelDatabaseFeatures, \
    NonrelDatabaseWrapper, NonrelDatabaseClient, \
    NonrelDatabaseValidation, NonrelDatabaseIntrospection

from djangotoolbox.db.base import NonrelDatabaseOperations


class DatabaseOperations(NonrelDatabaseOperations):
    def no_limit_value(self):
        pass

    def datetime_extract_sql(self, lookup_type, field_name, tzname):
        pass

    def date_extract_sql(self, lookup_type, field_name):
        pass

    def date_trunc_sql(self, lookup_type, field_name):
        pass

    def regex_lookup(self, lookup_type):
        pass

    def datetime_trunc_sql(self, lookup_type, field_name, tzname):
        pass

    def date_interval_sql(self, sql, connector, timedelta):
        pass

    def fulltext_search_sql(self, field_name):
        pass

    compiler_module = __name__.rsplit('.', 1)[0] + '.compiler'

    def sql_flush(self, style, tables, sequence_list):
        for table in tables:
            self.connection.db_connection.delete_mapping(self.connection.db_name, table)
        return []

    def check_aggregate_support(self, aggregate):
        """
        This function is meant to raise exception if backend does
        not support aggregation.
        """
        pass


class DatabaseFeatures(NonrelDatabaseFeatures):
    string_based_auto_field = True


class DatabaseClient(NonrelDatabaseClient):
    def runshell(self):
        pass


class DatabaseValidation(NonrelDatabaseValidation):
    pass


class DatabaseIntrospection(NonrelDatabaseIntrospection):
    def get_table_list(self, cursor):
        pass

    def get_indexes(self, cursor, table_name):
        pass

    def get_key_columns(self, cursor, table_name):
        pass

    def table_names(self):
        """
        Show defined models
        """
        # TODO: get indices
        return []

    def sequence_list(self):
        # TODO: check if it's necessary to implement that
        pass


class DatabaseWrapper(NonrelDatabaseWrapper):
    def _start_transaction_under_autocommit(self):
        pass

    def create_cursor(self):
        pass

    def is_usable(self):
        pass

    def _cursor(self):
        self._ensure_is_connected()
        return self._connection

    def __init__(self, *args, **kwds):
        super(DatabaseWrapper, self).__init__(*args, **kwds)
        self.features = DatabaseFeatures(self)
        self.ops = DatabaseOperations(self)
        self.client = DatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.validation = DatabaseValidation(self)
        self.introspection = DatabaseIntrospection(self)
        self._is_connected = False

    @property
    def db_connection(self):
        self._ensure_is_connected()
        return self._db_connection

    def _ensure_is_connected(self):
        if not self._is_connected:
            try:
                port = int(self.settings_dict['PORT'])
            except ValueError:
                raise ImproperlyConfigured("PORT must be an integer")

            self.db_name = self.settings_dict['NAME']

            self._connection = ES("%s:%s" % (self.settings_dict['HOST'], port),
                                  decoder=Decoder,
                                  encoder=Encoder,
                                  autorefresh=True,
                                  default_indices=[self.db_name])

            self._db_connection = self._connection
            # auto index creation: check if to remove
            try:
                self._connection.create_index(self.db_name)
            except:
                pass
            # We're done!
            self._is_connected = True