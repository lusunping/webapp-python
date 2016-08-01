#!C:\Users\Evol\Desktop\python\webapp-python
#-*- coding: utf-8 -*-

import aiomysql
import logging
import asyncio

__author__  = 'Lu Sunping'

#��¼������־
def log(sql, args=()):
    logging.info('SQL: %s' % sql)
	
#�������ӳأ�����Ƶ���Ĵ򿪻�ر����ݿ�����
async def create_pool(loop, **kw):
	logging.info("create database connecting pool...")
	global __pool
	#����һ����Э��������ȫ�����ӳأ�create_pool����һ��Poolʵ������
	__pool = await aiomysql.create_pool(
	#������������������
		host  		= kw.get('host','localhost'),	#���ݿ������λ�ã� ����Ϊ����
		port 		= kw.get('port',3306),			#MySql�˿ں�
		user 		= kw['user'],					#��½�û���
		password 	= kw['password'],				#��½����
		db 			= kw['db'],						#��½�����ݿ�
		charset 	= kw.get('cahrset','utf8'),		#���ñ�������
		autocommit 	= kw.get('autocommit',True),	#�Զ��ύ�� Ĭ��Ϊfalse
		maxsize 	= kw.get('maxsize',10),			#������ӳش�С
		minsize 	= kw.get('minsize',1),			#��С���Ӵʴ�С
		loop = loop									#������Ϣѭ��
	)
	
#select��� �������ݼ�
async def select(sql, args, size=None):
	#sql : sql���
	#args: ����sql�Ĳ�����list���ͣ���['20160110','lixue']
	#size: ȡ�����м�¼
	log(sql, args)
	global __pool
	#�����ӳػ�ȡһ������
	async with __pool.get() as conn: #python 3.5 ���÷� 		//with...as...�����þ���try...exception
		async with conn.cursor(aiomysql.DictCursor) as cur:			#��һ��DictCursor����dict����ʽ���ؽ������
		await cur.execute(sql.replace('?','%s'), args or ())		#sql��ռλ���ǣ�����mysql��ռλ����%s  �滻
		if size:	#���size��Ϊ�գ���ȡһ�����Ľ����
			rs = await cur.ferchmany(size)
		else:		#Ĭ��ȡȫ�������
			rs = await cur.fetchall()
		yield from cur.close()
		logging.info('rows return: %s' % len(rs))
		return rs
		
#insert,update,delete ---> excute
async def excute(sql, args, autocommit=True):
	log(sql)
	async with __pool.get() as conn:
		if not autocommit:
			await conn.begin()
		try:
			async with conn.cursor(aiomysql.DictCursor) as cur: 
			await cur.excute(sql.replace('?','%s'), args)
			affected = cur.rowcount
			if not autocommit:
				await conn.commit()
		except BaseException as e:
			if not autocommit:
				await conn.rollback()
			raise
		return affected
		
#����һ�����󣬽��������ݿ�user���������  --  ORM
from orm import Model, StringField, InterField
class User(Model):
	__table__ = 'users'				#��Щ�����������
	id = InterField(primary_key = True)
	name = StringField()
#����ʵ��
user =  User(id=123, name='Lusunping')
#�������ݿ�
user.insert()
#��ѯ����User����
users = User.findAll()

#�÷�����������ռλ��ƴ��������'?,?,?'����ʽ��num��ʶ�����ĸ���
def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ', '.join(L)


#����Field��  ����
def Field(object):
	#�ֶ����ƣ��ֶ����ͣ��Ƿ�Ϊ����
	def __init__(self, name. column_type, primary_key, default):
		self.name = name
		self.column_type = column_type
		self.column_key = column_key
		self.default = default
	#�������������������ֶ����ͣ� �ֶ���
	def __str__(self):
		return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)
		
		
#ӳ��varchar��Field����StringField
def StringField(Field):

	def __init__(self, name = None, primary_key=false, default=None, ddl='varchar(100)'):
		super().__init__(name, ddl, primary_key, default)
		
class BooleanField(Field):

    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)

class IntegerField(Field):

    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)

class FloatField(Field):

    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)

class TextField(Field):

    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)
		
		
		
