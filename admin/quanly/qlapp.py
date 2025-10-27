from flask import Flask, render_template, request, redirect, url_for, flash, session
from db import ket_noi_csdl
from werkzeug.security import generate_password_hash, check_password_hash
import threading, webbrowser

app = Flask(__name__)
app.secret_key = "super_secret_key"

@app.route('/')
def home():
    if 'user_name' in session:
        if session['user_role'] == 'admin':
            return redirect(url_for('dashboard'))
        return f"<h2>Chào mừng, {session['user_name']}!</h2><br><a href='/logout'>Đăng xuất</a>"
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_role' not in session or session['user_role'] != 'admin':
        flash("❌ Bạn không có quyền truy cập Dashboard!", "danger")
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = ket_noi_csdl()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['user_role'] = user['role']  # admin, recruiter, applicant
            flash("✅ Đăng nhập thành công!", "success")
            return redirect(url_for('home'))
        else:
            flash("❌ Sai email hoặc mật khẩu!", "danger")
            return redirect(url_for('login'))

    return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'applicant')  

        conn = ket_noi_csdl()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            flash("Email đã tồn tại!", "danger")
        else:
            password_hash = generate_password_hash(password)
            cur.execute(
                "INSERT INTO users (full_name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                (full_name, email, password_hash, role)
            )
            conn.commit()
            flash("✅ Đăng ký thành công! Mời bạn đăng nhập.", "success")
            conn.close()
            return redirect(url_for('login'))
        conn.close()

    return render_template("register.html")

@app.route('/logout')
def logout():
    session.clear()
    flash("Đã đăng xuất!", "info")
    return redirect(url_for('login'))

# ----------------- USERS (ADMIN) -----------------
@app.route('/admin/users')
def users():
    if 'user_role' not in session or session['user_role'] != 'admin':
        flash("❌ Bạn không có quyền!", "danger")
        return redirect(url_for('login'))

    filter_role = request.args.get('role')
    conn = ket_noi_csdl()
    cur = conn.cursor(dictionary=True)

    if filter_role:
        cur.execute("SELECT * FROM users WHERE role=%s ORDER BY id ASC", (filter_role,))
    else:
        cur.execute("SELECT * FROM users ORDER BY id ASC")

    data = cur.fetchall()
    conn.close()
    return render_template('users.html', users=data, filter_role=filter_role)

@app.route('/admin/users/add', methods=['POST'])
def add_user():
    if 'user_role' not in session or session['user_role'] != 'admin':
        flash("❌ Bạn không có quyền!", "danger")
        return redirect(url_for('login'))

    full_name = request.form['full_name']
    email = request.form['email']
    password = request.form['password']
    role = request.form['role']

    conn = ket_noi_csdl()
    cur = conn.cursor()
    password_hash = generate_password_hash(password)
    cur.execute(
        "INSERT INTO users (full_name, email, password_hash, role) VALUES (%s,%s,%s,%s)",
        (full_name, email, password_hash, role)
    )
    conn.commit()
    conn.close()
    flash("✅ Đã thêm người dùng mới!", "success")
    return redirect(url_for('users'))

@app.route('/admin/users/fix/<email>', methods=['GET','POST'])
def fix_user(email):
    if 'user_role' not in session or session['user_role'] != 'admin':
        flash("❌ Bạn không có quyền!", "danger")
        return redirect(url_for('login'))

    conn = ket_noi_csdl()
    cur = conn.cursor(dictionary=True)

    if request.method == 'POST':
        full_name = request.form['full_name']
        password = request.form['password']
        role = request.form['role']
        password_hash = generate_password_hash(password)
        cur.execute(
            "UPDATE users SET full_name=%s, password_hash=%s, role=%s WHERE email=%s",
            (full_name, password_hash, role, email)
        )
        conn.commit()
        flash("✅ Đã sửa người dùng!", "success")
        conn.close()
        return redirect(url_for('users'))

    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    conn.close()
    if not user:
        flash("❌ Người dùng không tồn tại!", "danger")
        return redirect(url_for('users'))
    return render_template('fix.html', user=user)

@app.route('/admin/users/delete/<email>')
def delete_user(email):
    if 'user_role' not in session or session['user_role'] != 'admin':
        flash("❌ Bạn không có quyền!", "danger")
        return redirect(url_for('login'))

    conn = ket_noi_csdl()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE email=%s", (email,))
    conn.commit()
    conn.close()
    flash("🗑️ Đã xóa người dùng!", "success")
    return redirect(url_for('users'))

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/login")  

if __name__ == '__main__':
    threading.Timer(1.0, open_browser).start()
    app.run(debug=True)
