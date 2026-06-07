from flask import Flask, render_template, request, send_file, jsonify, redirect,session,flash,url_for
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os
import io
import time
import random
from datetime import datetime
from psycopg2 import errors
import psycopg2
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from flask import send_from_directory
from waitress import serve
import secrets



app = Flask(__name__)
app.secret_key = "784588"




BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "evidence")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="Ai_investigation",
        user="postgres",
        password="4718"
    )


def generate_complaint_number():
    year = datetime.now().year
    rand = random.randint(100000, 999999)
    return f"CCR-{year}-{rand}"


def is_image(filename):
    return filename.lower().endswith((".png", ".jpg", ".jpeg"))


def calculate_risk(amount):
    amount = float(amount or 0)

    if amount >= 500000:
        return "CRITICAL"
    elif amount >= 100000:
        return "HIGH"
    elif amount >= 50000:
        return "MEDIUM"
    else:
        return "LOW"


# ================= NORMAL PAGE ROUTES =================
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/crime")
def crime():
    return render_template("crime.html")

@app.route("/Complaint")
def complaint():
    if session.get("user_id"):
        return render_template("complaint.html")
    return render_template("login.html")
@app.route("/Financial Fraud")
def comp():
    if session.get("user_id"):
        return redirect("/Complaint")
    return redirect('/login')


@app.route("/Register Complaint")
def compa():
    return render_template("register_complaint.html")


@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/Complaint_Women_Child_Related_Crime")
def child():
    if session.get("user_id"):
        return render_template("child_reg.html")
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        conn = None
        cur = None

        try:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            mobile = request.form['phone']
            state = request.form['state']
            password = request.form['password']

            # 🔥 Clean phone (important for your constraint)
            mobile = mobile.replace("+91", "").replace(" ", "").strip()

            # 🔐 Hash password (VERY IMPORTANT)
            password_hash = password

            no = datetime.now()

            user_id = "USR-" + str(int(time.time()))

            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO people 
                (user_id, first_name, last_name, email, phone, state, password_hash, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                first_name,
                last_name,
                email,
                mobile,
                state,
                password_hash,
                True,   # ✅ boolean (not string)
                no
            ))

            conn.commit()

            return render_template("register.html", error="Register Successfully ✅")

        except psycopg2.errors.UniqueViolation:
            if conn:
                conn.rollback()
            return render_template('register.html', error="User already exists ❌")

        except psycopg2.errors.CheckViolation:
            if conn:
                conn.rollback()
            return render_template('register.html', error="Invalid input format ❌")

        except Exception as e:
            if conn:
                conn.rollback()
            return render_template('register.html', error=str(e))

        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    return render_template('register.html')

