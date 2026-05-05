import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from matching import calculate_compatibility
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = 'any_long_random_string_here'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///roommates.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# The updated User database model with ALL metrics
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    college = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    
    # Lifestyle Metrics
    year = db.Column(db.Integer, nullable=True)      # replaces age
    gender = db.Column(db.String(20), nullable=True)
    hobbies = db.Column(db.String(200), nullable=True)
    budget = db.Column(db.Integer, nullable=True)
    cleanliness = db.Column(db.Integer, nullable=True)
    noise_level = db.Column(db.Integer, nullable=True)
    sleep_schedule = db.Column(db.String(20), nullable=True)
    smoking = db.Column(db.Boolean, default=False)
    drinking = db.Column(db.Boolean, default=False)



    # Personification
    bio = db.Column(db.Text, nullable=True)
    profile_image = db.Column(db.String(300), nullable=True)
    
# Chat feature
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False) # For notifications

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        college = request.form.get('college') # Required only for new accounts
        
        # 1. Look for an existing user with this exact Name and Phone
        existing_user = User.query.filter_by(name=name, phone=phone).first()
        
        if existing_user:
            # 2. If they exist, log them in and go straight to Matches
            session['user_id'] = existing_user.id
            return redirect(url_for('matches', user_id=existing_user.id))
        
        # 3. If they DON'T exist, create the new account
        new_user = User(name=name, college=college, phone=phone)
        db.session.add(new_user)
        db.session.commit()
        
        session['user_id'] = new_user.id
        return redirect(url_for('preferences', user_id=new_user.id))
        
    return render_template('login.html')

@app.route('/inbox')
def inbox():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_id = session['user_id']
    
    # Get unique users the current user has chatted with
    sent = db.session.query(Message.receiver_id).filter_by(sender_id=user_id)
    received = db.session.query(Message.sender_id).filter_by(receiver_id=user_id)
    contact_ids = [r[0] for r in sent.union(received).all()]
    contacts = User.query.filter(User.id.in_(contact_ids)).all()
    
    unread_count = Message.query.filter_by(receiver_id=user_id, is_read=False).count()
    return render_template('inbox.html', contacts=contacts, unread_count=unread_count)

@app.route('/preferences/<int:user_id>', methods=['GET', 'POST'])
def preferences(user_id):
    user = User.query.get_or_404(user_id) # Find the user in the database
    
    if request.method == 'POST':
        # Update the user's empty columns with the form data
        user.year = request.form.get('year')
        user.gender = request.form.get('gender')
        user.hobbies = request.form.get('hobbies')
        user.budget = request.form.get('budget')
        user.cleanliness = request.form.get('cleanliness')
        user.noise_level = request.form.get('noise')
        user.sleep_schedule = request.form.get('sleep_schedule')
        user.smoking = True if request.form.get('smoking') else False
        user.drinking = True if request.form.get('drinking') else False
        
        db.session.commit() # Save the updates
        return redirect(url_for('matches', user_id=user.id)) # Send to matches page
        
    return render_template('preferences.html', user_id=user_id)

@app.route('/matches/<int:user_id>')
def matches(user_id):
    current_user = User.query.get_or_404(user_id)
    
    # Fetch everyone except the current user AND strictly from the same college
    all_others = User.query.filter(
        User.id != user_id, 
        User.college == current_user.college
    ).all()
    
    scored_matches = []
    for other in all_others:
        score = calculate_compatibility(current_user, other)
        scored_matches.append({'data': other, 'score': score})
    
    scored_matches.sort(key=lambda x: x['score'], reverse=True)
    
    # Calculate the unread count
    unread_count = Message.query.filter_by(receiver_id=user_id, is_read=False).count()
    
    return render_template('matches.html', 
                           current_user=current_user, 
                           potential_matches=scored_matches, 
                           unread_count=unread_count)

@app.route('/profile/<int:user_id>')
def view_profile(user_id):
    """View the full profile of a potential roommate."""
    user = User.query.get_or_404(user_id)
    return render_template('profile.html', user=user)

@app.route('/chat/<int:sender_id>/<int:receiver_id>', methods=['GET', 'POST'])
def chat(sender_id, receiver_id):
    sender = User.query.get_or_404(sender_id)
    receiver = User.query.get_or_404(receiver_id)
    
    if request.method == 'POST':
        content = request.form.get('message')
        if content:
            new_msg = Message(sender_id=sender_id, receiver_id=receiver_id, content=content)
            db.session.add(new_msg)
            db.session.commit()
            return redirect(url_for('chat', sender_id=sender_id, receiver_id=receiver_id))

    # Fetch messages between these two users
    messages = Message.query.filter(
        ((Message.sender_id == sender_id) & (Message.receiver_id == receiver_id)) |
        ((Message.sender_id == receiver_id) & (Message.receiver_id == sender_id))
    ).order_by(Message.timestamp.asc()).all()
    
    return render_template('chat.html', sender=sender, receiver=receiver, messages=messages)

if __name__ == '__main__':
    app.run(debug=True)