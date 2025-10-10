from datetime import datetime
from flask import Flask, flash, jsonify, request, render_template, redirect, session, url_for
import mysql.connector

app = Flask(__name__)
app.secret_key = "112233"  # kuch bhi random strong string daal do

db_config= {
    'host':'localhost',
    'user':'root',
    'password':'raziq12@',
    'database':'e_comrece'
}

# Home route
@app.route('/')
def home():
    return render_template('home.html')


# Shop route
@app.route('/shop')
def shop():
    return render_template('shop.html')

# contact route
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Shipping Policy routes
@app.route('/shipping_policy')
def shipping_policy():
    return render_template('shipping_policy.html')

# refund policy route
@app.route('/refund_policy')
def refund_policy():
    return render_template('refund_policy.html')

# privacy policy route
@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')

# terms of service route
@app.route('/terms_of_service')
def terms_of_service():
    return render_template('terms_of_service.html')


if __name__ == '__main__':
    app.run(host="192.168.100.23", debug=True, port=5500)
    # app.run(debug=True)