from flask import Flask, abort, jsonify, render_template, request, redirect, session, url_for, flash
import os, time, random, string, json
from werkzeug.utils import secure_filename
import mysql.connector
from flask_mail import Mail, Message


app = Flask(__name__)
app.secret_key = "112233"


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

app.config['MAIL_USERNAME'] = 'areezfragrances@gmail.com'
app.config['MAIL_PASSWORD'] = 'vzkh wcnl hiqh xyyu'  # 👈 yahan app password paste karo

mail = Mail(app)

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

@app.route('/')
@app.route('/home')
def home():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM perfumes ORDER BY id DESC")
    perfumes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', perfumes=perfumes)


# -----------------------------
# route for loginpage
# -----------------------------

@app.route('/loginpage', methods=['GET', 'POST'])
def loginpage():
    if request.method == 'POST':
        username = request.form.get('id')
        password = request.form.get('password')

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)

            # 1️⃣ Get user by username only
            cursor.execute("SELECT * FROM login WHERE username = %s", (username,))
            user = cursor.fetchone()

            # 2️⃣ Check if user exists and password matches (plain text)
            if user and user['password'] == password:
                # 3️⃣ Save session (login success)
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user.get('role', 'user')  # optional, if you use roles

                return redirect(url_for('dashboard'))
            else:
                flash("Invalid username or password!", "error")
                return redirect(url_for('loginpage'))

        except Exception as e:
            flash(f"Error: {e}", "error")
            return redirect(url_for('loginpage'))
        finally:
            cursor.close()
            conn.close()

    return render_template('loginpage.html')


# -----------------------------
# register route
# -----------------------------

REGISTER_KEY = "areez_fragrance_2025"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('fullname')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        entered_key = request.form.get('register_key')

        # 1️⃣ Check registration key
        if entered_key != REGISTER_KEY:
            flash("Invalid registration key!", "error")
            return redirect(url_for('register'))

        # 2️⃣ Check password match
        if password != confirm:
            flash("Passwords do not match!", "error")
            return redirect(url_for('register'))

        # 3️⃣ Check password strength
        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return redirect(url_for('register'))

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)

            # 4️⃣ Check duplicate username
            cursor.execute("SELECT * FROM login WHERE username = %s", (username,))
            existing_user = cursor.fetchone()
            if existing_user:
                flash("Username already exists. Please choose another.", "error")
                return redirect(url_for('register'))

            # 5️⃣ Insert into register table (plain text password)
            cursor.execute(
                "INSERT INTO register (username, email, password, confirm_password) VALUES (%s, %s, %s, %s)",
                (username, email, password, password)
            )

            # 6️⃣ Insert into login table (plain text password)
            cursor.execute(
                "INSERT INTO login (username, password) VALUES (%s, %s)",
                (username, password)
            )

            conn.commit()
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('loginpage'))

        except Exception as e:
            flash(f"Error: {e}", "error")
            return redirect(url_for('register'))

        finally:
            cursor.close()
            conn.close()

    return render_template("register.html")


# -----------------------------
# dashboard route
# -----------------------------

@app.route('/dashboard')
def dashboard():
    conn = get_db()
    cursor = conn.cursor()

    # 🧴 Total perfumes
    cursor.execute("SELECT COUNT(*) FROM perfumes")
    total_perfumes = cursor.fetchone()[0]

    # 📦 Total orders
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    # 💰 Total sales (sum of order totals)
    cursor.execute("SELECT IFNULL(SUM(total), 0) FROM orders")
    total_sales = cursor.fetchone()[0]

    # ⏳ Pending orders
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Pending'")
    pending_orders = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template(
        'dashboard.html',
        total_perfumes=total_perfumes,
        total_orders=total_orders,
        total_sales=total_sales,
        pending_orders=pending_orders
    )


# ---------------------------
# Admin Panel - Perfumes
# -----------------------------
@app.route('/admin')
def admin():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM perfumes ORDER BY id DESC")
    perfumes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin.html', perfumes=perfumes)


# -----------------------------
# 🧴 Add New Perfume
# -----------------------------

@app.route('/perfume', methods=['GET', 'POST'])
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
        return redirect(url_for('perfume'))

    return render_template('perfume.html')


# -----------------------------
# ✏️ Edit Perfume
# -----------------------------

@app.route('/edit_perfume/<int:id>', methods=['GET','POST'])
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

    return render_template('edit_perfume.html', perfume=perfume)


