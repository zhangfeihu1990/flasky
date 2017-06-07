from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from . import login_manager
from . import db
from datetime import datetime
from flask import current_app,request, url_for
from app.exceptions import ValidationError

# from markdown import markdown
# import bleach

class Permission:
  FOLLOW = 0x01
  COMMENT = 0x02
  WRITE_ARTICLES = 0x04
  MODERATE_COMMENTS = 0x08
  ADMINISTER = 0x80

class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
  __tablename__ = 'users'
  id = db.Column(db.Integer, primary_key = True)
  email = db.Column(db.String(64), unique=True, index=True)
  username = db.Column(db.String(64), unique=True, index=True)
  password_hash = db.Column(db.String(128))
  #password = db.Column(db.String(128))
  role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

  name = db.Column(db.String(64))
  location = db.Column(db.String(64))
  about_me = db.Column(db.Text())
  member_since = db.Column(db.DateTime(), default=datetime.utcnow())
  last_seen = db.Column(db.DateTime(), default=datetime.utcnow())
  posts = db.relationship('Post', backref='author', lazy='dynamic')
  followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
  followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
  comments = db.relationship('Comment', backref='author', lazy='dynamic')
  @property
  def followed_posts(self):
     return Post.query.join(Follow, Follow.followed_id == Post.author_id)\
            .filter(Follow.follower_id == self.id)

  def ping(self):
    self.last_seen = datetime.utcnow()
    db.session.add(self)
  # ...
  def __init__(self, **kwargs):
    super(User, self).__init__(**kwargs)
    if self.role is None:
      if self.email == current_app.config['FLASKY_ADMIN']:
        self.role = Role.query.filter_by(permissions=0xff).first()
      if self.role is None:
        self.role = Role.query.filter_by(default=True).first()
  def can(self, permissions):
    return self.role is not None and \
     (self.role.permissions & permissions) == permissions
  def is_administrator(self):
    return self.can(Permission.ADMINISTER)


  @login_manager.user_loader
  def load_user(user_id):
    return User.query.get(int(user_id))
  @property
  def password(self):
    raise AttributeError('password is not a readable attribute')
  @password.setter
  def password(self, password):
    self.password_hash = generate_password_hash(password)
  def verify_password(self, password):
    return check_password_hash(self.password_hash, password)

  def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)
            db.session.commit()

  def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)
            db.session.commit()

  def is_following(self, user):
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

  def is_followed_by(self, user):
        return self.followers.filter_by(
            follower_id=user.id).first() is not None


class AnonymousUser(AnonymousUserMixin):
  def can(self, permissions):
    return False
  def is_administrator(self):
    return False
login_manager.anonymous_user = AnonymousUser



class Role(db.Model):
  __tablename__ = 'roles'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(64), unique=True)
  default = db.Column(db.Boolean, default=False, index=True)
  permissions = db.Column(db.Integer)
  users = db.relationship('User', backref='role', lazy='dynamic')
  @staticmethod
  def insert_roles():
    roles = {
      'User': (Permission.FOLLOW |
        Permission.COMMENT |
        Permission.WRITE_ARTICLES, True),
      'Moderator': (Permission.FOLLOW |
        Permission.COMMENT |
        Permission.WRITE_ARTICLES |
        Permission.MODERATE_COMMENTS, False),
      'Administrator': (0xff, False)
    }
    for r in roles:
      role = Role.query.filter_by(name=r).first()
      if role is None:
        role = Role(name=r)
      role.permissions = roles[r][0]
      role.default = roles[r][1]
      db.session.add(role)
    db.session.commit()

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    def to_json(self):
        json_post = {
            'url': url_for('api.get_post', id=self.id, _external=True),
            'body': self.body,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id,
                              _external=True),
            'comments': url_for('api.get_post_comments', id=self.id,
                                _external=True),
            'comment_count': self.comments.count()
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('post does not have a body')
        return Post(body=body)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    def to_json(self):
        json_comment = {
            'url': url_for('api.get_comment', id=self.id, _external=True),
            'post': url_for('api.get_post', id=self.post_id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id,
                              _external=True),
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')
        return Comment(body=body)

    # @staticmethod
    # def on_changed_body(target, value, oldvalue, initiator):
    #     allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
    #                     'strong']
    #     target.body_html = bleach.linkify(bleach.clean(
    #         markdown(value, output_format='html'),
    #         tags=allowed_tags, strip=True))

# db.event.listen(Comment.body, 'set', Comment.on_changed_body)