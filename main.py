from flask import *
import requests
from flask_wtf import *
from wtforms import *
from wtforms.validators import *
from flask_sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy import *
from werkzeug.utils import secure_filename
from werkzeug.security import *
import os
import smtplib
from random import *
from flask import session
from flask_login import *
import math
import json
from flask_wtf.file import FileAllowed
from typing import List
from functools import wraps
from datetime import date
import datetime as dt
from flask_migrate import Migrate
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from wtforms import HiddenField
#from flask.sessions import SecureCookieSessionInterface
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv
from flask_mail import Mail, Message
#"""from utils.email import send_email"""

load_dotenv()
class Base(DeclarativeBase):
    pass
    
mail = Mail()

#database setup
app = Flask(__name__)
db = SQLAlchemy(model_class=Base)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URI")

#email config
app.config['MAIL_SERVER'] = 'smtp.mailgun.org'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = os.getenv('MY_EMAIL')
app.config['MAIL_PASSWORD'] = os.getenv('MY_EMAIL_PASSWORD')
app.config['MAIL_USE_TLS'] =  True
app.config['MAIL_DEFAULT_SENDER'] = 'ceefind@sandboxe4f442f327d74f65b6c1d5e30d6c9838.mailgun.org'

db.init_app(app)
migrate = Migrate()
migrate.init_app(app, db)
mail.init_app(app)

def send_email(subject, recipients, body, html=None):
    msg=Message(
        subject=subject, 
        recipients=recipients, 
        body=body, 
        html=html
        )
    mail.send(msg)

#email setup
def generate_token(email):
    serializer = URLSafeTimedSerializer(
        app.config['SECRET_KEY']
        )
    return serializer.dumps(email, salt='email-confirm')

def confirm_token(token, expiration=5000):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    try:
        email = serializer.loads(token, salt='email-confirm' ,max_age=expiration)
        return email
    except:
        return False

@app.route('/send_link/<email>')
@login_required
def send_verification_email(email):
    user = User.query.filter_by(email=email).first()
    count = 0
    token = generate_token(email)
    verify_url = url_for(
        'verify', 
        token=token, 
        _external=True)

    html = f"""
        <h2>Verify Your Email</h2>
        <p>Click the link below to verify your email</p>
        <a style="
                display: flex;
                text-decoration: none;
                width: 60%;
                margin: auto;
                background-color: blue;
                color: white;
                font-size: bold;
                border-radius: 30px;
                height: 30px;
                text-align: center;
                justify-content: center;
                align-items: center;"
        href="{verify_url}">
        Verify Email
        </a>"""
    
    if count != 3:
        send_email(
            subject='Verify Your Account', 
            recipients=[email], 
            body='Verify Your Email', 
            html=html
            )
        count += 1

    return render_template('verify.html', email=email, count=count)

def gravatar(email, size=50):
    email_hash = hashlib.md5(email.lower().encode()).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon"
    
#configure flask_login
login_manager = LoginManager()
login_manager.init_app(app)

#create a user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

google_bp = make_google_blueprint(
    client_id=573938737365,
    client_secret="6b87752glebv0ls3np20eu7vfdec1da5.apps.googleusercontent.com",
    scope=["profile", "email"]
    )

facebook_bp = make_facebook_blueprint(
    client_id='' ,
    client_secret= '',
    scope=["email"]
)

