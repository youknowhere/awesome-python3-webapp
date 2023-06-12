from models import User, Blog, Comment
import orm
import asyncio

async def add_users(loop):
    await orm.create_pool(loop = loop, host = '127.0.0.1', port = 3306, user = 'root', password = 'fxyjiayou', db = 'awesome')

    u_a = User(name = 'Administrator', email = 'admin@example.com', passwd = '000000', image = 'about:blank')
    u_b = User(name = 'Michael', email = 'Michael@example.com', passwd = '000000', image = 'about:blank')
    u_c = User(name = 'Test', email = 'Test@example.com', passwd = '000000', image = 'about:blank')
    await u_a.save()
    await u_b.save()
    await u_c.save()

loop = asyncio.get_event_loop()
loop.run_until_complete(add_users(loop))




