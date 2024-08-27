from pyrebase import pyrebase
from config import firebaseConfig

firebase = pyrebase.initialize_app(config=firebaseConfig)
auth = firebase.auth()
db = firebase.database()

def save_config(id, client_id ,client_secret, username, password):
    data = {
        "client_id":client_id,
        "client_secret":client_secret,
        "username":username,
        "password":password
    }
    db.child(id).child("app").set(data)
    
    