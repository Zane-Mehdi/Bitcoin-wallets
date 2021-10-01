from flask import Flask,render_template,flash,request,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required,logout_user,current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from bit import PrivateKey

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///mydb.db'
db = SQLAlchemy(app)
app.config['SECRET_KEY']='SUPERSECRETKEY'
app.config['TRANSACTON_PERCENTAGE']=1
app.config['COMPANY_ADDRESS']='34234234324 '
login_manager = LoginManager(app)




class User(db.Model,UserMixin):
    id=db.Column(db.Integer,primary_key=True)
    username= db.Column(db.String(50),unique=True)
    password=db.Column(db.String(50),nullable=False)
    wallet=db.Column(db.String(1000),nullable=False)
    address = db.Column(db.String(100),nullable=False)
    amount = db.Column(db.String(1000),default=0)
    email = db.Column(db.String(1000), nullable=False)


admin=Admin(app,name='name',template_mode='bootstrap3')
admin.add_view(ModelView(User,db.session))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def getbalance(wallet):
    key = PrivateKey(wallet)
    newbalance = key.balance_as('usd')
    user=User.query.filter_by(wallet=wallet)
    user.amount = newbalance
    db.session.commit()



@app.route('/')
def home():
    if current_user.is_authenticated:
        getbalance(current_user.wallet)

    return render_template('index.html')


@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('index.html')

@app.route('/signup',methods=['POST','GET'])
def signup():
    if request.method == 'POST' and request.form.get('username') and request.form.get('password') and request.form.get('email'):
        
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        if User.query.filter_by(username=username).first():
            flash('username taken')
            return render_template('signup.html')
        else:    
            wallet = PrivateKey()
            user = User(username=username, email=email,password=password,address=wallet.address,wallet=wallet.to_wif())
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))

    elif request.method == 'POST':
        flash('check your input')
        return render_template('signup.html')

    else:
        return render_template('signup.html')


@app.route('/login',methods=['POST','GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST' and request.form.get('username') and request.form.get('password'):
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            user = User.query.filter_by(username=username).first()
            if user.password == password:
                login_user(user)
                flash('YOU ARE NOW LOGGED IN')
                return redirect(url_for('home'))
            else: 
                flash('wrong Password')
                return render_template('login.html')
        else:
            flash('USER DOES NOT EXIST')
            return render_template('login.html')

        flash('THIS IS A MESSAGE')
    return render_template('login.html')

def createuser(username,password):
    user = User(username=username,password=password)
    db.session.add(user)
    db.session.commit()

@app.route('/createtransaction',methods=['POST','GET'])
@login_required
def transact():
    getbalance(current_user.wallet)
    if request.method == 'POST' and request.form.get('address') and request.form.get('amount'):
        address = request.form.get('address')
        amount = request.form.get('amount')
        if int(current_user.wallet) < int(amount):
            flash('not enough funds')
            return render_template('transact.html')
        
        key = PrivateKey(current_user.wallet)
        myamount = (app.config['TRANSACTON_PERCENTAGE']/100)*amount
        youramount = amount - myamount
        transactionid=key.send([(address,youramount,'usd'),(app.config['COMPANY_ADDRESS'],myamount,'usd')])
        flash(f'transaction succeeeded + transaction id ={transactionid}')
        return render_template('transact.html')
    return render_template('transact.html')


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
