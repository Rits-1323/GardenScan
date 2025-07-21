from flask import Flask, render_template, request, redirect, url_for, jsonify
import datetime
import json
import mysql.connector

app = Flask(__name__)

DB_CONFIG = {
    'host': 'localhost',
    'user':'root',
    'password': 'R!tv!k@14',
    'database': 'GardenDB'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return None

def get_garden_details():
    conn = get_db_connection()
    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)
    garden_details = None
    try:
        cursor.execute("SELECT garden_id, garden_name, adult_price, child_price, account_number FROM gardens LIMIT 1")
        garden_details = cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Error fetching garden details: {err}")
    finally:
        cursor.close()
        conn.close()
    return garden_details

def generate_qr_code_data(garden_details):
    if not garden_details:
        return json.dumps({"error": "Garden details not available"})

    data = {
        "gardenName": garden_details["garden_name"],
        "adultPrice": float(garden_details["adult_price"]),
        "childPrice": float(garden_details["child_price"]),
        "accountNumber": garden_details["account_number"],
        "formUrl": request.url_root
    }
    return json.dumps(data)

@app.route('/')
def index():
    """
    Renders the main visitor form page.
    """
    garden_details = get_garden_details()
    if not garden_details:
        return "Garden details could not be loaded. Please check database connection and data.", 500

    qr_data_string = generate_qr_code_data(garden_details)
    return render_template('index.html',
                           garden_name=garden_details["garden_name"],
                           adult_price=garden_details["adult_price"],
                           child_price=garden_details["child_price"],
                           qr_data=qr_data_string)

@app.route('/submit_ticket', methods=['POST'])
def submit_ticket():
    """
    Handles the submission of the visitor form.
    """
    conn = get_db_connection()
    if conn is None:
        return "Database connection error.", 500

    cursor = conn.cursor()
    try:
        visitor_name = request.form['visitorName']
        num_adults = int(request.form['numAdults'])
        num_children = int(request.form['numChildren'])
        phone_number = request.form['phoneNumber']

        garden_details = get_garden_details()
        if not garden_details:
            return "Garden details not available for ticket calculation.", 500

        adult_price = float(garden_details["adult_price"])
        child_price = float(garden_details["child_price"])
        total_amount = (num_adults * adult_price) + (num_children * child_price)

        # Insert ticket details in the DB
        sql = """
        INSERT INTO tickets (garden_id, visitor_name, num_adults, num_children, total_amount, phone, visit_date, payment_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        garden_id = garden_details["garden_id"]
        visit_date = datetime.date.today().strftime("%Y-%m-%d")
        payment_status = "pending" # Initial status

        cursor.execute(sql, (garden_id, visitor_name, num_adults, num_children, total_amount, phone_number, visit_date, payment_status))
        conn.commit()

        ticket_id = cursor.lastrowid

        # Redirection
        return redirect(url_for('payment_page', ticket_id=ticket_id))

    except ValueError:
        conn.rollback()
        return "Invalid input for number of adults or children. Please enter valid numbers.", 400
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Error submitting ticket to database: {err}")
        return f"An error occurred while saving ticket: {err}", 500
    except Exception as e:
        conn.rollback()
        return f"An unexpected error occurred: {e}", 500
    finally:
        cursor.close()
        conn.close()

@app.route('/payment/<int:ticket_id>')
def payment_page(ticket_id):
    """
    Renders the payment placeholder page.
    """
    conn = get_db_connection()
    if conn is None:
        return "Database connection error.", 500

    cursor = conn.cursor(dictionary=True)
    ticket_details = None
    try:
        cursor.execute("SELECT total_amount FROM tickets WHERE ticket_id = %s", (ticket_id,))
        ticket_details = cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Error fetching ticket for payment: {err}")
    finally:
        cursor.close()
        conn.close()

    if not ticket_details:
        return "Ticket not found or payment details unavailable.", 404

    garden_details = get_garden_details() # Fetch garden details for account number
    if not garden_details:
        return "Garden details could not be loaded for payment.", 500

    return render_template('payment.html',
                           ticket_id=ticket_id,
                           total_amount=ticket_details["total_amount"],
                           account_number=garden_details["account_number"])

@app.route('/confirm_payment/<int:ticket_id>', methods=['POST'])
def confirm_payment(ticket_id):
    """
    Simulates payment confirmation.
    """
    conn = get_db_connection()
    if conn is None:
        return "Database connection error.", 500

    cursor = conn.cursor()
    try:
        sql = "UPDATE tickets SET payment_status = 'paid' WHERE ticket_id = %s"
        cursor.execute(sql, (ticket_id,))
        conn.commit()

        # Redirect to the final ticket display page
        return redirect(url_for('ticket_confirmed', ticket_id=ticket_id))

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Error confirming payment in database: {err}")
        return f"An error occurred while confirming payment: {err}", 500
    except Exception as e:
        conn.rollback()
        return f"An unexpected error occurred: {e}", 500
    finally:
        cursor.close()
        conn.close()

@app.route('/ticket_confirmed/<int:ticket_id>')
def ticket_confirmed(ticket_id):
    """
    Renders the final generated ticket page.
    Fetches all ticket details from the database.
    """
    conn = get_db_connection()
    if conn is None:
        return "Database connection error.", 500

    cursor = conn.cursor(dictionary=True)
    ticket = None
    try:
        sql = """
        SELECT t.visitor_name, t.num_adults, t.num_children, t.total_amount, t.phone, t.visit_date,
               g.garden_name
        FROM tickets t
        JOIN gardens g ON t.garden_id = g.garden_id
        WHERE t.ticket_id = %s AND t.payment_status = 'paid'
        """
        cursor.execute(sql, (ticket_id,))
        ticket = cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Error fetching confirmed ticket: {err}")
    finally:
        cursor.close()
        conn.close()

    if not ticket:
        return "Ticket not found or payment not confirmed.", 404

    return render_template('ticket.html', ticket=ticket)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port= 5001,debug=True)
