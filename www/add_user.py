from models import User, Blog, Comment
import orm
import asyncio
import hashlib
from handlers import next_id
async def add_users(loop):
    email = 'admin@qq.com'
    passwd = hashlib.sha1('admin@qq.com:000000'.encode('utf-8')).hexdigest()
    uid = next_id()
    sha1_passwd = '%s:%s' % (uid, passwd)
    await orm.create_pool(loop = loop, host = '127.0.0.1', port = 3306, user = 'root', password = 'fxyjiayou', db = 'awesome')
    passwd1 = hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest()
    u_a = User(id = uid, name = 'Admin', email = 'admin@qq.com', passwd = passwd1, image = 'about:blank', admin=True)
    await u_a.save()

loop = asyncio.get_event_loop()
loop.run_until_complete(add_users(loop))




