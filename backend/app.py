import os, calendar
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps
import jwt
from flask import Flask, jsonify, request, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'mysql+pymysql://family_user:change_me@db:3306/family_finance?charset=utf8mb4'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={'pool_pre_ping': True},
    SECRET_KEY=os.getenv('SECRET_KEY', 'change-this-secret')
)
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__='users'
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(120), nullable=False)
    email=db.Column(db.String(190), unique=True, nullable=False)
    password_hash=db.Column(db.String(255), nullable=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Business(db.Model):
    __tablename__='businesses'
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(100), unique=True, nullable=False)
    business_type=db.Column(db.String(30), nullable=False, default='business')
    active=db.Column(db.Boolean, default=True, nullable=False)

class Category(db.Model):
    __tablename__='categories'
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(100), nullable=False)
    transaction_type=db.Column(db.Enum('income','expense'), nullable=False)
    business_id=db.Column(db.Integer, db.ForeignKey('businesses.id'))
    active=db.Column(db.Boolean, default=True, nullable=False)

class Income(db.Model):
    __tablename__='income'
    id=db.Column(db.Integer, primary_key=True)
    business_id=db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)
    category_id=db.Column(db.Integer, db.ForeignKey('categories.id'))
    user_id=db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount=db.Column(db.Numeric(14,2), nullable=False)
    transaction_date=db.Column(db.Date, nullable=False, index=True)
    description=db.Column(db.String(255), default='')
    payment_method=db.Column(db.String(40), default='Cash')
    created_at=db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    business=db.relationship('Business'); category=db.relationship('Category'); user=db.relationship('User')

class Expense(db.Model):
    __tablename__='expenses'
    id=db.Column(db.Integer, primary_key=True)
    business_id=db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)
    category_id=db.Column(db.Integer, db.ForeignKey('categories.id'))
    user_id=db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount=db.Column(db.Numeric(14,2), nullable=False)
    transaction_date=db.Column(db.Date, nullable=False, index=True)
    description=db.Column(db.String(255), default='')
    payment_method=db.Column(db.String(40), default='Cash')
    created_at=db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    business=db.relationship('Business'); category=db.relationship('Category'); user=db.relationship('User')

def token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth=request.headers.get('Authorization','')
        if not auth.startswith('Bearer '): return jsonify(error='Authentication required'),401
        try:
            payload=jwt.decode(auth[7:],app.config['SECRET_KEY'],algorithms=['HS256'])
            g.user=db.session.get(User,int(payload['user_id']))
            if not g.user: raise ValueError()
        except Exception: return jsonify(error='Session expired. Please sign in again.'),401
        return fn(*args,**kwargs)
    return wrapper

def issue_token(user):
    return jwt.encode({'user_id':user.id,'exp':datetime.utcnow()+timedelta(hours=12)},app.config['SECRET_KEY'],algorithm='HS256')
def amt(v): return float(v or 0)
def fy_start(today=None):
    d=today or date.today(); return d.year if d.month>=4 else d.year-1
def transaction_json(r):
    return {'id':r.id,'business_id':r.business_id,'business_name':r.business.name,'category_id':r.category_id,'category_name':r.category.name if r.category else '', 'amount':amt(r.amount),'transaction_date':r.transaction_date.isoformat(),'description':r.description or '', 'payment_method':r.payment_method or 'Cash','created_by':r.user.name}
def parse_tx(data, model):
    try:
        amount=Decimal(str(data.get('amount','')))
        if amount<=0: raise ValueError()
    except Exception: raise ValueError('Amount must be greater than zero.')
    try: tx_date=date.fromisoformat(data.get('transaction_date',''))
    except Exception: raise ValueError('Please provide a valid transaction date.')
    try: bid=int(data.get('business_id',0))
    except Exception: bid=0
    if not db.session.get(Business,bid): raise ValueError('Select a valid income source.')
    cid=data.get('category_id') or None
    if cid:
        cat=db.session.get(Category,int(cid)); expected='income' if model is Income else 'expense'
        if not cat or cat.transaction_type!=expected: raise ValueError('Select a valid category.')
    return dict(business_id=bid,category_id=int(cid) if cid else None,user_id=g.user.id,amount=amount,transaction_date=tx_date,description=(data.get('description') or '').strip()[:255],payment_method=(data.get('payment_method') or 'Cash')[:40])

