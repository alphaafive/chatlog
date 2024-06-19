from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, send
from models import User, ChatRoom, session as db_session
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

colors = ["red", "green", "blue", "purple", "orange"]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db_session.query(User).filter_by(username=username).first()
        if user:
            if user.check_password(password):
                session['username'] = username
                session['color'] = random.choice(colors)
                return redirect(url_for('chat'))
            else:
                return "Invalid password"
        else:
            new_user = User(username=username)
            new_user.set_password(password)
            db_session.add(new_user)
            db_session.commit()
            session['username'] = username
            session['color'] = random.choice(colors)
            return redirect(url_for('chat'))
    return render_template('index.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        room_name = request.form['room_name']
        room = db_session.query(ChatRoom).filter_by(name=room_name).first()
        if not room:
            room = ChatRoom(name=room_name)
            db_session.add(room)
            db_session.commit()
        return redirect(url_for('chatroom', room_name=room_name))
    return render_template('chat.html')

@app.route('/chat/<room_name>')
def chatroom(room_name):
    if 'username' not in session:
        return redirect(url_for('index'))
    room = db_session.query(ChatRoom).filter_by(name=room_name).first()
    if not room:
        return "Room not found"
    return render_template('chatroom.html', room_name=room_name)

@socketio.on('join')
def handle_join(data):
    username = session['username']
    room = data['room']
    join_room(room)
    send({'msg': f'{username} has joined the room.', 'username': 'System', 'color': 'black'}, room=room)

@socketio.on('message')
def handle_message(data):
    data['color'] = session['color']
    send(data, room=data['room'])

@socketio.on('leave')
def handle_leave(data):
    username = session['username']
    room = data['room']
    leave_room(room)
    send({'msg': f'{username} has left the room.', 'username': 'System', 'color': 'black'}, room=room)

if __name__ == '__main__':
    socketio.run(app)
