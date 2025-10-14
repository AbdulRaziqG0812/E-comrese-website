from flask import Flask, render_template, request, redirect, url_for, flash
import os, time, random, string, json
from werkzeug.utils import secure_filename
import mysql.connector

app = Flask(__name__)
app.secret_key = "112233"

# -----------------------------
# Config
# -----------------------------
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'raziq12@',
    'database': 'e_comrece'
}

DEFAULT_IMAGE = 'uploads/default.jpg'

# -----------------------------
# Helpers
# -----------------------------
def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def unique_filename(filename):
    rnd = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    return f"{int(time.time())}_{rnd}_{secure_filename(filename)}"

def remove_file(filepath):
    if filepath and not filepath.endswith('default.jpg'):
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(filepath))
        if os.path.exists(full_path):
            os.remove(full_path)

# -----------------------------
# Routes
# -----------------------------

# Root route redirects to dashboard
@app.route('/')
def home():
    return redirect(url_for('dashboard'))


# Dashboard Route
@app.route('/dashboard')
def dashboard():
    conn = get_db()
    cursor = conn.cursor()
    
    # Total perfumes
    cursor.execute("SELECT COUNT(*) FROM perfumes")
    total_perfumes = cursor.fetchone()[0]
    
    # Total orders
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return render_template('admin/dashboard.html', total_perfumes=total_perfumes, total_orders=total_orders)


# -----------------------------
# Admin Panel - Perfumes
# -----------------------------
@app.route('/admin/admin')
def admin():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM perfumes ORDER BY id DESC")
    perfumes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/admin.html', perfumes=perfumes)

@app.route('/admin/perfume', methods=['GET', 'POST'])
def perfume():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '0').strip()
        sale_price = request.form.get('sale_price', '0').strip()
        stock = request.form.get('stock', '0').strip()
        category = request.form.get('category', 'Unisex').strip()

        if not name or not price:
            flash("❌ Name and Price required!")
            return redirect(request.url)

        try:
            price = float(price)
            sale_price = float(sale_price) if sale_price else 0.0
            stock = int(stock) if stock else 0
        except:
            flash("❌ Invalid numeric values!")
            return redirect(request.url)

        image = request.files.get('image')
        img_path = DEFAULT_IMAGE

        if image and allowed_file(image.filename):
            filename = unique_filename(image.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                image.save(save_path)
                img_path = f"uploads/{filename}"
            except Exception as e:
                flash(f"❌ Failed to save image: {e}")
                return redirect(request.url)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO perfumes (name, image, description, price, sale_price, stock, category) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (name, img_path, description, price, sale_price, stock, category)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("✅ Perfume added successfully!")
        return redirect(url_for('admin'))

    return render_template('admin/perfume.html')

@app.route('/admin/edit_perfume/<int:id>', methods=['GET','POST'])
def edit_perfume(id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM perfumes WHERE id=%s", (id,))
    perfume = cursor.fetchone()
    cursor.close()
    conn.close()

    if not perfume:
        flash("❌ Perfume not found!")
        return redirect(url_for('admin'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '0').strip()
        sale_price = request.form.get('sale_price', '0').strip()
        stock = request.form.get('stock', '0').strip()
        category = request.form.get('category', 'Unisex').strip()

        if not name or not price:
            flash("❌ Name and Price required!")
            return redirect(request.url)

        try:
            price = float(price)
            sale_price = float(sale_price) if sale_price else 0.0
            stock = int(stock) if stock else 0
        except:
            flash("❌ Invalid numeric values!")
            return redirect(request.url)

        img_path = perfume['image']
        image = request.files.get('image')
        if image and allowed_file(image.filename):
            filename = unique_filename(image.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                image.save(save_path)
                remove_file(perfume['image'])
                img_path = f"uploads/{filename}"
            except Exception as e:
                flash(f"❌ Failed to save image: {e}")
                return redirect(request.url)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE perfumes SET name=%s, image=%s, description=%s, price=%s, sale_price=%s, stock=%s, category=%s WHERE id=%s",
            (name, img_path, description, price, sale_price, stock, category, id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("✏️ Perfume updated successfully!")
        return redirect(url_for('admin'))

    return render_template('admin/edit_perfume.html', perfume=perfume)

@app.route('/delete/<int:id>')
def delete_perfume(id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT image FROM perfumes WHERE id=%s", (id,))
    perfume = cursor.fetchone()
    if perfume:
        remove_file(perfume['image'])
        cursor.execute("DELETE FROM perfumes WHERE id=%s", (id,))
        conn.commit()
        flash("🗑️ Perfume deleted successfully!")
    else:
        flash("❌ Perfume not found")
    cursor.close()
    conn.close()
    return redirect(url_for('admin'))

# -----------------------------
# Admin Orders Route
# -----------------------------
@app.route('/admin/orders')
def admin_orders():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/orders.html', orders=orders)

# -----------------------------
# User Checkout Route
# -----------------------------
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        city = request.form.get('city')
        country = request.form.get('country')
        postal = request.form.get('postal')
        address = request.form.get('address')
        payment_method = "Cash on Delivery"

        items_json = request.form.get('items')
        try:
            items = json.loads(items_json)
        except:
            items = []

        total = sum([item['price']*item['quantity'] for item in items])

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO orders (user_name, email, phone, city, country, postal, address, items, total, payment_method) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (name, email, phone, city, country, postal, address, json.dumps(items), total, payment_method)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("✅ Order placed successfully! Admin will process it soon.")
        return redirect(url_for('home'))

    return render_template('user/checkout.html')

# -----------------------------
if __name__ == '__main__':
    app.run(host="192.168.100.23", port=5600, debug=True)
