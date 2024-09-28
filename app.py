from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from Authentication import Authentication
from payload import Payload
import random

app = Flask(__name__)
app.secret_key = '1c2416c5bc4eba1897aa21ac6b724ee7879199dd70d1967e'

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(email):
    user = User()
    user.id = email
    return user

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        awaypassword = request.form['awaypassword']
        status_login = Authentication().data_register(email,password,awaypassword)

        if status_login == 'Gmail is using':
            flash('Email đã được đăng ký!')
        else:
            if status_login == 'save success':
                flash('Đăng ký thành công! Bạn có thể đăng nhập ngay bây giờ.')
            else:
                flash('Mật Khẩu Nhập Lại Không Giống')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        status_login = Authentication().data_login(email, password)
        if status_login == 'Login Success':
            user = User()
            user.id = email
            login_user(user)
            return redirect(url_for('home_page'))
        else:
            flash('Thông tin đăng nhập không chính xác!')
    return render_template('login.html')

login_manager.login_view = 'login'

@app.route('/home_page')
@login_required
def home_page():
    return render_template('home_page.html')

@app.route('/document')
@login_required
def document():
    return render_template('document.html')

@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.route('/payment')
@login_required
def payment():
    # Lấy thông tin từ `current_user`
    user_email = current_user.id

    # Lấy dữ liệu thanh toán từ URL nếu có
    speed = request.args.get('speed', 'Tối Đa 2 Gbps')
    storage = request.args.get('storage', '512 GB')
    device_limit = request.args.get('device_limit', 'Id: 2 Thiết Bị/Gói')
    support = request.args.get('support', 'ADR - IOS')
    price = request.args.get('price', '10,000đ')

    order_id_buy = generate_order_id()
    order_id = datetime.now().strftime("%Y%m%d%H%M%S")
    order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Thông tin gói thanh toán
    package_info = {
        'name': 'Gói VIP',
        'speed': speed,
        'data': storage,
        'devices': device_limit,
        'support': support,
        'sms': 'VINA Soạn YT30 gửi 888',
        'price': price,
        'order_id_buy':order_id_buy
    }

    # Lưu thông tin thanh toán của người dùng vào session hoặc cơ sở dữ liệu
    session['payment_user'] = {
        'email': user_email,
        'order_id': order_id,
        'package': package_info,
        'time': order_time,
    }

    # Render thông tin thanh toán lên trang web
    return render_template('payment.html', order_id_buy=order_id_buy, order_id=order_id, order_time=order_time, package=package_info)

def generate_order_id():
    time_component = datetime.now().strftime("%Y%m%d%H%M%S")
    random_component = ''.join([str(random.randint(0, 9)) for _ in range(10)])
    return time_component + random_component

@app.route('/QR')
@login_required
def QR():
    # Lấy thông tin từ session
    payment_info = session.get('payment_user')
    print(payment_info['email'])

    type = payment_info['package']['name']
    order_id = payment_info['package']['order_id_buy']
    price = payment_info['package']['price']

    user_email = current_user.id
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")

    data = Payload().payload(current_time,user_email,type,order_id)
    print(data)
    try:
        if data['paying']:
            for i in range(len(data['paying'])):
                if payment_info['package']['name'] == data['paying'][i]['type']:
                    order_time = data['paying'][i]['datetime']
                    order_id_buy = data['paying'][i]['order_id_buy']
            
        else:
            order_time = data['datetime']
            order_id_buy = data['order_id_buy']
        order_time = datetime.strptime(order_time, '%Y-%m-%d %H:%M:%S')
        time_remaining = (order_time + timedelta(minutes=30)) - now
        
        # Nếu thời gian còn lại nhỏ hơn 0 thì gán bằng 0
        if time_remaining.total_seconds() < 0:
            time_remaining_seconds = 0
        else:
            time_remaining_seconds = int(time_remaining.total_seconds())
    except:
        order_time = data['datetime']
        order_id_buy = data['order_id_buy']
        time_remaining_seconds = 1800
    
    return render_template('QR.html', time_remaining_seconds=time_remaining_seconds, package_info=order_id_buy,price=price)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
