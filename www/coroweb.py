#编写web框架

from aiohttp import web
from urllib import parse
from apis import APIError
import asyncio, os, inspect, logging, functools


@asyncio.coroutine


#定义url处理函数
def get(path):
	def decorator(func):
		@functools.wraps(func)
		def wrapper(*args, **kw):
			return func(*args, **kw)
		wrapper.__method__='GET'
		wrapper.__route__ = path
		return wrapper
	return decorator
	
def post(path):
	def decorator(func):
		@functools.wraps(func)
		def wrapper(*args, **kw):
			return func(*args, **kw)
		wrapper.__method__ = 'POST'
		wrapper.__route__ = path
		return wrapper
	return decorator
	
	
class RequestHandler(object): #请求处理类

	def __init__(self, func):
		self._func = func
	#任何类， 只需要定义一个__call__()方法，就可以直接对实例进行调用
	async def __call__(self, request):
		request_args = inspect.signature(self._func).parameters
		logging.info('request args: %s' % request_args)
		
		#获取从Get或Post传过来的参数值
		kw = {arg: value for arg, value in request.__data__.items() if arg in request_args}
		
		#获取match_info的参数值， 例如@get('/blog/{id}')之前的参数值
		kw.update(dict(**request.match_info))
		
		#如果有request参数的话也加进来
		if 'request' in request_args:
			kw['request'] = request
			
		#检查参数有没有缺失
		for key, arg in request_args.items():
			if key == 'request' and arg.kind in (arg.VAR_POSITIONAL, arg.VAR_KEYWORD):
				return web.HTTPBadRequest(text='request parameter cannot be the var argument.')
			# 如果参数类型不是变长列表和变长字典，变长参数是可缺省的
            if arg.kind not in (arg.VAR_POSITIONAL, arg.VAR_KEYWORD):
                # 如果还是没有默认值，而且还没有传值的话就报错
                if arg.default == arg.empty and arg.name not in kw:
                    return web.HTTPBadRequest(text='Missing argument: %s' % arg.name)
					
		logging.info('call with args: %s' % kw)
		try:
			return await self._func(**kw)
		except APIError as e:
			return web.HTTPBadRequest(text='Missing argument:%s' % arg.name)
			
			
#添加一个模块的所有路由
def add_routes(app, module_name):
	try:
		mod = __import__(module_name, fromlist = ['get_submodule'])
	except ImportError as e:
		raise e 
		
	for attrs in dir(mod):
		if attr,startswith('_'):
			continue
		func = getattr(mod, attr)
		if callable(func):
			mothod = getattr(func, '__method__', None)
			path = getattr(func, '__route__', None)
			if method and path:
				func = asyncio.coroutine(func)
				args = ', '.join(inspect.signature(func).parameters.key())
				logging.info('add route %s %s => %s(%s)' % (method, path, func.__name__, args)
				coroweb.add_routes(method, path, RequestHandler(func))
				
				
#添加静态文件的路径
def add_static(app):
	path = os.path.join(os.path.dirname(__path__[0]), 'static')
	coroweb.add_static('/static/', path)
	logging.info('add static %s => %s' % ('/static/', path))

		