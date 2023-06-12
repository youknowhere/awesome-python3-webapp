__author__ = 'prince Fan'

from typing import Any
import logging; logging.basicConfig(level = logging.INFO)
import aiomysql

def log(sql, arg = ()):
    logging.info('SQL: %s' % sql)

async def create_pool(loop, **kw):
    logging.info('create database connection pool...')
    global __pool
    __pool = aiomysql.create_pool(
        host = kw.get('host', 'localhost'),
        port = kw.get('port', 3306),
        user = kw['user'],
        password = kw['password'],
        db = kw['db'],
        charset = kw.get('charset', 'utf-8'),
        autocommit = kw.get('autocommit', True),
        maxsize = kw.get('maxsize', 10),
        minsize = kw.get('minsize', 1),
        loop = loop
    )
    
async def select(sql, args, size = None):
    log(sql, args)
    global __pool
    async with __pool.get() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.excute(sql.replace('?', '%s'), args or ())
            if size:
                rs = await cur.fetchmany(size)
            else:
                rs = await cur.fetchall()
        logging.info('rows returned: %s' % len(rs))
        return rs

async def execute(sql, args, autocommit = True):
    log(sql)
    async with __pool.get() as conn:
        if not autocommit:
            conn.begin()
        try:
            async with conn.cursor() as cur:
                await cur.exeute(sql.replace('?', '%s'), args)
                affected = cur.rowcount
            if not autocommit:
                await conn.commit()
        except BaseException as e:
            if not autocommit:
                conn.rollback()
            raise
        return affected
    
class Field(object):
    """表中的列对象"""
    def __init__(self, name, ddl, primary_key, default):
        self.name = name
        self.column_type = ddl
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '%s, %s:%s' % (self.__class__.__name__, self.column_type, self.name)

class StringField(Field):
    """字符串列对象"""
    def __init__(self, name = None, ddl = 'varchar(100)', primary_key = False, default = None):
        super().__init__(name, ddl, primary_key, default)

class BooleanField(Field):
    def __init__(self, name = None, default = False):
        super().__init__(name, 'boolean', False, default)

class IntegerField(Field):
    """字符串列对象"""
    def __init__(self, name = None, primary_key = False, default = 0):
        super().__init__(name, 'bigint', primary_key, default)

class FloatField(Field):
    def __init__(self, name = None, primary_key = False, default = 0.0):
        super().__init__(name, 'real', primary_key, default)

class TextField(Field):
    def __init__(self, name = None, primary_key = False, default = None):
        super().__init__(name, 'text', False, default)


class ModelMetaClass(type):
    """定制化创建Model子类"""
    def __new__(cls, name, bases, attrs):
        # 排除类Model本身
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        # 获取tablename
        tableName = attrs.get('__table__', None) or name
        logging.info('found model: %s (table: %s)' % (name, tableName))
        # 获取所有的Field和主键名:
        mappings = []
        fields = []
        primary_key = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('    found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    if primary_key:
                        raise RuntimeError('Duplicated primary key for field: %s' % k)
                    primary_key = v.primary_key
                else:
                    fields.append(k)
        if not primary_key:
            raise RuntimeError('Primary key not found.')
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda f: '`%s`'%f, fields))
        attrs['__mappings__'] = mappings
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primary_key
        attrs['__fields__'] = fields 
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primary_key, ','.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ','.join(escaped_fields), 
                                                                           primary_key, create_args_string(len(escaped_fields)+1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ','.join(map(lambda f: '`%s`=?' % mappings.get(f).name or f, 
                                                                                           fields)), primary_key)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primary_key)
        return type.__new__(cls, name, bases, attrs)

class Model(dict, metaclass = ModelMetaClass):

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)
    
    def __getattr__(self, key):
        return self[key]
    
    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)
    
    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            value = field.default() if callable(field.default) else field.default
            logging.info('using default value for %s: %s' % (key, str(value)))
            setattr(self, key, value)
        return value
    
    @classmethod
    async def find(cls, pk):
        'find object by primary key'
        rs = await select(cls.__select__, [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])
    
    @classmethod
    async def find(cls, pk):
        'find object by primary key'
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    @classmethod
    async def findAll(cls, where = None, args = None, **kw):
        ' find object by where clause. '
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []
        orderBy = kw.get('orderBy', None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple):
                sql.append('?,?')
                sql.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await select(' '.join(sql), args)
        return [cls(**r) for r in rs]
    
    @classmethod
    async def findNumber(cls, selectField, where = None, args = None):
        ' find number by select and where. '
        sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']

    async def update(self):
        'update table'
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.info('failed to update by primary key: affected rows: %s' % rows)

    async def remove(self):
        'delete a object of table'
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.info('failed to remove by primary key: affected rows: %s' % rows)

    async def save(self):
        args = list(map(lambda f: self.getValueOrDefault(f), self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.info('failed to insert record: affected rows: %s' % rows)
    
def create_args_string(lens):
    return ','.join('?' * lens)
