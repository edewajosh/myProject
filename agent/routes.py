from agent.models import users, update_site
from agent import app, db, bcrypt, APP_ROOT,destination, mail
from flask import render_template,flash,redirect, url_for, request,send_from_directory
from data import Products
from agent.forms import RegistrationForm, LoginForm, UploadForm, RequestResetForm, ResetPasswordForm
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug import secure_filename
from flask_wtf.file import FileAllowed
from flask_mail import Message
import os
import secrets


@app.route('/')
def index():
   
    return render_template('index.html') 

@app.route('/about')
@login_required
def about():
    return render_template('about.html')

def save_image(form_image):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename)
    image_fn = random_hex + f_ext
    image_path = os.path.join(app.root_path, 'static/photos', image_fn)
    form_image.save(image_path) 
    return image_fn


@app.route('/home', methods = ['GET'])
@login_required
def home():
    house = update_site.query.first()
    images = os.path.join(app.root_path, 'static/photos'+ house.images)
    return render_template('home.html', images = images, house = house)
    #pics = os.listdir(destination)  
    #return render_template('home.html',pics=pics)

@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = users(username = form.username.data, email = form.email.data, password = hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account created for you please login!!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form = form)

@app.route('/login',methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = users.query.filter_by(email = form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember= form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessiful please check email and password!', 'danger')
    return render_template('login.html', form = form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile')
#@login_required
def profile():
    return render_template('profile.html')

@app.route('/update', methods = ['GET', 'POST'])
def update():
    form = UploadForm()
    if form.validate_on_submit():
        if form.image.data:
            photo = save_image(form.image.data) 
        plot = update_site(plotname = form.plotname.data, images = photo)
        db.session.add(plot)
        db.session.commit()
        flash('data added successifilly', 'success')
        return redirect(url_for('update'))
    return render_template('upload.html', form = form)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Reset password request', sender='joseymahugu@gmail.com', recipients=[user.email])
    msg.body = f''' To reset your password, visit the following link
{url_for('reset_token', token = token, external = True)}
If you did nor request this email ignore and no changes will be made
'''
    with app.app_context():
        mail.send(msg)

@app.route('/reset_password', methods = ['GET', 'POST'])
def request_reset():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = users.query.filter_by(email = form.email.data).first()
        send_reset_email(user)
        flash('A reset email has been sent to your email address', 'info')
        return redirect(url_for('login'))
    return render_template('request_reset.html', form = form)

@app.route('/reset_password/<token>', methods = ['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = user.veryfy_reset_token(token)
    if user is None:
        flash('The token is invalid or has expired','warning')
        return redirect(url_for('request_reset'))
    form = RersetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been reset', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', form = form)