@app.route("/trace-complaint", methods=["GET", "POST"])
def trace_complaint():
    # Always render page on GET
    if request.method == "GET":
        return render_template("trace_complaint.html")

    # POST: process tracking request
    id = request.form.get("id")
    email = request.form.get("email")



    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT * FROM admin_case_view 
            WHERE complaint_id = %s AND email = %s
        """, (id, email))

        
        case = cur.fetchone()
        cur.close()
        conn.close()
        comp_id = case[0]
        cat = case[5]
        date = case[12]
        risk = case[9]
        amount = case[13]
        name = case[1]
        if case:
            return render_template("trace_view.html",comp_id = comp_id,cat=cat,date = date,risk = risk,amount = amount,name = name)
        else:
            flash("Invalid CaseID or Email")
            return render_template("trace_complaint.html")
    except psycopg2.errors.InvalidTextRepresentation:
        if conn and not conn.closed:
            conn.rollback()
        flash("Invalid Case ID format")
        return render_template("trace_complaint.html")

    except TypeError:
        if conn and not conn.closed:
            conn.rollback()
        flash("No Case ID or Email Found")
        return render_template("trace_complaint.html")
    except psycopg2.InterfaceError:
        if conn and not conn.closed:
            conn.rollback()
        flash("Database connection error. Please try again.")
        return render_template("trace_complaint.html")
    except Exception as e:
        if conn and not conn.closed:
            conn.rollback()
        print("Error:", e)
        flash("Something went wrong. Please try again.")
        return render_template("trace_complaint.html")
# ============= DB ===========
@app.route("/Trace Complaint")
def trace():
    return render_template("trace_complaint.html")

@app.route("/Ransomeware_Complaint")
def ran():
    if session.get("user_id"):
        return render_template("ransomware.html") 
    return redirect('/login')
@app.route("/Social_Crime_Complaint")
def social():
    if session.get("user_id"):
        return render_template("social_crime.html") 
    return redirect('/login')

@app.route("/contact us",methods = ['POST','GET'])
def us():
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("message")
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('INSERT INTO contact_messages (name,email,message) VALUES(%s,%s,%s)',(name,email,message))
            conn.commit()
            flash("Our Team Contact us Soon............")
            return render_template("contact.html")
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash("This Email is Already Exsists")
            return render_template("contact.html")
    return render_template("contact.html")


@app.route("/women-children-complaint",methods = ['POST'])
def women_comp():
    os.makedirs("static/uploads",exist_ok = True)
    name = request.form.get('name')
    mobile = request.form.get('mobile')
    email = request.form.get('email')
    gender = request.form.get('gender')
    state = request.form.get('state')
    district = request.form.get('district')
    crime_type = request.form.get('crime_type')
    incident_date = request.form.get('incident_date')
    platform = request.form.get('platform')
    profile = request.form.get('profile_link')
    victim_age = request.form.get('victim_age')
    emergency = request.form.get('emergency')
    description = request.form.get('description')
    screenshots = request.files.get('screenshots')
    media = request.files.get('media')
    screenshots_name = None
    media_name = None
    if screenshots and screenshots.filename !="":
        screenshots_name = secure_filename(screenshots.filename)
        screenshots.save(os.path.join(UPLOAD_FOLDER, screenshots_name))
    if media and media.filename !="":
        media_name = secure_filename(media.filename)
        media.save(os.path.join(UPLOAD_FOLDER,media_name))
    
    anonymous = request.form.get('anonymous')
    complaint_id = "WC-" + datetime.now().strftime("%Y%m%d%H%M%S")
    
    emergency_bool = True if emergency == "Yes" else False
    anonymous_bool = True if anonymous else False
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
                INSERT INTO women_child (complaint_id,name,mobile,email,gender,state,district,crime_type,incident_date,platform,profile_link,victim_age,emergency,description,screenshot_path,media_path,anonymous,risk_level,status) 
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    
                complaint_id,
                name,mobile,email,gender,state,district,
                crime_type,incident_date,
                platform,profile,victim_age,
                emergency,
                description,screenshots_name,
                media_name,anonymous,"LOW",
                "AI Reviewed"))
        conn.commit()
        cur.close()
        conn.close()
        flash("Registered Successfully")
    except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash("This Email is Already Exsists")
    return render_template("child_reg.html")

@app.route("/ransomware_report",methods = ['POST'])
def ransome(): 
    name = request.form.get('name')
    email = request.form.get('email')
    ip = request.form.get('ip')
    os1 = request.form.get('os')
    description = request.form.get('description')
    evidence = request.files.get('evidence')
    id =  "RA-" + datetime.now().strftime("%Y%m%d%H%M%S")
    evidence_name = None
    if evidence and evidence.filename !="":
        evidence_name = secure_filename(evidence.filename)
        evidence.save(os.path.join(UPLOAD_FOLDER, evidence_name))
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(""" INSERT into ransomware (id,name,email,ip,os,description,evidence)
                VALUES(%s,%s,%s,%s,%s,%s,%s)""",(id,name,email,ip,os1,description,evidence_name))
        conn.commit()
        cur.close()
        conn.close() 
        flash("Complaint Registered Successfully")
    except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash("This Email is Already Exsists")
    return render_template("ransomware.html")

@app.route("/shopping_fraud",methods = ['POST'])
def shop():
    name = request.form.get('name')
    mobile = request.form.get('mobile')
    email = request.form.get('email')
    state = request.form.get('state')
    website = request.form.get('website')
    order_id = request.form.get('order_id')
    amount = request.form.get('amount')
    payment_method = request.form.get('payment_method')
    fraud_date = request.form.get('fraud_date')
    seller_mobile = request.form.get('seller_mobile')
    description = request.form.get('description')
    payment_proof = request.files.get('payment_proof')
    product_image = request.files.get('product_image')
    chat_proof = request.files.get('chat_proof')
    id =  "SH-" + datetime.now().strftime("%Y%m%d%H%M%S")
    payment_proof_name = None
    product_image_name = None
    chat_proof_name = None
    if payment_proof and payment_proof.filename !="":
        payment_proof_name = secure_filename(payment_proof.filename)
        payment_proof.save(os.path.join(UPLOAD_FOLDER, payment_proof_name))
    if product_image and product_image.filename !="":
        product_image_name = secure_filename(product_image.filename)
        product_image.save(os.path.join(UPLOAD_FOLDER, product_image_name))
    if chat_proof and chat_proof.filename !="":
        chat_proof_name = secure_filename(chat_proof.filename)
        chat_proof.save(os.path.join(UPLOAD_FOLDER, chat_proof_name))
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(""" INSERT into shopping (id,name,mobile,email,state,website,order_id,amount,payment_method,fraud_date,seller_mobile,description,payment_proof,product_image,chat_proof)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(id,name,mobile,
                                                                email,state,website,
                                                                order_id,amount,payment_method,
                                                                fraud_date,seller_mobile,description,payment_proof_name,
                                                                product_image_name,chat_proof_name
                                                                ))
        conn.commit()
        cur.close()
        conn.close() 
        flash("Complaint Registered Successfully")
    except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash("This Email is Already Exsists")
    return render_template("shopping.html")
    

