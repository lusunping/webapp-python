#!C:\Users\Evol\Desktop\python\webapp-python
#-*- coding: utf-8 -*-

__author__  = 'Lu Sunping'

'''
async web application
'''

#由于Web app是建立在asyncio的基础上的，所以用aiohttp写一个基本的app.py

import logging; logging.basicConfig(level=logging.INFO)
import asyncio, os, json, time
from datetime import datetime
from aiohttp import web

def index(request):
	return web.Response(body=b'<h1>Awesome</h1>')
	
def index_home(request):
	return web.Response(body=b'<h1>Home</h1>')
	   
@asyncio.coroutine
def init(loop):
	app = web.Application(loop = loop)
	app.router.add_route('GET','/',index)
	app.router.add_route('GET','/home',index_home)
	srv = yield from loop.create_server(app.make_handler(),'127.0.0.1',9000)
	logging.info("Server started at http://127.0.0.1...")
	return srv
	
loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
	