#!C:\Users\Evol\Desktop\python\webapp-python
#-*- coding: utf-8 -*-

import aiomysql
import logging
import asyncio

__author__  = 'Lu Sunping'

#记录操作日志
def log(sql, args=()):
    logging.info('SQL: %s' % sql)
	
#创建连接池，避免频繁的打开或关闭数据库连接
async def create_pool(loop, **kw):
	logging.info("create database connecting pool...")
	global __pool
	#调用一个子协程来创建全局连接池，create_pool返回一个Pool实例对象
	__pool = await aiomysql.create_pool(
	#基本的连接属性设置
		host  		= kw.get('host','localhost'),	#数据库服务器位置， 设置为本地
		port 		= kw.get('port',3306),			#MySql端口号
		user 		= kw['user'],					#登陆用户名
		password 	= kw['password'],				#登陆密码
		db 			= kw['db'],						#登陆的数据库
		charset 	= kw.get('cahrset','utf8'),		#设置编码内容
		autocommit 	= kw.get('autocommit',True),	#自动提交， 默认为false
		maxsize 	= kw.get('maxsize',10),			#最大连接池大小
		minsize 	= kw.get('minsize',1),			#最小连接词大小
		loop = loop									#设置消息循环
	)
	
#select语句 返回数据集
async def select(sql, args, size=None):
	#sql : sql语句
	#args: 填入sql的参数，list类型，如['20160110','lixue']
	#size: 取多少行记录
	log(sql, args)
	global __pool
	#从连接池获取一个连接
	async with __pool.get() as conn: #python 3.5 的用法 		//with...as...的作用就是try...exception
		async with conn.cursor(aiomysql.DictCursor) as cur:			#打开一个DictCursor，以dict的形式返回结果坐标
		await cur.execute(sql.replace('?','%s'), args or ())		#sql的占位符是？，而mysql的占位符是%s  替换
		if size:	#如果size不为空，则取一定量的结果集
			rs = await cur.ferchmany(size)
		else:		#默认取全部结果集
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
		
#定义一个对象，将他和数据库user表关联起来  --  ORM
from orm import Model, StringField, InterField
class User(Model):
	__table__ = 'users'				#这些都是类的属性
	id = InterField(primary_key = True)
	name = StringField()
#创建实例
user =  User(id=123, name='Lusunping')
#存入数据库
user.insert()
#查询所有User对象
users = User.findAll()

#该方法用来将其占位符拼接起来成'?,?,?'的形式，num标识参数的个数
def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ', '.join(L)


#定义Field类  父域
def Field(object):
	#字段名称，字段类型，是否为主键
	def __init__(self, name. column_type, primary_key, default):
		self.name = name
		self.column_type = column_type
		self.column_key = column_key
		self.default = default
	#返回类名（域名），字段类型， 字段名
	def __str__(self):
		return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)
		
		
#映射varchar的Field子类StringField
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
		
		
		
#将子类user的映射信息读出来
class ModelMetaclass(type):
	#cls : 当前准备创建的类对象，相当于self
	#name: 类名，比如user继承了Model,当使用该元类创建user时，name=user
	#bases:父类的元组
	#attrs:Model子类的属性和方法的字典，比如user有__table__,id等，就作为attrs的key
	def __new__(cls, name, bases, attrs):
		if name == 'Model':		#排除Model本身
			return type.__new__(cls, name, bases, attrs)
		tableName = attrs.get('__table__', None) or name	#获取table的名称，若没有定义__table__属性，将类名作为表名
		logging.info('found model: %s (table: %s)' % (name, tableName))
		#获取所有的Field和主键名
		mappings = dict()	#用字典来存储类属性与数据库表的列的映射关系
		fields = []			#用于保存除主键以外的属性
		primary_key = None	#用于保存主键
		#k是主键名，v是定义域。如name=StringField(ddl = "varchar50")==>k=name,v=StringField(ddl="varchar50")
		for k, v in attrs.items():
			if isintance(v, field):
				logging.info(' found mapping: %s' % (k, v))
				mappings[k] = v
				if v.primary_key:
					#找到主键
					if primaryKey:	#如果主键已存在，报错
						raise RuntimeError('Duplicate primary key for field: %s' % k)
					primaryKey = k
				else:
					fields.appenf(k)
			if not primartKey:
				raise RuntimeError('Primary key not found')
			for k in mapping.keys():
				attrs.pop(k)			#从类属性中删除已经加入了映射字典的键，以免重名
			#将非主键的属性变形，放入escaped_fields中，方便增删查改语句的书写
			escaped_fields = list(map(lambda f:'`%s`' % f, fields))
			attrs['__mappings__'] 	= mappings  #保持属性和列的映射关系
			attrs['__table__']		= tableName 
			attrs['__primary_key__']= primaryKey 
			attrs['__fields__']		= fields 
			attrs['__select__']		= 'select `%s`, %s from `%s`' % (primaryKey,','.join(escaped_fields), tableName) 
			attrs['__insert__']		= 'insert into `%s` (%s,`%s`) values (%s)' % (tableName,','.join(escaped_fields),primartKey,create_args_string(len(escaped_fields)+1))  
			attrs['__update__']		= 'update `%s` set %s where `%s`=?' % (tableName,',',join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)),primartKey)
			attrs['__delete__']		= 'delete from `%s` where `%s`=?' % (tableName, primartKey)
			return type.__name__(cls, name, bases, attrs)
			
	
#定义Model，所有ORM映射的基类 继承dict，通过ModelMetaclass元类来构造类
class Model(dict, metaclass=ModelMetaclass):
	
	#初始化函数，调用父类dict的方法
	def __init__(self, **kw):
		super(Model, self).__init__(**kw)
	
	#增加__getattr__方法，可通过a.b的方式获取属性，使获取属性更方便，
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
			
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	

		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		