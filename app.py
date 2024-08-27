from flask import Flask, render_template, redirect, request, session, jsonify
from pyrebase import pyrebase
from firebase.main import *
from config import firebaseConfig
from auth.id import *
from auth.bots import fetch_bots, get_bot
import datetime
from reddit.main import RedditBot
from threading import Thread

firebase = pyrebase.initialize_app(config=firebaseConfig)
auth = firebase.auth()
db = firebase.database()

bot_thread = None

app = Flask(__name__)

app.secret_key = "sessionnew1111"

app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=5)

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(days=5)

@app.route("/")
def index_page():
    return "working"

@app.route("/register", methods=["POST", "GET"])
def register_page():
    if request.method == "POST":
        
        try:
            user_id = generate_id()
            email = request.form.get('email')
            password = request.form.get('password')
            username = request.form.get('username')
            
            auth.create_user_with_email_and_password(email, password)
            
            data = {
                "login_email": email,
                "login_pass":password, 
                "username":username
            }
            
            db.child('users').child(user_id).set(data)
            
            session['user_id'] = user_id
            
            return redirect("/dashboard") 
        except Exception as e:
            return f"something went wrong {e}"
    
    else:
        if 'user_id' in session:
            return redirect('/dashboard')
        else:
            return render_template("register.html")
    
@app.route("/login", methods=['GET', 'POST'])
def login_page():
    if 'user_id' in session:
        return redirect('/dashboard')
    else:
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            try:
                # Authenticate with Firebase Auth
                user = auth.sign_in_with_email_and_password(email=email, password=password)
                
                # Retrieve all user data from the database
                user_data = db.child('users').get().val()
                
                # Search for the user with the matching email and password
                user_id = None
                for uid, data in user_data.items():
                    if data['login_email'] == email and data['login_pass'] == password:
                        user_id = uid
                        break
                
                if user_id:
                    session['user_id'] = user_id
                    return redirect('/dashboard')
                else:
                    return "Error: Invalid email or password."
                
            except Exception as e:
                error_message = str(e)  # Convert the exception to a string
                return f"Error: {error_message}"
        else:
            return render_template("login.html")

@app.route('/logout')
def logout():
    try:
        session.pop('user_id')
    
        return redirect("/login")
    except:
        return redirect("/")
    
@app.route("/dashboard")
def dashboard_page():
    if 'user_id' in session:
        id = session['user_id']
        bots = fetch_bots(id)
        print(bots)
        return render_template("dashboard.html", bots=bots)
    else:
        return redirect('/register')

@app.route("/bot/<id>")
def bot_page(id):
    user_id = session['user_id']
    data = get_bot(user_id=user_id, bot_id=id)
    return render_template("info.html", id=id, data=data)

@app.route("/start-service", methods=['POST'])
def start_service(): 
    # Retrieve data from the POST request
    data = request.json
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')
    username = data.get('username')
    password = data.get('password')
    bot_id = data.get('bot_id')
    
    db.child('users').child(session['user_id']).child('bots').child(bot_id).child('status').set('running')
    
    # Instantiate the RedditBot with the received data
    reddit_bot = RedditBot(client_id=client_id, client_secret=client_secret, username=username, password=password, bot_id = bot_id, user_id=session['user_id'])
    
    global bot_thread
    bot_thread = Thread(target=reddit_bot.run)
    bot_thread.start()
    return jsonify({"status": "success", "message": "Reddit Bot started successfully!"})
    
   
@app.route("/stop-service", methods=['POST'])
def stop_service():
    # Retrieve data from the POST request
    data = request.json
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')
    username = data.get('username')
    password = data.get('password')
    bot_id = data.get('bot_id')
    
    db.child('users').child(session['user_id']).child('bots').child(bot_id).child('status').set('not_running')
    
    return {"status":"succesfull"}

@app.route("/create", methods=['GET', 'POST'])
def config_page():
    
    if request.method == "POST":
        
        user_id = session['user_id']
        bot_id = generate_bot_id()
        password = request.form.get('password')
        username = request.form.get('username')
        client_id = request.form.get('id')
        client_secret = request.form.get('secret')
        name = request.form.get('name')
        
        data = {
            'name':name,
            "username":username,
            "password":password,
            "client_id":client_id,
            "client_secret":client_secret,
            "status":"not_running",
            "last_comment_time":"",
            "logs":""
        }
        
        db.child('users').child(user_id).child("bots").child(bot_id).set(data)
        
        return redirect("/dashboard")
        
    else:
        if 'user_id' in session:
           return render_template("create.html")
        else:
            return redirect('/login')
        
app.run(debug=True)

