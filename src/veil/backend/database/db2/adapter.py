from __future__ import unicode_literals, print_function, division
import contextlib
import logging
import re
import ibm_db_dbi
import ibm_db
from ibm_db_dbi import OperationalError
from veil.model.collection import *

LOGGER = logging.getLogger(__name__)

class DB2Adapter(object):
    def __init__(self, host, port, database, user, password, schema):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.schema = schema
        self.conn = self._get_conn()

    def _get_conn(self):
        conn = None
        try:
            connection_string = 'DRIVER={IBM DB2 ODBC DRIVER};DATABASE=%s;HOSTNAME=%s;PORT=%s; PROTOCOL=TCPIP;UID=%s;PWD=%s;' % (
                self.database, self.host, self.port, self.user, self.password)
            conn = ibm_db_dbi.connect(connection_string)
            if self.schema:
                with contextlib.closing(NamedParameterCursor(conn.cursor())) as c:
                    c.execute('SET SCHEMA {}'.format(self.schema))
        except:
            LOGGER.critical('Cannot connect to database: %(connection_string)s', {'connection_string': connection_string}, exc_info=1)
            try:
                raise
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except:
                        LOGGER.exception('Cannot close database connection')
        else:
            return conn

    def reconnect_if_broken_per_verification(self, sql='VALUES 1'):
        try:
            with contextlib.closing(self.conn.cursor()) as cur:
                cur.execute(sql)
        except:
            LOGGER.warn('failed in verifying database connection', exc_info=1)
            self._reconnect()

    def reconnect_if_broken_per_exception(self, e):
        if isinstance(e, OperationalError):
            self._reconnect()

    def _reconnect(self):
        LOGGER.info('Reconnect now: %(connection)s', {'connection': self})
        try:
            self.close()
        except:
            LOGGER.exception('Cannot close database connection')
        try:
            self.conn = self._get_conn()
        except:
            LOGGER.exception('failed to reconnect')

    def _reconnect_if_broken_per_lightweight_detection(self):
        """
        lightweight detection is not supported by the driver library ibm_db_dbi
        """
        pass

    @property
    def autocommit(self):
        return ibm_db.autocommit(self.conn.conn_handler)

    @autocommit.setter
    def autocommit(self, on_off):
        self.conn.set_autocommit(on_off)

    def rollback_transaction(self):
        self.conn.rollback()

    def commit_transaction(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def cursor(self, returns_dict_object=True, **kwargs):
        self._reconnect_if_broken_per_lightweight_detection()
        cursor = self.conn.cursor(**kwargs)
        cursor = NamedParameterCursor(cursor)
        if returns_dict_object:
            return ReturningDictObjectCursor(cursor)
        else:
            return cursor

    def __repr__(self):
        return 'DB2 adapter {} with connection parameters {}'.format(
            self.__class__.__name__, dict(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user))


class NamedParameterCursor(object):
    PARAMETER_REGEX = re.compile(r'%\((.*?)\)s')

    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, sql, kwargs=None):
        if not kwargs:
            return self.cursor.execute(sql)
        sql, args = self.translate_parameters(sql, kwargs)
        return self.cursor.execute(sql, args)

    def executemany(self, sql, kwargs=None):
        if not kwargs:
            return self.cursor.executemany(sql)
        sql, args = self.translate_parameters(sql, kwargs)
        return self.cursor.executemany(sql, args)

    def translate_parameters(self, sql, kwargs):
        param_names = []

        def replace_placeholder(match):
            param_name = match.group(1).strip()
            param_names.append(param_name)
            return '?'

        sql = self.PARAMETER_REGEX.sub(replace_placeholder, sql)
        args = tuple(kwargs[param_name] for param_name in param_names)
        return sql, args

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        return getattr(self.cursor, attr)


class ReturningDictObjectCursor(object):
    def __init__(self, cursor):
        self.cursor = cursor

    def fetchone(self):
        return self.to_dict_object(self.cursor.fetchone())

    def fetchmany(self, size=None):
        return [self.to_dict_object(row) for row in self.cursor.fetchmany(size)]

    def fetchall(self):
        return [self.to_dict_object(row) for row in self.cursor.fetchall()]

    def to_dict_object(self, row):
        o = DictObject()
        for i, cell in enumerate(row):
            o[self.get_column_name(i)] = cell
        return o

    def get_column_name(self, i):
        return self.cursor.description[i][0].lower()

    def __iter__(self):
        while 1:
            yield self.to_dict_object(self.cursor.next())

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        return getattr(self.cursor, attr)