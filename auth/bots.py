from pyrebase import pyrebase
from config import firebaseConfig
import json

firebase = pyrebase.initialize_app(config=firebaseConfig)
auth = firebase.auth()
db = firebase.database()

def fetch_bots(user_id):
    bots = db.child('users').child(user_id).child('bots').get().val()
    return bots

def get_bot(user_id, bot_id):
    bots = db.child('users').child(user_id).child('bots').child(bot_id).get().val()
    return bots

def create_log(user_id, log, bot_id):
    bots = db.child('users').child(user_id).child('bots').child(bot_id).child('logs').set(log)
    return True

def fetch_log(user_id, bot_id):
    bots = db.child('users').child(user_id).child('bots').child(bot_id).child('log').get().val
    return bots

def comment_time():
    time = "20:59"
    return time