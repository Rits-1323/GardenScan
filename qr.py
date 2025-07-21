import mysql.connector
import qrcode
from qrcode.image.pil import PilImage
import os

DB_CONFIG = {
    'host': 'localhost',
    'user':'root',
    'password': 'R!tv!k@14',
    'database': 'GardenDB'
}

BASE_APP_URL = "http://192.168.0.103:5001"

QR_CODES_DIR = "qr_codes"

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return None

def fetch_gardens():
    conn = get_db_connection()
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)
    gardens = []
    try:
        cursor.execute("SELECT garden_id, garden_name FROM gardens")
        gardens = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error fetching gardens: {err}")
    finally:
        cursor.close()
        conn.close()
    return gardens

def generate_qr_codes():
    gardens = fetch_gardens()

    if not gardens:
        print("No gardens found in the database. Please add entries to the 'gardens' table.")
        return

    if not os.path.exists(QR_CODES_DIR):
        os.makedirs(QR_CODES_DIR)

    print(f"Generating QR codes in '{QR_CODES_DIR}' directory...")
    for garden in gardens:
        garden_id = garden['garden_id']
        garden_name = garden['garden_name']


        qr_data_url = f"{BASE_APP_URL}?garden_id={garden_id}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white", image_factory=PilImage)

        # Save the QR code image
        file_name = f"{QR_CODES_DIR}/garden_{garden_id}_{garden_name.replace(' ', '_').lower()}.png"
        img.save(file_name)
        print(f"Generated QR code for '{garden_name}' (ID: {garden_id}) -> {file_name}")

if __name__ == "__main__":
    generate_qr_codes()