@app.route("/social_media_crime",methods = ['POST'])
def socr():
    name = request.form.get('name')    
    mobile = request.form.get('mobile')
    email = request.form.get('email')   
    state = request.form.get('state')
    crime_type = request.form.get('crime_type')
    platform = request.form.get('platform')     
    profile_link = request.form.get('profile_link') 
    incident_date = request.form.get('incident_date')  
    description= request.form.get('description')
    screenshots = request.files.get('screenshots')
    chat_file = request.files.get('chat_file')
    screenshots_name = None
    chat_file_name = None
    if screenshots and screenshots.filename !="":
        screenshots_name = secure_filename(screenshots.filename)
        screenshots.save(os.path.join(UPLOAD_FOLDER, screenshots_name))
    screenshots_name = None
    media_name = None
    if chat_file and chat_file.filename !="":
        chat_file_name = secure_filename(chat_file.filename)
        chat_file.save(os.path.join(UPLOAD_FOLDER, chat_file_name))
    id =  "SO-" + datetime.now().strftime("%Y%m%d%H%M%S")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(""" INSERT into social (id,name,mobile,email,state,crime_type,platform,profile_link,incident_date,description)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(id,name,mobile,email,state,crime_type,platform,profile_link,incident_date,description))
        conn.commit()
        cur.close()
        conn.close() 
        flash("Complaint Registered Successfully")
    except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash("This Email is Already Exsists")
    return render_template("social_crime.html")

        
    
    
    
    
@app.route("/Report Suspect")
def report():
    return render_template("report.html")
@app.route("/Cyber Volunteers")
def cys():
    return render_template("cyber_volunteers.html")

@app.route("/Shopping_Complaint")
def shopping():
    if session.get("user_id"):
        return render_template("shopping.html")
    return redirect('/login')

@app.route("/Phishing_Complaint")
def phishing():
    if session.get("user_id"):
        return render_template("phishing.html")
    return redirect('/login')

@app.route("/Cyberbullying_Harassment")
def bulling():
    if session.get("user_id"):
        return render_template("bulling.html")
    return redirect('/login')
@app.route('/Identity_Theft')
def identity():
    return render_template('identity.html')
@app.route('/Sus')
def sus():
    return render_template("sus.html")

@app.route("/Volunteers",methods = ["GET","POST"])
def volunteers():
    if request.method == "POST":
        name = request.form["fullname"]
        email = request.form["email"]
        skill = request.form["skill"]
        conn = get_db_connection()
        cur=conn.cursor()
        try:
            cur.execute(
            "INSERT INTO volunteers(name, email, skill) VALUES (%s, %s, %s)",
            (name, email, skill)
            )
            conn.commit()
            
            
            flash("Congratulations! You have joined as a Cyber Volunteer.")
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash("This Email is Already Exsists")
        return redirect(url_for("volunteers"))
    return render_template("cyber_volunteers.html")

@app.route("/Contact Us")
def contact():
    return render_template("contact.html")

@app.route("/Learning Corner")
def learning():
    return render_template("learning.html")


# ================= SUBMIT COMPLAINT + GENERATE PDF =================

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    conn = None
    cur = None
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        registered_on = datetime.now().strftime("%d-%m-%Y %H:%M")

        victim_name = request.form.get("victimName", "")
        victim_phone = request.form.get("victimPhone", "")
        victim_alt_phone = request.form.get("victimAltPhone", "")
        victim_email = request.form.get("victimEmail", "")
        victim_address = request.form.get("victimAddress", "")
        complaint_title = request.form.get("complaintTitle", "")
        crime_category = request.form.get("crimeCategory", "")
        incident_date = request.form.get("incidentDate") or None
        incident_time = request.form.get("incidentTime") or None
        incident_description = request.form.get("incidentDescription", "")
        suspect_details = request.form.get("suspectDetails", "")

        tx_ids = request.form.getlist("transactionId[]")
        tx_dates = request.form.getlist("transactionDate[]")
        tx_times = request.form.getlist("transactionTime[]")
        tx_amounts = request.form.getlist("transactionAmount[]")
        tx_sender_banks = request.form.getlist("senderBank[]")
        tx_sender_accounts = request.form.getlist("senderAccount[]")
        tx_receiver_banks = request.form.getlist("receiverBank[]")
        tx_modes = request.form.getlist("transactionMode[]")
        tx_remarks = request.form.getlist("transactionRemark[]")

        total_amount = sum(float(a or 0) for a in tx_amounts)
        risk_level = calculate_risk(total_amount)

        cur.execute("""
            INSERT INTO complaints
            (victim_full_name, phone, email, complaint_title, category,
             incident_date, incident_time, description, risk_level, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (
            victim_name,
            victim_phone,
            victim_email,
            complaint_title,
            crime_category,
            incident_date,
            incident_time,
            incident_description,
            risk_level,
            "AI Reviewed"
        ))

        complaint_id = cur.fetchone()[0]
        complaint_number = generate_complaint_number()
        display_number = f"case-{complaint_id}"

        transactions = []

        for i in range(len(tx_ids)):
            amount = float(tx_amounts[i] or 0) if i < len(tx_amounts) else 0

            transaction = {
                "transaction_id": tx_ids[i] if i < len(tx_ids) else "",
                "transaction_date": tx_dates[i] if i < len(tx_dates) else "",
                "transaction_time": tx_times[i] if i < len(tx_times) else "",
                "amount": amount,
                "sender_bank": tx_sender_banks[i] if i < len(tx_sender_banks) else "",
                "sender_account": tx_sender_accounts[i] if i < len(tx_sender_accounts) else "",
                "receiver_bank": tx_receiver_banks[i] if i < len(tx_receiver_banks) else "",
                "mode": tx_modes[i] if i < len(tx_modes) else "",
                "remark": tx_remarks[i] if i < len(tx_remarks) else "",
            }

            transactions.append(transaction)

            cur.execute("""
                INSERT INTO complaint_transactions
                (complaint_id, transaction_id, transaction_date, transaction_time,
                 amount, payment_mode, sender_account, receiver_account, receiver_bank)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                complaint_id,
                transaction["transaction_id"],
                transaction["transaction_date"] or None,
                transaction["transaction_time"] or None,
                transaction["amount"],
                transaction["mode"],
                transaction["sender_account"],
                transaction["receiver_bank"],
                transaction["receiver_bank"]
            ))

        evidence_types = request.form.getlist("evidenceType[]")
        evidence_refs = request.form.getlist("evidenceTransactionRef[]")
        evidence_descs = request.form.getlist("evidenceDescription[]")
        uploaded_files = request.files.getlist("evidenceFile[]")

        evidences = []

        for i, file in enumerate(uploaded_files):
            if not file or not file.filename:
                continue

            original_name = secure_filename(file.filename)

            saved_name = f"case_{complaint_id}_{int(time.time())}_{original_name}"

            file_path = os.path.join(UPLOAD_FOLDER, saved_name)
            file.save(file_path)

            db_file_path = "uploads/evidence/" + saved_name

            file_type = saved_name.rsplit(".", 1)[1].lower()

            cur.execute("""
            INSERT INTO complaint_evidence
            (complaint_id, file_name, file_path, file_type)
            VALUES (%s,%s,%s,%s)
            """, (
            complaint_id,
            saved_name,
            db_file_path,
        file_type
        ))

        cur.execute("""
            INSERT INTO ai_risk_analysis
            (complaint_id, amount_risk, time_risk, behavior_risk, final_risk, ai_notes)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            complaint_id,
            "Checked",
            "Checked",
            "Checked",
            risk_level,
            f"Total transaction amount ₹{total_amount}. Risk level: {risk_level}."
        ))

        cur.execute("""
            INSERT INTO case_progress
            (complaint_id, stage, status, remarks)
            VALUES (%s,%s,%s,%s)
        """, (
            complaint_id,
            "AI Review",
            "Completed",
            f"Complaint saved. Risk level: {risk_level}."
        ))

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 40

        def new_page():
            nonlocal y
            pdf.showPage()
            y = height - 40
            pdf.setFont("Helvetica", 10)
            pdf.drawRightString(width - 40, 20, f"Complaint No: {complaint_number}")

        def line(text, x=40, step=16, font="Helvetica", size=10):
            nonlocal y
            if y < 60:
                new_page()
            pdf.setFont(font, size)
            pdf.drawString(x, y, str(text))
            y -= step

        def wrapped_label_value(label, value, x=40, max_chars=95):
            text = f"{label}: {value if value else '-'}"
            while text:
                part = text[:max_chars]
                text = text[max_chars:]
                line(part, x=x)

        pdf.setTitle(f"{display_number}.pdf")

        line("Cyber Crime Complaint Copy", font="Helvetica-Bold", size=16, step=24)
        line(f"Complaint No: {display_number}", font="Helvetica-Bold")
        line(f"Registered On: {registered_on}")
        line("Status: Submitted")
        line(f"Risk Level: {risk_level}")
        y -= 6

        line("1. Victim Details", font="Helvetica-Bold", size=12, step=20)
        wrapped_label_value("Victim Name", victim_name)
        wrapped_label_value("Phone", victim_phone)
        wrapped_label_value("Alternate Phone", victim_alt_phone)
        wrapped_label_value("Email", victim_email)
        wrapped_label_value("Address", victim_address)
        y -= 6

        line("2. Incident Details", font="Helvetica-Bold", size=12, step=20)
        wrapped_label_value("Complaint Title", complaint_title)
        wrapped_label_value("Crime Category", crime_category)
        wrapped_label_value("Incident Date", incident_date)
        wrapped_label_value("Incident Time", incident_time)
        wrapped_label_value("Suspect Details", suspect_details)
        wrapped_label_value("Incident Description", incident_description)
        y -= 6

        line("3. Transaction Annexure", font="Helvetica-Bold", size=12, step=20)
        if not transactions:
            line("No transaction details available.")
        else:
            for idx, tx in enumerate(transactions, start=1):
                wrapped_label_value(
                    f"TX {idx}",
                    f"ID {tx['transaction_id']}, Date {tx['transaction_date']}, "
                    f"Time {tx['transaction_time']}, Amount Rs.{tx['amount']}, "
                    f"Sender Bank {tx['sender_bank']}, Sender A/C {tx['sender_account']}, "
                    f"Receiver {tx['receiver_bank']}, Mode {tx['mode']}, Remark {tx['remark']}"
                )

        y -= 6

        line("4. Evidence Annexure", font="Helvetica-Bold", size=12, step=20)
        if not evidences:
            line("No evidence details available.")
        else:
            for idx, ev in enumerate(evidences, start=1):
                wrapped_label_value(
                    f"Evidence {idx}",
                    f"Type {ev['evidence_type']}, Linked TX {ev['linked_transaction']}, "
                    f"Description {ev['description']}, File {ev['file_name'] or '-'}"
                )

        for idx, ev in enumerate([e for e in evidences if e["is_image"] and e["file_path"]], start=1):
            new_page()
            line(f"5.{idx} Evidence Preview", font="Helvetica-Bold", size=12, step=20)
            wrapped_label_value("Evidence Type", ev["evidence_type"])
            wrapped_label_value("Linked Transaction", ev["linked_transaction"])
            wrapped_label_value("Description", ev["description"])
            wrapped_label_value("File Name", ev["file_name"])
            y -= 10

            try:
                img = ImageReader(ev["file_path"])
                img_width = width - 80
                img_height = 300

                if y - img_height < 40:
                    new_page()

                pdf.drawImage(
                    img,
                    40,
                    y - img_height,
                    width=img_width,
                    height=img_height,
                    preserveAspectRatio=True,
                    mask="auto"
                )
                y -= img_height + 20
            except Exception:
                line("Could not render image preview.")

        if y < 120:
            new_page()

        line("6. Declaration", font="Helvetica-Bold", size=12, step=20)
        wrapped_label_value(
            "Declaration",
            "I hereby declare that the information submitted in this complaint is true to the best of my knowledge and belief."
        )

        y -= 20
        line(f"Complainant Name: {victim_name}")
        line(f"Complaint Number: {display_number}")
        y -= 20
        pdf.line(350, y, 540, y)
        y -= 14
        line("Signature / Digital Acknowledgment", x=380)

        pdf.save()
        buffer.seek(0)

        pdf_filename = f"case_{complaint_id}_{display_number}_{complaint_number}.pdf"
        pdf_save_path = os.path.join(UPLOAD_FOLDER, pdf_filename)

        with open(pdf_save_path, "wb") as f:
            f.write(buffer.getvalue())

        pdf_db_path = "/" + pdf_save_path.replace("\\", "/")

        cur.execute("""
            INSERT INTO complaint_evidence
            (complaint_id, file_name, file_path, file_type)
            VALUES (%s,%s,%s,%s)
        """, (
            complaint_id,
            pdf_filename,
            pdf_db_path,
            "pdf"
        ))

        conn.commit()

        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{complaint_number}.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        if conn:
            conn.rollback()
        print("DATABASE ERROR:", e)
        return f"Database error: {e}"

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            
# CASE DELETE 
@app.route("/delete-case/<int:complaint_id>", methods=["POST"])
def delete_case(complaint_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM complaints WHERE id = %s", (complaint_id,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Case deleted"})


