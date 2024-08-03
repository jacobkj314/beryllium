from flask import Flask, request, redirect, render_template, render_template_string, url_for, flash, get_flashed_messages
from flask_socketio import SocketIO, join_room, leave_room
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

import utils
from datetime import datetime

# # # MEMORY SETUP
from IMAGES import IMAGES

# # # FLASK SETUP
app = Flask(__name__)
app.config['SECRET_KEY'] = utils.get_secret_key()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.add_template_global(name='images', f=IMAGES)



login_manager = LoginManager(app)
login_manager.login_view = 'handle_login'

socketio = SocketIO(app)

# # # DATABASE STUFF

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def can_view_posts(self):
        return (self.username in IMAGES.keys())
    @property
    def can_post(self):
        return (self.username not in IMAGES.keys())
    
    @property
    def users_to_view(self):
        results = db.session.query  (
                                        ViewSetting.that_user_id
                            ).join  (
                                        ShowSetting,
                                        (ViewSetting.this_user_id == ShowSetting.that_user_id)
                                        & 
                                        (ViewSetting.that_user_id == ShowSetting.this_user_id)
                            ).filter(
                                ViewSetting.this_user_id == self.id
                            ).all()
        return [load_user(result[0]) for result in results]


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()

class ViewSetting(db.Model):
    this_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    that_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    this_user = relationship('User', foreign_keys=[this_user_id])
    that_user = relationship('User', foreign_keys=[that_user_id])
def views(viewer:User, poster:User):
    return bool(
        ViewSetting.query.filter_by(
            this_user_id=viewer.id, 
            that_user_id=poster.id
        ).first()
    )
def update_view_setting(viewer:User, poster:User, target_view_setting:bool):
    existing_relation = ViewSetting.query.filter_by(
            this_user_id=viewer.id, 
            that_user_id=poster.id
        ).first()
    if target_view_setting and (existing_relation is None):
        new_relation = ViewSetting(this_user_id=viewer.id, that_user_id=poster.id)
        db.session.add(new_relation)
    elif not target_view_setting and not (existing_relation is None):
            db.session.delete(existing_relation)
    db.session.commit()


class ShowSetting(db.Model):
    this_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    that_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    this_user = relationship('User', foreign_keys=[this_user_id])
    that_user = relationship('User', foreign_keys=[that_user_id])
def shows(poster:User, viewer:User):
    return bool(
        ShowSetting.query.filter_by(
            this_user_id=poster.id, 
            that_user_id=viewer.id
        ).first()
    )
def update_show_setting(poster:User, viewer:User, target_show_setting:bool):
    existing_relation = ShowSetting.query.filter_by(
            this_user_id=poster.id, 
            that_user_id=viewer.id
        ).first()
    if target_show_setting and (existing_relation is None):
        new_relation = ShowSetting(this_user_id=poster.id, that_user_id=viewer.id)
        db.session.add(new_relation)
    elif not target_show_setting and not (existing_relation is None):
            db.session.delete(existing_relation)
    db.session.commit()









# # # ROUTES
last_reset_time = datetime.now()
@app.before_request
def check_reset():
    print(request)

    global last_reset_time, IMAGES
    now = datetime.now()
    intended_last_reset_time = datetime(now.year, now.month, now.day, 12, 0, 0, 0) #TODO : have a better and more varied function to determine when the server resets
    if now > intended_last_reset_time and not last_reset_time > intended_last_reset_time: 
        IMAGES = {}
        last_reset_time = now

@app.route('/', methods=['GET', 'POST'])
@login_required
def main():
    global IMAGES
    if request.method == 'GET':
        return render_template('index.html')
    if current_user.can_post:
        faceImage = request.form['faceImage']
        awayImage = request.form['awayImage']
        if current_user.username not in IMAGES.keys():
            IMAGES[current_user.username] = []
        current_user_posts = IMAGES[current_user.username]
        post =  (
                    {
                        "images"    :   [
                                            faceImage, 
                                            awayImage
                                        ], 
                        "timestamp" :   datetime.now(), 
                        "comments"  :   list()
                    }
                )
        IMAGES[current_user.username].append(post)

        socketio.emit   (
                            'add_post',
                            {
                                'user':current_user.username,
                                'post_number':len(IMAGES[current_user.username])-1,
                                'new_post':render_template('post.html', relevant_user=current_user, post=post, post_number=len(current_user_posts)-1)
                            },
                            room = current_user.username
                        )
    return redirect(url_for('main'))

@app.get('/api/')
@login_required
def handle_api():
    return '' #TODO

@app.route('/user/', methods=['GET', 'POST'])
@login_required
def handle_user_interaction():
    other_username = (request.form if request.method=='POST' else request.args)['username'].lower()
    other_user = User.query.filter_by(username=other_username).first()
    if not other_user:
        return render_template_string('The user {{ other_username}} does not exist!')
    if request.method == 'POST':
        view = bool(request.form.get('view'))
        show = bool(request.form.get('show'))
        update_view_setting(current_user, other_user, view)
        update_show_setting(current_user, other_user, show)
    return render_template('userpage.html', other_user=other_user, views=views, shows=shows)

@app.route('/signup/', methods=['GET', 'POST'])
def handle_signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return 'Username already exists'
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('main'))
    return render_template('signup.html')

@app.route('/login/', methods=['GET', 'POST'])
def handle_login():
    if current_user.is_authenticated:
        return redirect(url_for('main'))
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main'))
        return "Invalid Credentials"
    return render_template('login.html')

@app.get('/logout/')
def handle_logout():
    logout_user()
    return redirect('/')

@app.post('/comment/')
@login_required
def handle_comment():
    poster_username = request.form['poster_username']
    poster_post     = request.form['poster_post']
    comment_text    = request.form['comment_text']
    comment_timestamp = datetime.now()

    print(request.form)

    if not (poster_username in IMAGES.keys() and len(IMAGES[poster_username]) > int(poster_post)):
        return '' #TODO - probably should be a 404 error I think
    #TODO - should verify that current_user views() poster's posts

    new_comment =   (
                        current_user,
                        comment_timestamp,
                        comment_text
                    )

    IMAGES[poster_username][int(poster_post)]["comments"].append(new_comment)

    socketio.emit   (
                            'add_comment',
                            {
                                'poster':current_user.username,
                                'post_number':poster_post,
                                'new_comment':render_template('comment.html', commenter=current_user, comment_timestamp=comment_timestamp, comment_text=comment_text)
                            },
                            room = poster_username
                        )
    
    return 'success'

# # # SOCKET.IO
@socketio.on('connect')
def handle_connect():
    join_room(current_user.username)
    for other_user in current_user.users_to_view:
        join_room(other_user.username)
@socketio.on('disconnect')
def handle_disconnect():
    for other_user in current_user.users_to_view:
        leave_room(other_user.username)
    leave_room(current_user.username)

if __name__ == '__main__':
    socketio.run(app, debug=True)