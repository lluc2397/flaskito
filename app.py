from flask import Flask, render_template, flash, request, redirect, url_for
from datetime import datetime 
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash 
from datetime import date
from forms import LoginForm, PostForm, UserForm, SearchForm
from flask_login import login_user, LoginManager, login_required, logout_user, current_user, UserMixin
from flask_ckeditor import CKEditor
from werkzeug.utils import secure_filename
import uuid as uuid
import os

# Create a Flask Instance
app = Flask(__name__)

ckeditor = CKEditor(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flaskdb.db'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://lucas:tete2323@127.0.0.1:5432/flasktestdb'

# Secret Key!
app.config['SECRET_KEY'] = "my super secret key"


UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
migrate = Migrate(app, db, render_as_batch=True)

# Flask_Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


@app.context_processor
def base():
	form = SearchForm()
	return dict(form=form)


@app.route('/search', methods=["POST"])
def search():
	form = SearchForm()
	posts = Post.query
	if form.validate_on_submit():
		post.searched = form.searched.data

		posts = posts.filter(Post.content.like('%' + post.searched + '%'))
		posts = posts.order_by(Post.title).all()

		return render_template("search.html",
		 form=form,
		 searched = post.searched,
		 posts = posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user:

			if check_password_hash(user.password_hash, form.password.data):
				login_user(user)
				flash("Login cool")
				return redirect(url_for('dashboard'))
			else:
				flash("wrong password try again")
		else:
			flash("User doesn't exists")

	return render_template('login.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
	logout_user()
	flash("Logout cool")
	return redirect(url_for('login'))


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
	form = UserForm()
	id = current_user.id
	name_to_update = User.query.get_or_404(id)
	if request.method == "POST":
		name_to_update.name = request.form['name']
		name_to_update.email = request.form['email']
		name_to_update.favorite_color = request.form['favorite_color']
		name_to_update.username = request.form['username']
		name_to_update.about_author = request.form['about_author']
		
		if request.files['profile_pic']:
			name_to_update.profile_pic = request.files['profile_pic']
			pic_filename = secure_filename(name_to_update.profile_pic.filename)			
			pic_name = str(uuid.uuid1()) + "_" + pic_filename			
			saver = request.files['profile_pic']			
			name_to_update.profile_pic = pic_name

			try:
				db.session.commit()
				saver.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
				flash("User updated")
				
			except:
				flash("Error try again")
				
		else:
			db.session.commit()
			flash("User updated")

		return render_template("dashboard.html", 
			form=form, 
			name_to_update = name_to_update)

	else:
		return render_template("dashboard.html", 
				form=form,
				name_to_update = name_to_update,
				id = id)



@app.route('/posts/delete/<int:id>')
@login_required
def delete_post(id):
	post_to_delete = Post.query.get_or_404(id)
	id = current_user.id
	if id == post_to_delete.author.id:
		try:
			db.session.delete(post_to_delete)
			db.session.commit()
			flash("Blog deleted")

		except:
			flash("Error try again...")
			
	else:
		flash("Not authorized")

	posts = Post.query.order_by(Post.date_posted)
	return redirect(url_for('posts', posts=posts))


@app.route('/posts')
def posts():
	posts = Post.query.order_by(Post.date_posted)
	return render_template("posts.html", posts=posts)


@app.route('/posts/<int:id>')
def post(id):
	post = Post.query.get_or_404(id)
	return render_template('post.html', post=post)


@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
	post = Post.query.get_or_404(id)
	form = PostForm()

	if form.validate_on_submit():
		post.title = form.title.data
		post.slug = form.slug.data
		post.content = form.content.data
		db.session.add(post)
		db.session.commit()

		flash("Post updated")
		return redirect(url_for('post', id=post.id))
	
	if current_user.id == post.author_id:
		form.title.data = post.title
		form.slug.data = post.slug
		form.content.data = post.content
		return render_template('edit_post.html', form=form)

	else:
		flash("You can't edit this post")
		posts = Post.query.order_by(Post.date_posted)
		return render_template("posts.html", posts=posts)


@app.route('/add-post', methods=['GET', 'POST'])
def add_post():
	form = PostForm()

	if form.validate_on_submit():
		author = current_user.id
		post = Post(title=form.title.data, content=form.content.data, author_id=author, slug=form.slug.data)
		# Clear the form
		form.title.data = ''
		form.content.data = ''
		form.slug.data = ''

		db.session.add(post)
		db.session.commit()

		flash("Blog Post Submitted Successfully!")

	return render_template("add_post.html", form=form)


@app.route('/delete/<int:id>')
@login_required
def delete(id):
	if id == current_user.id:
		user_to_delete = User.query.get_or_404(id)
		name = None
		form = UserForm()

		try:
			db.session.delete(user_to_delete)
			db.session.commit()
			flash("User deleted")

			our_users = User.query.order_by(User.date_added)
			
		except:
			flash("Error! try again...")

		return render_template(
			"add_user.html", 
			form=form, 
			name=name,
			our_users=our_users)

	else:
		flash("Sorry, you can't delete this user ")
		return redirect(url_for('dashboard'))


@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
	form = UserForm()
	name_to_update = User.query.get_or_404(id)
	if request.method == "POST":
		name_to_update.name = request.form['name']
		name_to_update.email = request.form['email']
		name_to_update.favorite_color = request.form['favorite_color']
		name_to_update.username = request.form['username']

		try:
			db.session.commit()
			flash("User updated")
			
		except:
			flash("Error! try again!")			
	
	return render_template(
		"update.html", 
		form=form,
		name_to_update = name_to_update,
		id = id)


@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
	name = None
	form = UserForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user is None:
			# Hashing the password
			hashed_pw = generate_password_hash(form.password_hash.data, "sha256")
			user = User(username=form.username.data, name=form.name.data, email=form.email.data, favorite_color=form.favorite_color.data, password_hash=hashed_pw)
			db.session.add(user)
			db.session.commit()
		name = form.name.data
		form.name.data = ''
		form.username.data = ''
		form.email.data = ''
		form.favorite_color.data = ''
		form.password_hash.data = ''

		flash("New user created")
	our_users = User.query.order_by(User.date_added)
	return render_template(
		"add_user.html", 
		form=form,
		name=name,
		our_users=our_users)


@app.route('/')
def index():
	first_name = "Lucas"
	things_list = ["skate", "pizza", "papas", 41]

	return render_template("index.html", 
		first_name=first_name,
		things_list = things_list)


# Invalid URL
@app.errorhandler(404)
def page_not_found(e):
	return render_template("complements/404.html"), 404

# Internal Server Error
@app.errorhandler(500)
def page_not_found(e):
	return render_template("complements/500.html"), 500






class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(255))
	content = db.Column(db.Text)
	date_posted = db.Column(db.DateTime, default=datetime.utcnow)
	slug = db.Column(db.String(255))
	author_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), nullable=False, unique=True)
	name = db.Column(db.String(200), nullable=False)
	email = db.Column(db.String(120), nullable=False, unique=True)
	favorite_color = db.Column(db.String(120))
	about_author = db.Column(db.Text(), nullable=True)
	date_added = db.Column(db.DateTime, default=datetime.utcnow)
	profile_pic = db.Column(db.String(), nullable=True)
	password_hash = db.Column(db.String(128))
	posts = db.relationship('Post', backref='author')

	def __repr__(self):
		return f'{self.name}'

	@property
	def password(self):
		raise AttributeError('password is not a readable')

	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)

	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)