# ================= CASE FOLDER ROUTES =================

@app.route("/case")
def case_page():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, complaint_title, victim_full_name, risk_level
        FROM complaints
        ORDER BY id DESC
    """)

    complaints = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("case.html", complaints=complaints)



@app.route("/Folder")
def folder_old():
    return redirect("/case")


@app.route("/evidence/<path:filename>")
def evidence_file(filename):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    return send_from_directory(UPLOAD_FOLDER, filename)
@app.route("/test-files")
def test_files():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    files = os.listdir(UPLOAD_FOLDER)

    html = ""
    for f in files:
        html += f'<p>{f} - <a href="/evidence/{f}" target="_blank">Open</a></p>'

    return html or "No files found"

@app.route("/folder/<int:complaint_id>")
def folder_page(complaint_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, victim_full_name, phone, email, complaint_title,
               category, incident_date, incident_time, description,
               risk_level, status
        FROM complaints
        WHERE id = %s
    """, (complaint_id,))

    complaint = cur.fetchone()

    cur.execute("""
        SELECT id, file_name, file_path, file_type
        FROM complaint_evidence
        WHERE complaint_id = %s
        ORDER BY uploaded_at DESC
    """, (complaint_id,))

    evidence = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("folder.html", complaint=complaint, evidence=evidence)


