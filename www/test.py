import orm
import asyncio
import sys
import aiomysql
from model import User, Blog, Comment

async def test(loop):
	await orm.create_pool(loop = loop, host = 'localhost', port = 3306, user = 'www-data', password = 'www-data', db = 'awesome')
	u = User(name = 'test01', email = 'l.sunping@gmail.com', password = 'test',admin = True, passwd = 'test', image = 'about:blank')
	await u.save()
	
if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	loop.run_until_complete(test(loop))
	loop.close()
	if loop.is_closed():
		sys.exit(0);