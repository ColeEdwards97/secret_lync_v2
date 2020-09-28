from flask import Flask, Response, make_response, request, redirect, render_template, stream_with_context, url_for
import time
import queue
from random import randint

# TODO:
# CHAT SIZE MANAGEMENT

HOST = '127.0.0.1'
#HOST = '0.0.0.0'
PORT = '5000'
KEY = str(input('enter a secret password: '))
USERS = {}


app = Flask(__name__)
q = queue.Queue()



def stream():
	while True:
		message = q.get(block=True, timeout=None)
		yield message

def validate_key(in_key):
	return (in_key == KEY) and (in_key != None)

def validate_name(in_name):
	return (in_name != "") and (in_name != None)
	
def register_user(ip, name):
	id = ip + '_' + ''.join(["{}".format(randint(0, 9)) for num in range(0, 4)])
	USERS[id] = name	
	return id

def stream_template(template_name, **context):
	app.update_template_context(context)
	t = app.jinja_env.get_template(template_name)
	rv = t.stream(context)
	rv.disable_buffering()
	return rv
	
	

@app.route('/chat', methods=['POST', 'GET'])
def chat():
	
	id = request.cookies.get('login')
	
	# redirect if user hasn't logged in or isnt registered
	if request.method == 'GET':
		if not request.cookies.get('login'):
			return redirect(url_for('login'))
		
		if id not in USERS:
			resp = redirect(url_for('login'))
			resp.set_cookie('login', '', expires=0)
			return resp

	# send a message
	if request.method == 'POST':
		#if 'send' in request.form:
		message = str(request.form['message'])
		message = "{}: {}".format(USERS[id], message)
		for user in USERS.keys():
			q.put(message)
		return message
		
	return Response(stream_with_context(stream_template('chat.html', stream=stream())))


@app.route('/login', methods=['POST', 'GET'])
def login():

	def successful_login(id):
		resp = redirect(url_for('chat'))
		resp.set_cookie('login', id) 
		return resp

	ip = request.environ['REMOTE_ADDR']
	
	# check for cookie
	# redirect if exists
	if request.method == 'GET':
		if request.cookies.get('login'):
			return redirect(url_for('chat'))
	
	# validate key
	# validate username
	# register username
	# set login cookie
	if request.method == 'POST':
		in_key = request.form['key']
		in_name = request.form['username']		
		if validate_key(in_key):
			if validate_name(in_name):
				id = register_user(ip, in_name)
				return successful_login(id)
			else:
				return render_template('login.html', msg='invalid username!')
		else:
			return render_template('login.html', msg='invalid key! youre probably not supposed to be here...')
			
	# default fallthrough action
	return render_template('login.html')	
	
	
	
	
if __name__ == "__main__":
	try: app.run(host=HOST, port=PORT, threaded=True)
	except KeyboardInterrupt:
		pass