@app.get('/api/health')
def health():
    try: db.session.execute(db.text('SELECT 1')); return jsonify(status='healthy',database='connected')
    except Exception: return jsonify(status='unhealthy'),503
@app.post('/api/auth/login')
def login():
    d=request.get_json(silent=True) or {}; u=User.query.filter_by(email=(d.get('email') or '').lower().strip()).first()
    if not u or not check_password_hash(u.password_hash,d.get('password') or ''): return jsonify(error='Incorrect email or password.'),401
    return jsonify(token=issue_token(u),user={'id':u.id,'name':u.name,'email':u.email})
@app.get('/api/auth/me')
@token_required
def me(): return jsonify(user={'id':g.user.id,'name':g.user.name,'email':g.user.email})
@app.get('/api/businesses')
@token_required
def businesses(): return jsonify([{'id':b.id,'name':b.name,'business_type':b.business_type} for b in Business.query.filter_by(active=True).order_by(Business.id).all()])
@app.get('/api/categories')
@token_required
def categories():
    q=Category.query.filter_by(active=True); t=request.args.get('type')
    if t in ('income','expense'): q=q.filter_by(transaction_type=t)
    return jsonify([{'id':c.id,'name':c.name,'transaction_type':c.transaction_type,'business_id':c.business_id} for c in q.order_by(Category.name).all()])
def add_tx(model):
    try:
        row=model(**parse_tx(request.get_json(silent=True) or {},model)); db.session.add(row); db.session.commit(); return jsonify(transaction_json(row)),201
    except ValueError as e: db.session.rollback(); return jsonify(error=str(e)),400
    except Exception: db.session.rollback(); app.logger.exception('Save transaction failed'); return jsonify(error='Could not save transaction.'),500
@app.post('/api/income')
@token_required
def add_income(): return add_tx(Income)
@app.post('/api/expenses')
@token_required
def add_expense(): return add_tx(Expense)
def get_rows(model):
    q=model.query
    if request.args.get('start'): q=q.filter(model.transaction_date>=date.fromisoformat(request.args['start']))
    if request.args.get('end'): q=q.filter(model.transaction_date<=date.fromisoformat(request.args['end']))
    if request.args.get('business_id'): q=q.filter(model.business_id==int(request.args['business_id']))
    return [transaction_json(r) for r in q.order_by(model.transaction_date.desc(),model.id.desc()).limit(500).all()]
@app.get('/api/income')
@token_required
def list_income():
    try: return jsonify(get_rows(Income))
    except Exception: return jsonify(error='Invalid filter.'),400
@app.get('/api/expenses')
@token_required
def list_expenses():
    try: return jsonify(get_rows(Expense))
    except Exception: return jsonify(error='Invalid filter.'),400
def delete_tx(model,row_id):
    r=db.session.get(model,row_id)
    if not r: return jsonify(error='Record not found.'),404
    db.session.delete(r); db.session.commit(); return jsonify(message='Deleted')
@app.delete('/api/income/<int:row_id>')
@token_required
def del_income(row_id): return delete_tx(Income,row_id)
@app.delete('/api/expenses/<int:row_id>')
@token_required
def del_expense(row_id): return delete_tx(Expense,row_id)