#
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")
#app.session_interface = RotatingSessionInterface(SECRET_KEYS)
UPLOAD_FOLDER = os.path.join(os.getcwd(),"static")
app.config["ALLOWED_EXTENSION"] = {'.png', '.jpg', '.jpeg', '.gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.register_blueprint(google_bp, url_prefix="/login")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

#Tables setup
class Technicians(db.Model):
    __tablename__ = "technician"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    shop_name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    career: Mapped[str] = mapped_column(String(250), nullable=False)
    state: Mapped[str] = mapped_column(String(250), nullable=False)
    contact: Mapped[str] = mapped_column(String(15), nullable=True)
    working_hours: Mapped[str] = mapped_column(String(20), nullable=False)
    image: Mapped[str] = mapped_column(String(250), nullable=True)
    email: Mapped[str] = mapped_column(String(250), nullable=True)
    reviews = relationship("Reviews", back_populates="tech_profile")
    author = relationship("User", back_populates="profiles")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    bio: Mapped[str] = mapped_column(String(450), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    reports = relationship("Reported", back_populates="tech_report")
    appeal = relationship("Appeal", back_populates="tech")
    
class Product(db.Model):
    __tablename__ = "post"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    image: Mapped[str] = mapped_column(String(200), nullable=False)
    gallery: Mapped[list[str]] = mapped_column(JSON, nullable=True)
    price: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    negotiable: Mapped[str] = mapped_column(String(50), nullable=False)
    contact: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    author = relationship("User", back_populates="posts")
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    reviews = relationship("Reviews", back_populates="product_post")
    reports = relationship("Reported", back_populates="post_report")
    appeal = relationship("Appeal", back_populates='post')
               
class Appeal(db.Model):
    __tablename__ = 'appeals'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    image: Mapped[str] = mapped_column(String(50), nullable=False)
    appeal_id: Mapped[int] = mapped_column(Integer, ForeignKey('post.id'), nullable=True)
    id_card: Mapped[str] = mapped_column(String(50), nullable=True)
    post = relationship('Product', back_populates='appeal')
    tech_id: Mapped[int] = mapped_column(Integer, ForeignKey('technician.id'), nullable=True)
    tech = relationship('Technicians', back_populates="appeal")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    user = relationship('User', back_populates="appeal")

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    firstname: Mapped[str] = mapped_column(String(250), nullable=False)
    lastname: Mapped[str] = mapped_column(String(250), nullable=True)
    provider: Mapped[str] = mapped_column(String(50), default="local")
    referral: Mapped[str] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=True)
    image: Mapped[str] = mapped_column(String(100), nullable=True)
    posts = relationship('Product', back_populates="author")
    reviews = relationship("Reviews", back_populates="commenter_name")
    profiles = relationship("Technicians", back_populates="author")
    reports = relationship("Reported", back_populates="reporter")
    appeal = relationship("Appeal", back_populates="user")
    
class Reviews(db.Model):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(Integer,ForeignKey("users.id"), nullable=True)
    text: Mapped[str] = mapped_column(String(250), nullable=False)
    commenter_name = relationship('User', back_populates="reviews")
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("post.id"), nullable=True)
    product_post = relationship("Product", back_populates="reviews")
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("technician.id"), nullable=True)
    tech_profile = relationship("Technicians", back_populates="reviews")
    
class Reported(db.Model):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("post.id"), nullable=True)
    post_report = relationship("Product", back_populates="reports")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    reporter = relationship("User", back_populates="reports")
    reporter_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tech_id: Mapped[int] = mapped_column(Integer, ForeignKey("technician.id"), nullable=True)
    tech_report = relationship("Technicians", back_populates="reports")
    
with app.app_context():
    db.create_all()
    

states = [
    "Abia","Adamawa",
    "Akwa Ibom","Anambra"
    ,"Bauchi","Bayelsa",
    "Benue","Bornu",
    "Crossriver","Delta",
    "Ebonyi","Edo",
    "Ekiti","Enugu",
    "Gombe","Imo",
    "Jigawa","Kaduna",
    "Kano","Katsina",
    "Kebbi","Kogi",
    "Kwara","Lagos",
    "Nassarawa","Niger",
    "Ogun","Ondo",
    "Osun","Oyo",
    "Plateau","Rivers",
    "Sokoto","Taraba",
    "Yobe","Zamfara","FCT"
    ]

    
