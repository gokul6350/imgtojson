import sqlite3
import os
import json
from datetime import datetime

class BillDatabase:
    def __init__(self):
        self.db_path = "bills.db"
        self.setup_database()

    def setup_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create bills table with only essential fields
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL,
            company_name TEXT NOT NULL,
            total_cost REAL NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()

    def add_bill(self, invoice_number, company_name, total_cost):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO bills (invoice_number, company_name, total_cost)
        VALUES (?, ?, ?)
        ''', (invoice_number, company_name, total_cost))
        
        conn.commit()
        conn.close()

    def get_all_bills(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM bills ORDER BY upload_date DESC')
        bills = cursor.fetchall()
        
        conn.close()
        
        # Convert to list of dictionaries
        columns = ['id', 'invoice_number', 'company_name', 'total_cost', 'upload_date']
        return [dict(zip(columns, bill)) for bill in bills]

    def search_bills(self, search_term):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM bills 
        WHERE invoice_number LIKE ? 
        OR company_name LIKE ?
        ORDER BY upload_date DESC
        ''', (f'%{search_term}%', f'%{search_term}%'))
        
        bills = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'invoice_number', 'company_name', 'total_cost', 'upload_date']
        return [dict(zip(columns, bill)) for bill in bills] 