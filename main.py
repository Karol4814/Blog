from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash,request
from typing import List
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column 
from sqlalchemy import Integer, String, Text,ForeignKey
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
# Import your forms from the forms.py
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from dotenv import load_dotenv
load_dotenv()
import os 
os.chdir(r"C:\Python\100 days course\Day 71")

'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirementsaaaaaaaaaaaa.txt 

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)

# TODO: Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'

db = SQLAlchemy(model_class=Base)
db.init_app(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# CONFIGURE TABLES
class User(UserMixin,db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    posts = relationship("BlogPost", back_populates="author")

    comments = relationship("Comment", back_populates="comment_author")
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author = relationship("User", back_populates="posts")
    author_id: Mapped[int] = mapped_column(Integer,ForeignKey("users.id"))
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    comments = relationship("Comment",back_populates="parent_post")
class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    comment_author = relationship("User",back_populates="comments")
    author_id: Mapped[int] = mapped_column(Integer,ForeignKey("users.id"))
    post_id: Mapped[int] = mapped_column(Integer,ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost",back_populates="comments")
with app.app_context():
    db.create_all()
# TODO: Create a User table for all your registered users. 



@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

with app.app_context():
    db.create_all()


def admin_only(function):
    @wraps(function)
    def decorated_function(*args,**kwargs):
       if current_user.id == 1:
            return function(*args,**kwargs)
       return abort(403)
    return decorated_function

# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register',methods = ["GET","POST"])
def register():
    form = RegisterForm()
    if request.method == "POST":
        password_hash = generate_password_hash(password=form.password.data,salt_length=8,method='pbkdf2:sha256')
        new_user = User(
            email = form.email.data,
            password = password_hash,
            name = form.name.data

        )
        result = db.session.execute(db.select(User).where(User.email == new_user.email))
        user = result.scalar()
        if user:
            error = "You already signed up log in instead"
            return render_template("login.html",error = error)
        
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user) 
        return redirect(url_for('get_all_posts'))
    return render_template("register.html",form = form,current_user = current_user)


# TODO: Retrieve a user from the database based on their email. 
@app.route('/login',methods = ["POST","GET"])
def login():
    
    form = LoginForm()
    if request.method == "POST":
        email = form.email.data
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        if user:
            
            password = form.password.data
            if check_password_hash(user.password,password):
                login_user(user)
                return redirect(url_for('get_all_posts'))
            else:
                error = "Invalid password"
                return render_template("login.html",error=error,form=form,current_user = current_user)
        else:
            error = "Invalid email"
            return render_template("login.html",error=error,form=form,current_user = current_user)
    return render_template("login.html",form = form,current_user = current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts)


# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>",methods = ["POST","GET"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    form = CommentForm()
    if request.method == "POST":
        new_comment = Comment(
            body = form.body.data,
            comment_author = current_user,
            parent_post = requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
    result = db.session.execute(db.select(Comment).where(Comment.parent_post  == requested_post))
    comments = result.scalars().all()
    return render_template("post.html", post=requested_post, form = form,comments = comments,gravatar = gravatar)


# TODO: Use a decorator so only an admin user can create a new post

@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form,current_user = current_user)


# TODO: Use a decorator so only an admin user can edit a post

@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id,current_user = current_user))
    return render_template("make-post.html", form=edit_form, is_edit=True,current_user = current_user)


# TODO: Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts',current_user = current_user))


@app.route("/about")
def about():
    return render_template("about.html",current_user = current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html",current_user = current_user)


if __name__ == "__main__":
    app.run(debug=True, port=5002)
