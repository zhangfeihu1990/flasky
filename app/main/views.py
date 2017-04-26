from datetime import datetime
from flask import render_template, session, redirect, url_for
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries

from . import main
from .forms import NameForm, EditProfileForm, PostForm
from .. import db
from ..models import User, Permission, Post

@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        print 'save post'
        post = Post(body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('.index'))
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    print posts
    return render_template('index.html', form=form, posts=posts)
  # return render_template('index.html',
  #       form=form, name=session.get('name'),
  #       known=session.get('known', False),
  #       current_time=datetime.utcnow())

@main.route('/user/<username>')
def user(username):
  user = User.query.filter_by(username=username).first()
  if user is None:
    abort(404)
  return render_template('user.html', user=user)


#@login_required
@main.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    # form.name.data = current_user.name
    # form.location.data = current_user.location
    # form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)