# ================= MANUAL EVIDENCE UPLOAD =================

@app.route("/upload-evidence/<int:complaint_id>", methods=["POST"])
def upload_evidence(complaint_id):
    conn = None
    cur = None

    try:
        if "pdf_file" not in request.files:
            return "No file part"

        file = request.files["pdf_file"]

        if file.filename == "":
            return "No file selected"

        filename = secure_filename(file.filename)
        filename = f"case_{complaint_id}_{int(time.time())}_{filename}"

        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        db_file_path = "/" + save_path.replace("\\", "/")
        file_type = filename.rsplit(".", 1)[1].lower()

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO complaint_evidence
            (complaint_id, file_name, file_path, file_type)
            VALUES (%s, %s, %s, %s)
        """, (complaint_id, filename, db_file_path, file_type))

        conn.commit()

        return redirect(f"/folder/{complaint_id}")

    except Exception as e:
        if conn:
            conn.rollback()
        print("UPLOAD ERROR:", e)
        return f"Upload failed: {e}"

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
@app.route("/login_accept",methods=["POST"])
def accept():
    email = request.form.get("email", "")
    password = request.form.get("password", "")
    
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute('SELECT * from people WHERE "email" = %s',(email,))
    user=cur.fetchone()
    conn.close()
    cur.close()
    Email = user[3]
    passw = user[6]
    print(passw)
    print(Email)
    if email == Email and password == passw:
        session['user_id'] = user[0]
        session['email'] = user[3]
        return redirect('/')
    else:
        return render_template('login.html',error = "wrong email or password")
@app.route("/logout")
def logout():
    session.clear()
    return redirect('/')
    

# ================= API FOR CASE.HTML IF YOUR JS USES FETCH =================

@app.route("/api/complaints")
def api_complaints():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, complaint_title, victim_full_name, risk_level
        FROM complaints
        ORDER BY id DESC
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    data = []

    for row in rows:
        data.append({
            "id": row[0],
            "complaint_title": row[1],
            "victim_full_name": row[2],
            "risk_level": row[3]
        })

    return jsonify(data)


# ================= CHATBOT =================

@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    if request.method == "GET":
        return "Chatbot API is running"

    conn = None
    cur = None

    try:
        data = request.get_json()
        user_msg = data.get("message", "").lower()

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT intent, keywords, reply FROM chatbot_keywords")
        rows = cur.fetchall()

        best_reply = None
        best_score = 0

        for intent, keywords, reply in rows:
            score = 0

            for word in keywords.lower().split():
                if word in user_msg:
                    score += 1

            if score > best_score:
                best_score = score
                best_reply = reply

        if best_reply:
            bot_reply = best_reply
        else:
            bot_reply = "I can help with cybercrime complaint registration, UPI fraud, case tracking, helpline, and evidence guidance Only, Not Your Own Purpose."

        return jsonify({"reply": bot_reply})

    except Exception as e:
        print("CHATBOT ERROR:", e)
        return jsonify({"reply": "Chatbot error. Please try again."})

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


if __name__ == "__main__":
   app.run( debug=True)