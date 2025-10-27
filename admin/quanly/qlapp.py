from flask import Flask, render_template, request, redirect, url_for, flash, session
from db import ket_noi_csdl
import webbrowser
import threading

app = Flask(__name__)
app.secret_key = "super_secret_key"

@app.route('/')
def home():
    if 'user_name' in session:
        if session['user_status'] == 1:
            return redirect(url_for('dashboard'))
        return f"<h2>Chào mừng, {session['user_name']}!</h2><br><a href='/logout'>Đăng xuất</a>"
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_status' not in session or session['user_status'] != 1:
        flash("❌ Bạn không có quyền truy cập Dashboard!", "danger")
        return redirect(url_for('login'))
    return render_template('index.html')

# ===== Login =====
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = ket_noi_csdl()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM user WHERE name=%s AND pass=%s", (username, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_status'] = user['status']  # 0=User,1=Admin,2=CTV
            flash("✅ Đăng nhập thành công!", "success")
            return redirect(url_for('home'))
        else:
            flash("❌ Sai tên đăng nhập hoặc mật khẩu!", "danger")
            return redirect(url_for('login'))

    return render_template("login.html")

# ===== Register =====
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        conn = ket_noi_csdl()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM user WHERE name=%s", (username,))
        existing_user = cur.fetchone()

        if existing_user:
            flash("Tên đăng nhập đã tồn tại!", "danger")
        else:
            cur.execute(
                "INSERT INTO user (name, mail, pass, status) VALUES (%s, %s, %s, %s)",
                (username, email, password, 0)
            )
            conn.commit()
            flash("✅ Đăng ký thành công! Mời bạn đăng nhập.", "success")
            return redirect(url_for('login'))
        conn.close()

    return render_template("register.html")

# ===== Logout =====
@app.route('/logout')
def logout():
    session.clear()
    flash("Đã đăng xuất!", "info")
    return redirect(url_for('login'))

# ===== Quản lý user (chỉ admin) =====
@app.route('/admin/users')
def users():
    if 'user_status' not in session or session['user_status'] != 1:
        flash("❌ Bạn không có quyền truy cập!", "danger")
        return redirect(url_for('login'))

    filter_status = request.args.get('status', type=int)  
    conn = ket_noi_csdl()
    cur = conn.cursor(dictionary=True)
    
    if filter_status is not None:
        cur.execute("SELECT * FROM user WHERE status=%s ORDER BY id ASC", (filter_status,))
    else:
        cur.execute("SELECT * FROM user ORDER BY id ASC")
    
    data = cur.fetchall()
    conn.close()
    return render_template('users.html', users=data, filter_status=filter_status)

@app.route('/admin/users/add', methods=['POST'])
def add_user():
    if 'user_status' not in session or session['user_status'] != 1:
        flash("❌ Bạn không có quyền!", "danger")
        return redirect(url_for('login'))

    name = request.form['name']
    email = request.form['mail']
    password = request.form['pass']
    status = request.form['status']

    conn = ket_noi_csdl()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO user (name, mail, pass, status) VALUES (%s,%s,%s,%s)",
        (name, email, password, status)
    )
    conn.commit()
    conn.close()
    flash("✅ Đã thêm người dùng mới!", "success")
    return redirect(url_for('users'))

@app.route('/admin/users/fix/<mail>')
def fix_user_page(mail):
    if 'user_status' not in session or session['user_status'] != 1:
        flash("❌ Bạn không có quyền!", "danger")
        return redirect(url_for('login'))

    conn = ket_noi_csdl()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM user WHERE mail=%s", (mail,))
    user = cur.fetchone()  
    conn.close()
    if not user:
        flash("❌ Người dùng không tồn tại!", "danger")
        return redirect(url_for('users'))
    return render_template('fix.html', user=user)

@app.route('/admin/users/fix', methods=['POST'])
def fix_user():
    if 'user_status' not in session or session['user_status'] != 1:
        flash("❌ Bạn không có quyền!", "danger")
        return redirect(url_for('login'))

    name = request.form['name']
    email = request.form['mail']
    password = request.form['pass']
    status = int(request.form['status'])

    conn = ket_noi_csdl()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE user SET name=%s, `pass`=%s, status=%s WHERE mail=%s",
            (name, password, status, email)
        )
        conn.commit()
        flash("✅ Đã sửa người dùng", "success")
    except Exception as e:
        flash(f"❌ Lỗi khi sửa người dùng: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('users'))

@app.route('/admin/users/delete/<mail>')
def delete_user(mail):
    if 'user_status' not in session or session['user_status'] != 1:
        flash("❌ Bạn không có quyền!", "danger")
        return redirect(url_for('login'))

    conn = ket_noi_csdl()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM user WHERE mail=%s", (mail,))
        conn.commit()
        flash("🗑️ Đã xóa người dùng thành công!", "danger")
    except Exception as e:
        flash(f"❌ Lỗi khi xóa người dùng: {e}", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('users'))

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/login")  

if __name__ == '__main__':
    threading.Timer(1.0, open_browser).start()
    app.run(debug=True)
