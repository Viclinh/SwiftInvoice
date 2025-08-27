from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
import sqlite3
import hashlib
from datetime import datetime, timedelta
import io
import base64
import json
import requests
import subprocess
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Database setup
def init_db():
    conn = sqlite3.connect('invoices.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE,
        password TEXT,
        business_name TEXT,
        subscription_plan TEXT DEFAULT 'free',
        subscription_expires DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Invoices table
    c.execute('''CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        invoice_number TEXT,
        client_name TEXT,
        client_email TEXT,
        amount REAL,
        status TEXT DEFAULT 'draft',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        business_name = request.form['business_name']
        
        conn = sqlite3.connect('invoices.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (email, password, business_name) VALUES (?, ?, ?)',
                     (email, password, business_name))
            conn.commit()
            flash('Registration successful!')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists!')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        conn = sqlite3.connect('invoices.db')
        c = conn.cursor()
        c.execute('SELECT id, business_name FROM users WHERE email = ? AND password = ?',
                 (email, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['business_name'] = user[1]
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('invoices.db')
    c = conn.cursor()
    c.execute('SELECT * FROM invoices WHERE user_id = ? ORDER BY created_at DESC',
             (session['user_id'],))
    invoices = c.fetchall()
    conn.close()
    
    return render_template('dashboard.html', invoices=invoices)

@app.route('/create_invoice', methods=['GET', 'POST'])
def create_invoice():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{session['user_id']}"
        client_name = request.form['client_name']
        client_email = request.form['client_email']
        amount = float(request.form['amount'])
        
        conn = sqlite3.connect('invoices.db')
        c = conn.cursor()
        c.execute('INSERT INTO invoices (user_id, invoice_number, client_name, client_email, amount) VALUES (?, ?, ?, ?, ?)',
                 (session['user_id'], invoice_number, client_name, client_email, amount))
        conn.commit()
        conn.close()
        
        flash('Invoice created successfully!')
        return redirect(url_for('dashboard'))
    
    return render_template('create_invoice.html')

@app.route('/download_pdf/<path:filename>')
def download_pdf(filename):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        return send_file(filename, as_attachment=True, download_name=os.path.basename(filename), mimetype='application/pdf')
    except FileNotFoundError:
        flash('PDF file not found!')
        return redirect(url_for('dashboard'))

@app.route('/generate_pdf/<int:invoice_id>')
def generate_pdf(invoice_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('invoices.db')
    c = conn.cursor()
    c.execute('SELECT * FROM invoices WHERE id = ? AND user_id = ?',
             (invoice_id, session['user_id']))
    invoice = c.fetchone()
    conn.close()
    
    if not invoice:
        flash('Invoice not found!')
        return redirect(url_for('dashboard'))
    
    # Check if it's a PDF filename, if so redirect to download
    if invoice[2].endswith('.pdf'):
        return redirect(url_for('download_pdf', filename=invoice[2]))
    
    # Generate PDF for regular invoices
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Invoice content
    p.drawString(100, 750, f"INVOICE")
    p.drawString(100, 720, f"Invoice #: {invoice[2]}")
    p.drawString(100, 700, f"Business: {session['business_name']}")
    p.drawString(100, 680, f"Client: {invoice[3]}")
    p.drawString(100, 660, f"Email: {invoice[4]}")
    p.drawString(100, 640, f"Amount: ${invoice[5]:.2f}")
    p.drawString(100, 620, f"Date: {invoice[7]}")
    
    p.save()
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f'invoice_{invoice[2]}.pdf', mimetype='application/pdf')

def docGen(doc, data, id, secret, host):
    headers = {
        "client_id": id,
        "client_secret": secret
    }
    
    body = {
        "outputFormat": "pdf",
        "documentValues": data,
        "base64FileString": doc
    }
    
    request = requests.post(f"{host}/document-generation/api/GenerateDocumentBase64", json=body, headers=headers)
    return request.json()

@app.route('/create_from_data')
def create_from_data():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Execute the generateInvoices.py script
        result = subprocess.run(['python3', 'generateInvoices.py'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            # Find all PDF files after running the script
            pdf_files = [f for f in os.listdir('.') if f.startswith('invoice_account_') and f.endswith('.pdf')]
            
            if pdf_files:
                # Load invoice data to save to database
                with open('invoicedata.json', 'r') as file:
                    data = json.load(file)
                
                # Save invoice records to database
                conn = sqlite3.connect('invoices.db')
                c = conn.cursor()
                
                for i, invoiceData in enumerate(data):
                    pdf_filename = f"invoice_account_{invoiceData['accountNumber']}.pdf" if i < len(pdf_files) else None
                    c.execute('INSERT OR IGNORE INTO invoices (user_id, invoice_number, client_name, client_email, amount) VALUES (?, ?, ?, ?, ?)',
                             (session['user_id'], pdf_filename or f"invoice_account_{invoiceData['accountNumber']}.pdf", invoiceData['accountName'], 
                              f"{invoiceData['accountName'].lower().replace(' ', '')}@email.com", 
                              sum(item['totalPrice'] for item in invoiceData.get('lineItems', []))))
                
                conn.commit()
                conn.close()
            else:
                flash('Script ran successfully but no PDF files found.')
        else:
            flash(f'Error running generateInvoices.py: {result.stderr}')
        
    except Exception as e:
        flash(f'Error executing invoice generation: {str(e)}')
    
    return redirect(url_for('dashboard'))

@app.route('/delete_invoice/<int:invoice_id>')
def delete_invoice(invoice_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('invoices.db')
    c = conn.cursor()
    c.execute('DELETE FROM invoices WHERE id = ? AND user_id = ?', (invoice_id, session['user_id']))
    conn.commit()
    conn.close()
    
    flash('Invoice deleted successfully!')
    return redirect(url_for('dashboard'))

@app.route('/merge_files')
def merge_files():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Execute the merge.py script
        result = subprocess.run(['python3', 'merge.py'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            # Find files in Merged_Output folder
            if os.path.exists('./Merged_Output'):
                merged_files = [f for f in os.listdir('./Merged_Output') if f.endswith('.pdf')]
                if merged_files:
                    # Add merged files to database for download links
                    conn = sqlite3.connect('invoices.db')
                    c = conn.cursor()
                    
                    for filename in merged_files:
                        c.execute('INSERT OR IGNORE INTO invoices (user_id, invoice_number, client_name, client_email, amount) VALUES (?, ?, ?, ?, ?)',
                                 (session['user_id'], f"Merged_Output/{filename}", "Merged File", "merged@file.com", 0.0))
                    
                    conn.commit()
                    conn.close()
                    
                    flash('Merge completed! Files are now available for download in the dashboard.')
                else:
                    flash('Merge completed but no files found in Merged_Output folder.')
            else:
                flash('Merge completed but Merged_Output folder not found.')
        else:
            flash(f'Error running merge.py: {result.stderr}')
        
    except Exception as e:
        flash(f'Error executing merge: {str(e)}')
    
    return redirect(url_for('dashboard'))

@app.route('/split_files')
def split_files():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Execute the split.py script
        result = subprocess.run(['python3', 'split.py'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            # Find files in Split_Output folder
            if os.path.exists('./Split_Output'):
                split_files = [f for f in os.listdir('./Split_Output') if f.endswith('.pdf')]
                if split_files:
                    # Add split files to database for download links
                    conn = sqlite3.connect('invoices.db')
                    c = conn.cursor()
                    
                    for filename in split_files:
                        c.execute('INSERT OR IGNORE INTO invoices (user_id, invoice_number, client_name, client_email, amount) VALUES (?, ?, ?, ?, ?)',
                                 (session['user_id'], f"Split_Output/{filename}", "Split File", "split@file.com", 0.0))
                    
                    conn.commit()
                    conn.close()
                    
                    flash('Split completed! Files are now available for download in the dashboard.')
                else:
                    flash('Split completed but no files found in Split_Output folder.')
            else:
                flash('Split completed but Split_Output folder not found.')
        else:
            flash(f'Error running split.py: {result.stderr}')
        
    except Exception as e:
        flash(f'Error executing split: {str(e)}')
    
    return redirect(url_for('dashboard'))

@app.route('/upload_data')
def upload_data():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    folder_path = '/Users/hongtran/Documents/SwiftInvoice'
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    subprocess.run(['open', folder_path])
    return redirect(url_for('dashboard'))

@app.route('/upload_invoices_merge')
def upload_invoices_merge():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    folder_path = '/Users/hongtran/Documents/SwiftInvoice/inputfiles'
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    subprocess.run(['open', folder_path])
    return redirect(url_for('dashboard'))

@app.route('/upload_invoices_split')
def upload_invoices_split():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    folder_path = '/Users/hongtran/Documents/SwiftInvoice/inputfilessplit'
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    subprocess.run(['open', folder_path])
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)