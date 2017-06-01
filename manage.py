#!/usr/bin/env python
import os
from app import create_app, db
from app.models import User, Role
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
  return dict(app=app, db=db, User=User, Role=Role)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
  """Run the unit test"""
  import unittest
  tests = unittest.TestLoader().discover('tests')
  unittest.TextTestRunner(verbosity=2).run(tests)

@manager.command
def sendemail():
  from flask_mail import Message
  from app import mail
  msg = Message('test subject', sender='963076844@qq.com',
     recipients=['zhangfeihu@sinosoft.com'])
  msg.body = 'text body'
  msg.html = '<b>HTML</b> body'
  with app.app_context():
    mail.send(msg)

if __name__ == '__main__':
  manager.run()
