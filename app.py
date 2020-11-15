#sets up a small table to hold user data

import time
from datetime import datetime
from flask import Flask, redirect, url_for, render_template, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user
from signin import OAuthSignIn


app = Flask(__name__)
app.config['SECRET_KEY'] = 'top secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['OAUTH_CREDENTIALS'] = {
    'twitter': {
        'id': '<INSERT KEY>',
        'secret': '<INSERT SECRET>'
    }
}

db = SQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'index'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer(), primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=True)
    score = db.Column(db.Integer(), default=0)
    tf = db.Column(db.Boolean())
    num_days_set = db.Column(db.Integer(), default = 0)
    num_days_work = db.Column(db.Integer(), default=0)
    time_set = db.Column(db.DateTime(), default=datetime.now())


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/')
def index():
    if current_user.is_authenticated:
        user_id = current_user.get_id()
        user = User.query.filter_by(id=user_id).first()
        print(user.nickname)
        print(user.score)
        print("Plz for the love of god" + str(user.num_days_set))
        if user.num_days_set == 0 or (user.time_set-datetime.now()).days >= 7 or user.num_days_work >= user.num_days_set:
            if (user.time_set-datetime.now()).days >= 7:
                user.score = User.score - 1
                db.session.commit()
            if user.num_days_work >= user.num_days_set:
                return render_template("completed.html")
            return render_template('set_goal.html')
        else:
            num_days_work = 0
            if user.num_days_work != None:
                num_days_work = user.num_days_work
            print(num_days_work)
            return render_template("progress.html", num_days_set=user.num_days_set, num_days_work=num_days_work)
        #if(user.time_set> 168:00:00)
    return render_template('splash.html')


#route for incrementing your points
@app.route('/point', methods=['POST'])
def add_point():
    if current_user.is_authenticated:
        user_id = current_user.get_id()
        user = User.query.filter_by(id=user_id).first()
        user.score = User.score + 1
        user.num_days_work = User.num_days_work + 1
        db.session.commit()
    return str(user.score)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/set', methods=['GET', 'POST'])
def set_goal():
    if request.method == 'POST':
        if current_user.is_authenticated:
            print(request.form)
            num_days_set = request.form.get('time')
            print("HELLO" + str(num_days_set))
            user_id = current_user.get_id()
            user = User.query.filter_by(id=user_id).first()
            print(num_days_set)
            user.num_days_set = num_days_set
            user.num_days_work = 0
            user.time_set = datetime.now()
            print(user.time_set)
            db.session.commit()
    return redirect("/")

@app.route('/info', methods=['GET'])
def send_data():
    if current_user.is_authenticated:
        user_id = current_user.get_id()
        user = User.query.filter_by(id=user_id).first()
        if (user.time_set-datetime.now()).days >= 7:
            return "Reset goalss"
        else:
             return "view goalss"
        #if(user.time_set> 168:00:00)
    return "NOT LOGGED IN BITCH"    

@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('index'))


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)