@app.get('/api/dashboard')
@token_required
def dashboard():
    try: fy=int(request.args.get('fy',fy_start())); start=date(fy,4,1); end=date(fy+1,4,1)
    except Exception: return jsonify(error='Invalid financial year.'),400
    incs=db.session.query(Business.id,Business.name,db.func.coalesce(db.func.sum(Income.amount),0)).outerjoin(Income,(Income.business_id==Business.id)&(Income.transaction_date>=start)&(Income.transaction_date<end)).filter(Business.active.is_(True)).group_by(Business.id,Business.name).order_by(Business.id).all()
    exps=db.session.query(Business.id,db.func.coalesce(db.func.sum(Expense.amount),0)).outerjoin(Expense,(Expense.business_id==Business.id)&(Expense.transaction_date>=start)&(Expense.transaction_date<end)).filter(Business.active.is_(True)).group_by(Business.id).all()
    expmap={i:amt(v) for i,v in exps}; bdata=[]; total_i=total_e=0
    for bid,name,value in incs:
        i=amt(value); e=expmap.get(bid,0); total_i+=i; total_e+=e
        bdata.append({'business_id':bid,'business_name':name,'income':i,'expenses':e,'net':i-e})
    monthly=[]
    for offset in range(12):
        y=fy+(3+offset)//12; m=(3+offset)%12+1; ms=date(y,m,1); me=date(y+1,1,1) if m==12 else date(y,m+1,1)
        i=amt(db.session.query(db.func.coalesce(db.func.sum(Income.amount),0)).filter(Income.transaction_date>=ms,Income.transaction_date<me).scalar())
        e=amt(db.session.query(db.func.coalesce(db.func.sum(Expense.amount),0)).filter(Expense.transaction_date>=ms,Expense.transaction_date<me).scalar())
        monthly.append({'month':calendar.month_abbr[m],'income':i,'expenses':e,'net':i-e})
    return jsonify(financial_year=f'FY {fy}-{str(fy+1)[-2:]}',financial_year_start=start.isoformat(),financial_year_end=(end-timedelta(days=1)).isoformat(),total_income=total_i,total_expenses=total_e,net_balance=total_i-total_e,businesses=bdata,monthly=monthly,recent_income=[transaction_json(r) for r in Income.query.order_by(Income.transaction_date.desc()).limit(5)],recent_expenses=[transaction_json(r) for r in Expense.query.order_by(Expense.transaction_date.desc()).limit(5)])

def seed():
    if not User.query.first():
        db.session.add(User(name=os.getenv('ADMIN_NAME','Family Admin'),email=os.getenv('ADMIN_EMAIL','admin@family.local').lower(),password_hash=generate_password_hash(os.getenv('ADMIN_PASSWORD','ChangeThisPassword123!'))))
    if not Business.query.first():
        db.session.add_all([Business(name='Farming'),Business(name='Cow Milk Business'),Business(name='Poultry Business'),Business(name="Tushar's Salary",business_type='salary')]); db.session.commit()
    if not Category.query.first():
        b={x.name:x.id for x in Business.query.all()}; cats=[]
        for name,bn in [('Crop sales','Farming'),('Milk sales','Cow Milk Business'),('Egg sales','Poultry Business'),('Chicken sales','Poultry Business'),('Monthly salary',"Tushar's Salary"),('Bonus',"Tushar's Salary"),('Other income',None)]: cats.append(Category(name=name,transaction_type='income',business_id=b.get(bn) if bn else None))
        for name,bn in [('Seeds','Farming'),('Fertilizer','Farming'),('Pesticides','Farming'),('Labour','Farming'),('Tractor and fuel','Farming'),('Irrigation','Farming'),('Cattle feed','Cow Milk Business'),('Veterinary and medicines','Cow Milk Business'),('Dairy labour','Cow Milk Business'),('Electricity','Cow Milk Business'),('Chicks','Poultry Business'),('Poultry feed','Poultry Business'),('Vaccines and medicines','Poultry Business'),('Poultry labour','Poultry Business'),('Rent',"Tushar's Salary"),('Food',"Tushar's Salary"),('Travel',"Tushar's Salary"),('Personal expenses',"Tushar's Salary"),('Other expense',None)]: cats.append(Category(name=name,transaction_type='expense',business_id=b.get(bn) if bn else None))
        db.session.add_all(cats); db.session.commit()
with app.app_context():
    db.create_all(); seed()
