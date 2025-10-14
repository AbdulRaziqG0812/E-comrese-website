from datetime import datetime
from flask import Flask, flash, jsonify, request, render_template, redirect, session, url_for
import mysql.connector
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "112233"

# ✅ Upload folder config
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# ✅ Auto-create upload folder
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# ✅ Database Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'raziq12@',
    'database': 'e_comrece'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)


# -----------------------------
# 🏠 Admin Panel Routes
# -----------------------------

@app.route('/')
def admin():
    # Optional: redirect directly to dashboard
    return redirect(url_for('admin_dashboard'))

# -----------------------------
# 🏠 Admin list Routes
# -----------------------------

@app.route('/admin')
def admin_dashboard():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM perfumes")
    perfumes = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('admin.html', perfumes=perfumes)


# -----------------------------
# 🏠 perfume Panel Routes
# -----------------------------

@app.route('/perfume', methods=['GET', 'POST'])
def perfume():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        sale_price = request.form['sale_price']
        stock = request.form['stock']

        # 🖼️ Handle Image Upload or Default
        image = request.files.get('image')
        if image and image.filename.strip() != '':
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = 'default.jpg'

        # 💾 Save to database
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO perfumes (name, image, description, price, sale_price, stock)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, filename, description, price, sale_price, stock))
        db.commit()
        cursor.close()
        db.close()

        flash("✅ Perfume added successfully!")

    return render_template('perfume.html')

# -----------------------------
# 🏠 edit perfume Panel Routes
# -----------------------------

@app.route('/edit_perfume/<int:id>', methods=['GET', 'POST'])
def edit_perfume(id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM perfumes WHERE id=%s", (id,))
    perfume = cursor.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        sale_price = request.form['sale_price']
        stock = request.form['stock']

        image = request.files.get('image')

        # ✅ If new image uploaded
        if image and image.filename.strip() != '':
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # 🧹 Delete old image (only if not default)
            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], perfume['image'])
            if perfume['image'] != 'default.jpg' and os.path.exists(old_image_path):
                os.remove(old_image_path)
        else:
            # 🧠 Keep old image if new not uploaded
            filename = perfume['image']

        # 💾 Update database
        cursor.execute("""
            UPDATE perfumes
            SET name=%s, image=%s, description=%s, price=%s, sale_price=%s, stock=%s
            WHERE id=%s
        """, (name, filename, description, price, sale_price, stock, id))
        db.commit()

        cursor.close()
        db.close()

        flash("✏️ Perfume updated successfully!")
        return redirect(url_for('admin_dashboard'))

    cursor.close()
    db.close()
    return render_template('edit_perfume.html', perfume=perfume)

# -----------------------------
# 🏠 delete perfume Panel Routes
# -----------------------------

@app.route('/delete/<int:id>')
def delete_perfume(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM perfumes WHERE id=%s", (id,))
    db.commit()
    cursor.close()
    db.close()

    flash("🗑️ Perfume deleted!")
    return redirect(url_for('admin_dashboard'))  # ✅ FIXED


if __name__ == '__main__':
    app.run(host="192.168.100.23", debug=True, port=5500)