career_choices = [
    ('Skill', 'Skill'),
    ('AC Technician', 'AC Technician'),
    ('Aluminium Tech', 'Aluminium Tech'),
    ('Building Engineer', 'Building Engineer'),
    ('Car Engineer', 'Car Engineer'),
    ('Caterer', 'Caterer'),
    ('Developer', 'Developer'),
    ('Electrician/Installer', 'Electrician/Installer'),
    ('Furniture/Roofer', 'Furniture/Roofer'),
    ('Gen Engineer', 'Gen Engineer'),
    ('Hair Stylist/Nail Tech', 'Hair Stylist/Nail Tech'),
    ('Movers/Loader', 'Movers/Loader'),
    ('Phone Technician', 'Phone Technician'),
    ('Plumber', 'Plumber'),
    ('Surveyor', 'Surveyor'),
    ('Welder', 'Welder')
]

#Forms setup
class LoginForm(FlaskForm):
    email = StringField(label='Email', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField('Log in')
    
class RegisterForm(FlaskForm):
    first_name = StringField(label='First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField(label='Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField(label='Email', validators=[DataRequired(), Email()])
    referral = SelectField(label='How did you hear about us?', choices=[('none', 'none'), ('Social media', 'Social media'), ('A Friend', 'A Friend'), ('Advert', 'Advert'),('Agent','Agent')])
    image = FileField(label='Image')
    password = PasswordField(label='Password', validators=[DataRequired()])
    re_password = PasswordField(label='Confirm Password', validators=[DataRequired(), EqualTo('password', message="password must match")])
    submit = SubmitField('Register')

class TechnicianForm(FlaskForm):
    shop_name = StringField("Shop Name", validators=[DataRequired(), Length(min=2, max=50)])
    career = SelectField('Career', choices=career_choices, validators=[DataRequired()])
    state = SelectField('State', choices=[(s, s) for s in states], validators=[DataRequired()])
    contact = StringField("Contact")
    working_hours = StringField("Working Hours", validators=[DataRequired()])
    image = FileField(label="Image")
    latitude = HiddenField()
    longitude = HiddenField()

    submit = SubmitField("Create Profile")

class BioForm(FlaskForm):
    bio = TextAreaField(label='Bio')
    submit = SubmitField(label='Post')
    
class EmailEditForm(FlaskForm):
    email = StringField(label='EMAIL', validators=[DataRequired(), Email()])
    submit = SubmitField(label='Verify Email')

class VerifyForm(FlaskForm):
    code = IntegerField(label='Enter Code Sent to Your Mail', validators=[DataRequired()])
    submit = SubmitField(label='Verify')

class AppealForm(FlaskForm):
    image = FileField(label="Upload a photo of you.", validators=[DataRequired()])
    id = FileField(label="Upload a government ID")
    submit = SubmitField(label='submit')

class ProductForm(FlaskForm):
    name = StringField(label='Enter Product Name', validators=[DataRequired()])
    image = MultipleFileField(label='Photos', validators=[DataRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    price = StringField(label='Product Price', validators=[DataRequired()])
    state = SelectField(label='State', choices=[(s, s) for s in states], validators=[DataRequired()])
    category = SelectField(label='Category', choices=[('Fashion', 'Fashion'),('Electronics', 'Electronics'),('Accessories', 'Accessories'),('Equipment', 'Equipment'),('Automobile', 'Automobile'),('Mobile Phone', 'MObile Phone'),('Lands/Buildings', 'Lands/Buildings')])
    label = SelectField(label='Product Review', choices=[('Brand New', 'Brand New'), ('Fairly Used', 'Fairly Used'), ('For Lease', 'For Lease'), ('For Sale', 'For Sale'), ('Other', 'Other')], validators=[DataRequired()])
    negotiable = SelectField(label='Price Negotiable', choices=[('Yes', 'Yes'), ('No', 'No')], validators=[DataRequired()])
    contact = StringField(label='Contact', validators=[DataRequired()])
    submit = SubmitField(label='Post')
    latitude = HiddenField()
    longitude = HiddenField()
    
    
class FeedbackForm(FlaskForm):
   # review = CKEditorField(label="Review", validators=[DataRequired()])
    review = StringField(label="Review", validators=[DataRequired()])
    submit = SubmitField(label="Submit")

def calculate_distance(lat1,lon1,lat2,lon2):
    R = 6371
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    
    a = (math.sin(dlat/2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

@app.route("/google-login")
def google_login():

    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    info = resp.json()

    email = info["email"]
    name = info["name"]
    
    
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, name=name, provider="google")
        db.session.add(user)
        db.session.commit()

    login_user(user)

    return redirect(url_for("dashboard"))

@app.route("/add_product", methods=["POST", "GET"])
def add_product():
    post = Product.query.filter_by(is_suspended = True).all()
    form = ProductForm()
    data = User.query.all()
    tech = Technicians.query.all()
    suspended_tech = Technicians.query.filter_by(is_suspended = True).all()
    if form.validate_on_submit():
        photo = request.files.getlist("image")
        
        saved_files = []

        for i, file in enumerate(photo):
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                saved_files.append(filename)
                
        profile_image = saved_files[0] if saved_files else None
        gallery_images = saved_files if len(saved_files) > 1 else []
            
        new_product = Product(
        name=form.name.data,
        image=profile_image,
        price=form.price.data,
        state=form.state.data,
        category=form.category.data,
        label=form.label.data,
        negotiable=form.negotiable.data,
        contact=form.contact.data,
        product_id=current_user.id,
        latitude=float(form.latitude.data) if form.latitude.data else None,
        longitude=float(form.longitude.data) if form.longitude.data else None,  
        gallery=gallery_images
        )
        
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('s_l'))
    return render_template("add.html", data=data, suspended_tech=suspended_tech, tech=tech, post=post, active_page="add_product", form=form, logged_in=current_user.is_authenticated)

@app.route("/appeal/<int:id>", methods=["GEt", "POST"])
@login_required
def appeal(id):
    form = AppealForm()
    product = db.session.execute(db.select(Product).where(Product.id == id)).scalar()

    if form.validate_on_submit():

        image = request.files["image"]
        filename = None
        if image and image.filename != '':

            filename = secure_filename(image.filename)
            file_ext = os.path.splitext(filename)[1]

            if file_ext not in app.config["ALLOWED_EXTENSION"]:
                flash('image file not recognise')
                return redirect(url_for('appeal'))
            
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_appeal = Appeal(
            image=filename,
            post=product
        )
        db.session.add(new_appeal)
        db.session.commit()
        return redirect(url_for('profile_page', profile=current_user.email))
    return render_template("appeal.html", form=form, post=product)

@app.route('/edit_bio/<shopname>', methods=["GET", "POST"])
@login_required
def bio_edit(shopname):
    form = BioForm()
    tech = db.session.execute(db.select(Technicians).where(Technicians.shop_name == shopname)).scalar()
    if form.validate_on_submit():
        tech.bio = form.bio.data
        db.session.commit()
        return redirect(url_for('profile_view', name=tech.shop_name))
    return render_template('bio.html', form=form, user=tech)

@app.route("/confirm_delete")
def confirm():
    flash("Logged Out Successfully")
    return render_template('confirm.html')

@app.route("/clear/<int:id>")
@admin_only
def clear(id):
    report = db.session.execute(db.select(Reported).where(Reported.post_id == id)).scalars().all()
    post_un_suspend = Product.query.get_or_404(id)
    appeal = db.session.execute(db.select(Appeal).where(Appeal.appeal_id == id)).scalar()
    post_un_suspend.is_suspended = False
    for rep in report:
        db.session.delete(rep)
    db.session.delete(appeal)
    db.session.commit()
    return redirect(url_for('get_post'))

@app.route("/clear_tech/<int:id>")
@admin_only
def clear_tech(id):
    report = db.session.execute(db.select(Reported).where(Reported.tech_id == id)).scalars().all()
    tech_un_suspend = Technicians.query.get_or_404(id)
    appeal = db.session.execute(db.select(Appeal).where(Appeal.tech_id == id)).scalar()
    tech_un_suspend.is_suspended = False
    for rep in report:
        db.session.delete(rep)
    if appeal:
        db.session.delete(appeal)
    db.session.commit()
    return redirect(url_for('suspended_tech'))

@app.route("/create_tech", methods=["GET", "POST"])
#@login_required
def create_tech():
    form = TechnicianForm()
    data = User.query.all()
    tech = Technicians.query.all()
    suspended_tech = Technicians.query.filter_by(is_suspended = True).all()
    post = Product.query.filter_by(is_suspended=True).all()
    if current_user.is_authenticated:
        profiles = db.session.execute(db.select(Technicians).where(Technicians.email == current_user.email)).scalars().all()
    else:
        flash('login to create a profile')
    if form.validate_on_submit():
        photo = request.files["image"]
        filename = None
        
        if photo and photo.filename != '':
            filename = secure_filename(photo.filename)
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config["ALLOWED_EXTENSION"]:
                flash("image file not recognise")
                return redirect(url_for('create_tech'))
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        if len(profiles) >= 2:
            flash("Maximum profile per user reached")
            return redirect(url_for('create_tech'))
            
        new_tech = Technicians(
            shop_name=form.shop_name.data,
            career=form.career.data,
            state=form.state.data,
            contact=form.contact.data,
            image=filename,
            email=current_user.email,
            working_hours=form.working_hours.data,
            latitude=float(form.latitude.data) if form.latitude.data else None,
            longitude=float(form.longitude.data) if form.longitude.data else None,
            user_id=current_user.id
        )

        db.session.add(new_tech)
        db.session.commit()

        return redirect(url_for("home"))
    return render_template('create_tech.html', data=data, tech=tech, suspended_tech=suspended_tech, post=post, form=form, logged_in=current_user.is_authenticated)  

@app.route("/delete")
@login_required
def delete():
    name = request.args.get("name")
    data = Technicians.query.filter_by(shop_name=name).first_or_404()
    db.session.delete(data)
    db.session.commit()
    return redirect(url_for('get_user'))
  
@app.route("/delete_post/<int:id>")
def delete_post(id):
    post_to_delete = db.session.execute(db.select(Product).where(Product.id == id)).scalar()
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('s_l'))

@app.route("/delete_user/<path:name>")
@login_required
def delete_user(name):
    user = db.session.execute(db.select(User).where(User.email == name)).scalar()
    if not user:
        return "user not found"
    post = Product.query.filter_by(product_id=user.id).all()
    tech = Technicians.query.filter_by(user_id=user.id).all()
    report = Reported.query.filter_by(user_id=user.id).scalar()
    review = Reviews.query.filter_by(user_id=user.id).all()
    if review:
        for r in review:
            if r:
                db.session.delete(r)
    if post:
        for p in post:
            if p:
                db.session.delete(p)
    if tech:
        for t in tech:
            if t:
                db.session.delete(t)
    if report:
        db.session.delete(report)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('get_accounts'))
    
@app.route("/edit_email/<email>", methods={"GET", "POST"})
@login_required
def email_edit(email):
    user = db.session.execute(db.select(User).where(User.email == email)).scalar()
    form = EmailEditForm()

    if form.validate_on_submit():
        if user.is_verified == True:
            user.is_verified = False
        email = form.email.data
        user.email = email
        db.session.commit()
        return redirect(url_for('send_verification_email', email=current_user.email))
    return render_template("email_edit.html", form=form, user=user) 

@app.route("/request_user")
@admin_only
def get_accounts():
    post = Product.query.filter_by(is_suspended=True).all()
    tech = Technicians.query.all()
    data = User.query.all()
    suspended_tech = Technicians.query.filter_by(is_suspended=True).all()
    return render_template('get_accounts.html', data=data, suspended_tech=suspended_tech, tech=tech, post=post)
    
@app.route("/restore_post")
@login_required
@admin_only
def get_post():
    reporters = []
    data = User.query.all()
    tech = Technicians.query.all()
    post = Product.query.filter_by(is_suspended= True ).all()
    suspended_tech = Technicians.query.filter_by(is_suspended=True).all()
    #post_get = db.session.execute(db.select(Appeal).where(Appeal.appeal_id == data.id)).scalar()

    for p in post:
        reporters = Reported.query.filter_by(post_id=p.id).all()

    return render_template('get_post.html', post=post, data=data,suspended_tech=suspended_tech, tech=tech, report=reporters)
  
@app.route("/request")
@admin_only
def get_user():
    data = User.query.all()
    post = Product.query.filter_by(is_suspended=True).all()
    tech = Technicians.query.all()
    suspended_tech = Technicians.query.filter_by(is_suspended=True).all()
    return render_template('get_user.html', suspended_tech=suspended_tech, data=data, tech=tech, post=post)
    
@app.route("/home")
def home():
    year = dt.datetime.now().year
    data = User.query.all()
    tech = Technicians.query.all()
    posts = Product.query.filter_by(is_suspended=False).all()
    post = Product.query.filter_by(is_suspended=True).all()
    suspended_tech = Technicians.query.filter_by(is_suspended= True).all()
    accessories = [ p for p in posts if p.category == "Accessories"]
    fashion = [p for p in posts if p.category == "Fashion"]
    electronics = [p for p in posts if p.category == "Electronics"]
    equipment = [p for p in posts if p.category == "Equipment"]
    automobile = [p for p in posts if p.category == "Automobile"]
    mobile_phone =[p for p in posts if p.category == "Mobile Phone"]
    land = [p for p in posts if p.category == "Lands/Buildings"]

    return render_template("index.html",
        year=year,
        electronics=electronics,
        automobile=automobile,
        mobile=mobile_phone,
        lands=land,
        equipment=equipment, 
        accessories=accessories, 
        fashion=fashion, 
        posts=posts, 
        suspended_tech=suspended_tech, 
        post=post, 
        data=data, 
        tech=tech, 
        logged_in=current_user.is_authenticated, 
        active_page="home")
    
    
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        result = db.session.execute(db.select(User).where(User.email == email)).scalar()
        data = result
        
        if not result:
            flash("incorrect credentials")
            return redirect(url_for('login'))
        else:
            if check_password_hash(data.password, password):
                login_user(data)
                return redirect(url_for("s_l"))
            else:
                flash("wrong credentials")
                return redirect(url_for('login'))
    return render_template("login.html", form=form)
  
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('confirm'))
    
@app.route("/product_view/<int:id>", methods=["GET", "POST"])
def product_view(id):
    form = FeedbackForm()
    product = db.session.execute(db.select(Product).where(Product.id == id)).scalar()
    product_review = db.session.execute(db.select(Reviews).where(Reviews.product_id == product.id)).scalars().all()
    gallery = product.gallery if product.gallery else []
    if form.validate_on_submit():
        reviews = Reviews(
        text=form.review.data,
        commenter_name=current_user,
        product_post=product
        )
        db.session.add(reviews)
        db.session.commit()
        return redirect(url_for('product_view', id=product.id))
    return render_template('product_view.html', reviews=product_review, form=form, product=product, gallery=gallery, gravatar=gravatar, logged_in=current_user.is_authenticated)
  
@app.route("/appeal/<int:id>", methods=["GEt", "POST"])
@login_required
def profile_appeal(id):
    form = AppealForm()
    tech = db.session.execute(db.select(Technicians).where(Technicians.id == id)).scalar()

    if form.validate_on_submit():

        image = request.files["image"]
        filename = None
        if image and image.filename != '':

            filename = secure_filename(image.filename)
            file_ext = os.path.splitext(filename)[1]

            if file_ext not in app.config["ALLOWED_EXTENSION"]:
                flash('image file not recognise')
                return redirect(url_for('appeal'))
            
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_appeal = Appeal(
            image=filename,
            tech=tech
        )
        db.session.add(new_appeal)
        db.session.commit()
        return redirect(url_for('profile_page', profile=current_user.email))
    return render_template("appeal.html", form=form, post=tech)

@app.route("/profile_page")
#@login_required
def profile_page():
    profile = db.session.execute(db.select(User).where(User.email == current_user.email)).scalar()
    posts = Product.query.filter_by(product_id=current_user.id).all()

    gallery = []
    for post in posts:
        if post.gallery:
            gallery.extend(post.gallery)
    return render_template("profile_page.html", active_page="profile_page", post=posts, gallery=gallery, profile=profile, logged_in=current_user.is_authenticated)

@app.route("/profile_view/<name>", methods=["GET", "POST"])
def profile_view(name):
    form = FeedbackForm()
    user_data = db.session.execute(db.select(Technicians).where(Technicians.shop_name == name)).scalar()
    p_id = user_data.id
    p_reviews = db.session.execute(db.select(Reviews).where(Reviews.profile_id == p_id)).scalars().all()
    
    if form.validate_on_submit():
        reviews = Reviews(
        text=form.review.data,
        commenter_name=current_user,
        tech_profile=user_data
        
        )
        db.session.add(reviews)
        db.session.commit()
        return redirect(url_for('profile_view', name=user_data.shop_name))
    return render_template("profile_view.html", form=form, post=p_reviews, data=user_data, gravatar=gravatar, logged_in=current_user.is_authenticated)

@app.route("/referral")
@login_required
@admin_only
def referral():
    data = User.query.all()
    tech = Technicians.query.all()
    post = Product.query.filter_by(is_suspended = True).all()
    suspended_tech = Technicians.query.filter_by(is_suspended = True).all()
    count = [ref["email"] for ref in data in ref.referral == 'none']
    a_friend = []
    social_media = []
    advert = []
    agent =[]
    for ref in data:
        if ref.referral == 'Social media':
            social_media.append(ref.email)
        elif ref.referral == 'A Friend':
            a_friend.append(ref.email)
        elif ref.referral == 'Advert':
            advert.append(ref.email)
        elif ref.referral == 'Agent':
            agent.append(ref.email)
    return render_template('referral.html', logged_in=current_user.is_authenticated, post=post, suspended_tech=suspended_tech, name=count, friend=a_friend, media=social_media, advert=advert, agent=agent, data=data, tech=tech)

@app.route("/register", methods=["GET", "POST"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        email = register_form.email.data
        password = register_form.password.data

        
        photo = request.files.get("image")
        filename = None
        
        if photo and photo.filename != '':
            filename = secure_filename(photo.filename)
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in app.config["ALLOWED_EXTENSION"]:
                flash("invalid file type")
                return redirect(url_for('register'))
            photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            #photo.save(os.path.join("static", photo.filename))
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        
        
        if user:
           flash("You've already signed up with that email, log in instead!")
           return redirect(url_for('login'))
        
        
        new_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
        
        new_user = User(
        firstname=register_form.first_name.data,
        lastname=register_form.last_name.data,
        referral=register_form.referral.data,
        image=filename,
        password=new_password,
        email=email
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("s_l"))
    return render_template("register.html", form=register_form)

@app.route("/auto_delete_post/<int:id>")
@login_required
def reported_post(id):

    reporter = Reported.query.filter_by(reporter=current_user, post_id=id).first()

    if not reporter:
        new_report = Reported(
        post_id=id, 
        reporter=current_user,
        reporter_name=current_user.firstname
        )
        db.session.add(new_report)
        db.session.commit()

    else:
        flash("you've created a report already and our team are working on it...")
        return redirect(url_for('s_l'))
    
    if Reported.query.filter_by(post_id=id).count() == 2:
        post_to_delete = Product.query.get_or_404(id)
        post_to_delete.is_suspended = True
        db.session.commit()
       
    return redirect(url_for('home'))
    
@app.route("/auto_delete_tech/<int:id>")
@login_required
def reported_tech(id):

    reporter = Reported.query.filter_by(reporter=current_user, tech_id=id).first()

    if not reporter:
        new_report = Reported(
        tech_id=id, 
        reporter=current_user,
        reporter_name=current_user.firstname
        )
        db.session.add(new_report)
        db.session.commit()

    else:
        flash("you've created a report already and our team are working on it...")
        return redirect(url_for('view_tech'))
    
    if Reported.query.filter_by(tech_id=id).count() == 2:
        suspend_profile = Technicians.query.get_or_404(id)
        suspend_profile.is_suspended = True
        db.session.commit()
       
    return redirect(url_for('view_tech'))

@app.route("/auto_delete_user/<int:id>")
@login_required
def reported_user(id):
    
    if Reported.query.filter_by(user_id=id).count() >= 2:
        user_to_delete = User.query.get_or_404(id)
        user_to_delete.is_suspended = True
        db.session.commit()
    return redirect(url_for('home'))

@app.route("/save-location", methods=["POST"])
@login_required
def save_location():
    data = request.get_json()
    user_lat = data.get("lat")
    user_lng = data.get("lng")
    
    technicians = db.session.execute(db.select(Technicians)).scalars().all()
    result = []
    
    for tech in technicians:
        if tech.latitude and tech.longitude:
            distance = calculate_distance(user_lat, user_lng, tech.latitude, tech.longitude)
            result.append({
                "name": tech.shop_name,
                "lat": tech.latitude,
                "lng": tech.longitude
            })
    #result.sort(key=lambdax:x(1))
    return render_template("save_location.html", user_lat=user_lat, user_lng=user_lng, technicians=result)
    
@app.route("/")
def s_l():
    today = date.today().toordinal()  # changes every day
    seed(today)

    product = Product.query.filter_by(is_suspended=False).order_by(func.random()).all()
    shuffle(product)
    
    return render_template("s&l.html",post=product, logged_in=current_user.is_authenticated)

@app.route("/suspended_tech")
@login_required
@admin_only
def suspended_tech():

    reporters = []
    data = User.query.all()
    tech = Technicians.query.all()
    post = Product.query.filter_by(is_suspended= True ).all()
    suspended = Technicians.query.filter_by(is_suspended=True).all()
    
    #post_get = db.session.execute(db.select(Appeal).where(Appeal.appeal_id == data.id)).scalar()
    
    for p in suspended:
        reporters = Reported.query.filter_by(tech_id=p.id).all()

    return render_template('suspended_tech.html', logged_in=current_user.is_authenticated, post=post, data=data, tech=tech, suspended_tech=suspended, report=reporters)
    
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
 
@app.route("/verify/<token>")
@login_required
def verify(token):

    try:
        email = confirm_token(token)
    except:
        flash('verification link expired')
        return redirect(url_for('profile_page'))
    
    user = User.query.filter_by(email=email).first()

    if user:
        if user.id == current_user.id:
            user.is_verified = True
            db.session.commit()
            flash("Email verified Successfully")
            return redirect(url_for('profile_page'))
        else:
            flash("You are not authorised")
            return redirect(url_for('home'))
    else:
        flash("No User found")
    return redirect(url_for("profile_page" ))

    
@app.route("/view/<name>")
def view(name):
    #name = request.args.get('name')
    return render_template('view.html', name=name)

@app.route('/view_appeal/<int:id>')
@login_required
def view_appeal(id):
    post_get = db.session.execute(db.select(Appeal).where(Appeal.appeal_id == id)).scalar()
    return render_template('view_appeal.html', post=post_get)

@app.route("/engineers")
def view_tech():
    user = Technicians.query.filter_by(is_suspended=False).all()
    if not current_user.is_authenticated:
        flash("login to view Technician profile")
    return render_template("repairs.html", prof=user, logged_in=current_user.is_authenticated)
   


   
if __name__=="__main__":
    app.run(debug=True)
                                                                                                                                