#������user��ӳ����Ϣ������
class ModelMetaclass(type):
	#cls : ��ǰ׼��������������൱��self
	#name: ����������user�̳���Model,��ʹ�ø�Ԫ�ഴ��userʱ��name=user
	#bases:�����Ԫ��
	#attrs:Model��������Ժͷ������ֵ䣬����user��__table__,id�ȣ�����Ϊattrs��key
	def __new__(cls, name, bases, attrs):
		if name == 'Model':		#�ų�Model����
			return type.__new__(cls, name, bases, attrs)
		tableName = attrs.get('__table__', None) or name	#��ȡtable�����ƣ���û�ж���__table__���ԣ���������Ϊ����
		logging.info('found model: %s (table: %s)' % (name, tableName))
		#��ȡ���е�Field��������
		mappings = dict()	#���ֵ����洢�����������ݿ����е�ӳ���ϵ
		fields = []			#���ڱ�����������������
		primary_key = None	#���ڱ�������
		#k����������v�Ƕ�������name=StringField(ddl = "varchar50")==>k=name,v=StringField(ddl="varchar50")
		for k, v in attrs.items():
			if isintance(v, field):
				logging.info(' found mapping: %s' % (k, v))
				mappings[k] = v
				if v.primary_key:
					#�ҵ�����
					if primaryKey:	#��������Ѵ��ڣ�����
						raise RuntimeError('Duplicate primary key for field: %s' % k)
					primaryKey = k
				else:
					fields.appenf(k)
			if not primartKey:
				raise RuntimeError('Primary key not found')
			for k in mapping.keys():
				attrs.pop(k)			#����������ɾ���Ѿ�������ӳ���ֵ�ļ�����������
			#�������������Ա��Σ�����escaped_fields�У�������ɾ���������д
			escaped_fields = list(map(lambda f:'`%s`' % f, fields))
			attrs['__mappings__'] 	= mappings  #�������Ժ��е�ӳ���ϵ
			attrs['__table__']		= tableName 
			attrs['__primary_key__']= primaryKey 
			attrs['__fields__']		= fields 
			attrs['__select__']		= 'select `%s`, %s from `%s`' % (primaryKey,','.join(escaped_fields), tableName) 
			attrs['__insert__']		= 'insert into `%s` (%s,`%s`) values (%s)' % (tableName,','.join(escaped_fields),primartKey,create_args_string(len(escaped_fields)+1))  
			attrs['__update__']		= 'update `%s` set %s where `%s`=?' % (tableName,',',join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)),primartKey)
			attrs['__delete__']		= 'delete from `%s` where `%s`=?' % (tableName, primartKey)
			return type.__name__(cls, name, bases, attrs)
			
	
#����Model������ORMӳ��Ļ��� �̳�dict��ͨ��ModelMetaclassԪ����������
class Model(dict, metaclass=ModelMetaclass):
	
	#��ʼ�����������ø���dict�ķ���
	def __init__(self, **kw):
		super(Model, self).__init__(**kw)
	
	#����__getattr__��������ͨ��a.b�ķ�ʽ��ȡ���ԣ�ʹ��ȡ���Ը����㣬
	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Model' object has no attribute '%s'" %key)
			
	def __setattr__(self, key, value):
		self[key] = value
		
	def getValue(self, key):
		return getattr(self, key, None)
		
	def getValueOrDefault(self, key):
		value =getattr(self, key, None)
		if value is None:
			field = self.__mapping__[key]
			if field default is not None:
				value = field.default() if callable(field.default) else field.default
				logging.debug('using default value for %s:%s' % (key, str(value)))
				setattr(self, key, value)
			return value
	
	@classmethod
    async def findAll(cls, where=None, args=None, **kw):
        ' find objects by where clause. '
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
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await select(' '.join(sql), args)
        return [cls(**r) for r in rs]

    @classmethod
    async def findNumber(cls, selectField, where=None, args=None):
        ' find number by select and where. '
        sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']

    @classmethod
    async def find(cls, pk):
        ' find object by primary key. '
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warn('failed to insert record: affected rows: %s' % rows)

    async def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warn('failed to update by primary key: affected rows: %s' % rows)

    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warn('failed to remove by primary key: affected rows: %s' % rows)
			
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	

		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		