# -----------------------------
# 🗑️ Delete Perfume
# -----------------------------

@app.route('/delete_perfume/<int:id>')
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

@app.route('/orders')
def admin_orders():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = cursor.fetchall()

    # 🛠 Safely decode JSON from 'items' field
    for order in orders:
        try:
            items_value = order.get("items")

            # If items are stored as a JSON string → decode it
            if isinstance(items_value, str) and items_value.strip():
                order["items"] = json.loads(items_value)

            # If items are None or empty string → make empty list
            elif not items_value:
                order["items"] = []

            # If already a list/dict → keep as is
            elif isinstance(items_value, (list, dict)):
                order["items"] = items_value

            else:
                order["items"] = []

        except Exception as e:
            print(f"⚠️ JSON decode error for order {order.get('id')}: {e}")
            order["items"] = []

    cursor.close()
    conn.close()

    return render_template('orders.html', orders=orders)


# -----------------------------
# 🗑️ Delete Order (AJAX)
# -----------------------------

@app.route('/delete_order/<int:id>', methods=['DELETE'])
def delete_order(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM orders WHERE id = %s", (id,))
    db.commit()
    cursor.close()
    return jsonify({"success": True, "message": "🗑️ Order deleted successfully!"})


# -----------------------------
# ✅ Update Order Status (AJAX)
# -----------------------------
@app.route('/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({"error": "Missing 'status' in request"}), 400

    new_status = data['status']

    # ✅ Allowed statuses (added 'Returned')
    allowed_statuses = ['Pending', 'Processing', 'Shipped', 'Completed', 'Cancelled', 'Returned']
    if new_status not in allowed_statuses:
        return jsonify({"error": f"Invalid status. Allowed: {', '.join(allowed_statuses)}"}), 400

    conn = get_db()  # ✅ your function to get MySQL connection
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE orders SET status=%s WHERE id=%s", (new_status, order_id))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": f"Order ID {order_id} not found"}), 404

        return jsonify({
            "success": True,
            "message": f"✅ Order status updated to '{new_status}' successfully!"
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Error updating status: {str(e)}"}), 500

    finally:
        cursor.close()
        conn.close()


# -----------------------------
# 📊 AREEZ Admin Dashboard
# -----------------------------
@app.route('/report')
def report():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # 🗓️ Optional date filter
    from_date = request.args.get('from')
    to_date = request.args.get('to')

    # ✅ Safe query construction
    date_filter = ""
    params = []
    if from_date and to_date:
        date_filter = "WHERE DATE(created_at) BETWEEN %s AND %s"
        params = [from_date, to_date]

    try:
        # 🧾 Total Orders
        cursor.execute(f"SELECT COUNT(*) AS total_orders FROM orders {date_filter}", params)
        total_orders = cursor.fetchone()['total_orders'] or 0

        # 💰 Total Sales
        cursor.execute(f"SELECT IFNULL(SUM(total), 0) AS total_sales FROM orders {date_filter}", params)
        total_sales = cursor.fetchone()['total_sales'] or 0

        # ⏳ Pending Orders
        if date_filter:
            cursor.execute(f"""
                SELECT COUNT(*) AS pending_orders
                FROM orders
                {date_filter} AND status = 'Pending'
            """, params)
        else:
            cursor.execute("SELECT COUNT(*) AS pending_orders FROM orders WHERE status='Pending'")
        pending_orders = cursor.fetchone()['pending_orders'] or 0

        # 🔁 Returned Orders
        if date_filter:
            cursor.execute(f"""
                SELECT COUNT(*) AS returned_orders
                FROM orders
                {date_filter} AND status = 'Returned'
            """, params)
        else:
            cursor.execute("SELECT COUNT(*) AS returned_orders FROM orders WHERE status='Returned'")
        returned_orders = cursor.fetchone()['returned_orders'] or 0

        # 📈 Sales (current month or filtered)
        if from_date and to_date:
            cursor.execute("""
                SELECT DATE(created_at) AS date, SUM(total) AS total
                FROM orders
                WHERE DATE(created_at) BETWEEN %s AND %s
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at)
            """, (from_date, to_date))
        else:
            cursor.execute("""
                SELECT DATE(created_at) AS date, SUM(total) AS total
                FROM orders
                WHERE MONTH(created_at) = MONTH(CURDATE())
                  AND YEAR(created_at) = YEAR(CURDATE())
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at)
            """)
        sales_data = cursor.fetchall()
        sales_labels = [row['date'].strftime("%d %b") for row in sales_data if row['date']] if sales_data else []
        sales_values = [float(row['total']) for row in sales_data if row['total']] if sales_data else []

        # 🧾 Order Status Breakdown
        cursor.execute(f"SELECT status, COUNT(*) AS count FROM orders {date_filter} GROUP BY status", params)
        status_data = cursor.fetchall()
        status_labels = [row['status'] for row in status_data] if status_data else []
        status_counts = [row['count'] for row in status_data] if status_data else []

        # 🌸 Top Perfumes
        cursor.execute(f"SELECT items FROM orders {date_filter}", params)
        perfume_sales = {}
        for row in cursor.fetchall():
            try:
                items = json.loads(row['items']) if row['items'] else []
                for item in items:
                    name = item.get('name')
                    qty = item.get('quantity', 1)
                    if name:
                        perfume_sales[name] = perfume_sales.get(name, 0) + qty
            except json.JSONDecodeError:
                continue

        top_perfumes = sorted(perfume_sales.items(), key=lambda x: x[1], reverse=True)[:5]

    except Exception as e:
        print("Report Error:", e)
        total_orders = total_sales = pending_orders = returned_orders = 0
        sales_labels = sales_values = status_labels = status_counts = []
        top_perfumes = []

    finally:
        cursor.close()
        conn.close()

    return render_template(
        'report.html',
        total_orders=total_orders,
        total_sales=total_sales,
        pending_orders=pending_orders,
        returned_orders=returned_orders,  # ✅ Added to template
        sales_labels=sales_labels,
        sales_values=sales_values,
        status_labels=status_labels,
        status_counts=status_counts,
        top_perfumes=top_perfumes,
        from_date=from_date,
        to_date=to_date
    )

# ----------------------------
# Shop Route
# -----------------------------

@app.route('/shop')
def shop():
    category = request.args.get('category')

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if category:
        # 🧩 Show only perfumes from the selected category
        cursor.execute("SELECT * FROM perfumes WHERE category = %s ORDER BY id DESC", (category,))
    else:
        # 🧩 Show all perfumes if no category selected
        cursor.execute("SELECT * FROM perfumes ORDER BY id DESC")

    perfumes = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('shop.html', perfumes=perfumes, selected_category=category)


# -----------------------------
# open image route
# -----------------------------

@app.route('/open_image/<int:id>')
def open_image(id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM perfumes WHERE id = %s", (id,))
    perfume = cursor.fetchone()
    cursor.close()
    conn.close()

    if not perfume:
        abort(404)

    # Agar aapke paas extra images alag table me hain, to yahan join bhi kar sakte ho
    return render_template('open_image.html', perfume=perfume)


# -----------------------------
# User Checkout Route
# -----------------------------

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':

        # 🧾 CUSTOMER DATA
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        city = request.form.get('city')
        country = request.form.get('country')
        postal = request.form.get('postal')
        address = request.form.get('address')
        payment_method = "Cash on Delivery"

        # 🛒 ITEMS
        items_json = request.form.get('items')

        try:
            items = json.loads(items_json)
        except:
            items = []

        # 💰 CALCULATIONS
        product_total = sum(float(i['price']) * int(i['quantity']) for i in items)
        shipping = 250
        total = product_total + shipping

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        try:
            # 🔍 STOCK CHECK + UPDATE
            for item in items:
                cursor.execute(
                    "SELECT id, stock FROM perfumes WHERE name=%s",
                    (item['name'],)
                )
                perfume = cursor.fetchone()

                if not perfume:
                    conn.rollback()
                    return jsonify({"error": f"{item['name']} not found"}), 400

                if perfume['stock'] < int(item['quantity']):
                    conn.rollback()
                    return jsonify({"error": f"Not enough stock for {item['name']}"}), 400

                cursor.execute(
                    "UPDATE perfumes SET stock=%s WHERE id=%s",
                    (perfume['stock'] - int(item['quantity']), perfume['id'])
                )

            # 💾 INSERT ORDER
            cursor.execute("""
                INSERT INTO orders 
                (user_name, email, phone, city, country, postal, address, items, total, payment_method)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                name, email, phone, city, country, postal, address,
                json.dumps(items), total, payment_method
            ))

            conn.commit()
            order_id = cursor.lastrowid

        except Exception as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 500

        finally:
            cursor.close()
            conn.close()

        # 📧 EMAIL (PROFESSIONAL HTML)
        try:

            items_html = ""

            for item in items:
                item_total = float(item['price']) * int(item['quantity'])

                items_html += f"""
                <div style="display:flex;align-items:center;gap:15px;
                            padding:12px;border-bottom:1px solid #eee;">

                    <img src="{item['image']}" 
                         style="width:65px;height:65px;border-radius:10px;
                         object-fit:cover;border:1px solid #ddd;">

                    <div style="flex:1;">
                        <div style="font-weight:bold;color:#333;">
                            {item['name']}
                        </div>
                        <div style="font-size:13px;color:#777;">
                            Qty: {item['quantity']} | Price: PKR {item['price']}
                        </div>
                    </div>

                    <div style="font-weight:bold;color:#e91e63;">
                        PKR {item_total}
                    </div>

                </div>
                """

            msg = Message(
                subject=f"Order Confirmation #{order_id} - AREEZ FRAGRANCE",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email]
            )

            msg.html = f"""
            <div style="font-family:Arial;background:#f7f7f7;padding:20px;">

              <div style="max-width:750px;margin:auto;background:#fff;
                          border-radius:12px;overflow:hidden;
                          box-shadow:0 5px 20px rgba(0,0,0,0.1);">

                <!-- HEADER -->
                <div style="background:#e91e63;color:white;
                            text-align:center;padding:20px;">
                    <h2 style="margin:0;">AREEZ FRAGRANCE</h2>
                    <p style="margin:5px 0;">Order Confirmation</p>
                </div>

                <!-- BODY -->
                <div style="padding:20px;">

                    <p>Hi <b>{name}</b>, your order is confirmed 🎉 ,we're getting your order ready for shipment.
                    this order will be shipped 3–5 business days, depending on your location.
                    All orders are processed within 24 hours and tracked until safely delivered to your doorstep.</p>

                    <h3 style="color:#e91e63;">🧾 Order Summary</h3>

                    {items_html}

                    <!-- SUMMARY -->
                    <div style="margin-top:20px;padding:15px;
                                background:#fff0f5;border-radius:10px;">

                        <p><b>🚚 Shipping:</b> PKR {shipping}</p>
                        <p><b>🛍 Product Total:</b> PKR {product_total}</p>

                        <hr>

                        <h2 style="color:#e91e63;">
                            Grand Total: PKR {total}
                        </h2>

                    </div>

                    <!-- CUSTOMER INFO -->
                    <div style="margin-top:20px;font-size:14px;color:#444;">
                        <p><b>📍 Address:</b> {address}</p>
                        <p><b>city:</b> {city}</p>
                        <p><b>country:</b> {country}</p>
                        <p><b>📞 Phone:</b> {phone}</p>
                        <p><b>💳 Payment:</b> Cash on Delivery</p>
                    </div>

                    <p style="margin-top:20px;">
                        Thank you for shopping with 
                        <b>AREEZ FRAGRANCE ❤️</b>
                    </p>

                    <p style="margin-top:20px;">
                        If You Have Any Questions, Reply To This Mail OR  Contact Us At Whatsapp
                        <b>+92 302 9389451</b>
                    </p>

                </div>
              </div>
            </div>
            """

            mail.send(msg)

        except Exception as e:
            print("Email error:", e)

        return jsonify({
            "order_id": order_id,
            "total": total,
            "shipping": shipping
        })

    return render_template("checkout.html")


# -----------------------------
# contact route
# -----------------------------

@app.route('/contact')
def contact():
    return render_template('contact.html')

# -----------------------------
# cart route
# -----------------------------

@app.route('/cart')
def cart():
    return render_template('cart.html')

# -----------------------------

# privacy route
# -----------------------------

@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')

# -----------------------------
# terms route
# -----------------------------

@app.route('/terms_of_service')
def terms_of_service():
    return render_template('terms_of_service.html')

# -----------------------------
# refund route
# -----------------------------

@app.route('/refund_policy')
def refund_policy():
    return render_template('refund_policy.html')

# -----------------------------
# shipping route
# -----------------------------

@app.route('/shipping_policy')
def shipping_policy():
    return render_template('shipping_policy.html')

# -----------------------------

if __name__ == '__main__':
    # app.run(host="192.168.100.23", port=5600, debug=True)
    app.run(debug=True)


