import functools
import xmlrpc.client
HOST = 'localhost'
PORT = 8069
DB = 'DB1'
USER =  'admin'
PASS = 'admin'
ROOT = 'http://%s:%d/xmlrpc/' % (HOST,PORT)

# 1. Login
uid = xmlrpc.client.ServerProxy(ROOT + 'common').login(DB,USER,PASS)
print("Logged in as %s (uid:%d)" % (USER,uid))

call = functools.partial(
    xmlrpc.client.ServerProxy(ROOT + 'object').execute,
    DB, uid, PASS)

# 2. Read the sessions
sessions = call('oa.session','search_read', [], ['name','seats','course_id'])
for session in sessions:
    print("Session %s (%s seats)  for %s" % (session['name'], session['seats'],session['course_id']))

# 3.create a new sessioncous
#session_id = call('openacademy.session', 'create', {
#    'name' : 'My session',
#    'course_id' : 335,
#})


#4.# 3.create a new session for the "Functional" Course
course_id = call('product.template', 'search', [('name','ilike','Dragon Functional')])[0]
print("check " )
print(course_id)
session_id = call('oa.session', 'create', { #will work only for Maesters and Achmaesters
    'name' : 'My session4',
    'course_id' : course_id,
})

#5
print("Final output")
sessions = call('oa.session','search_read', [], ['name','seats','course_id'])
for session in sessions:
    #print("Session %s (%s seats)" % (session['name'], session['seats']))
    print("Session %s (%s seats)  for %s" % (session['name'], session['seats'],session['course_id']))
