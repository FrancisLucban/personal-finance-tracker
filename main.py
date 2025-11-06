from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QFormLayout, QDialogButtonBox,
    QLabel, QLineEdit, QComboBox, QDateEdit, QMessageBox, QDialog
)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor, QBrush
from database import get_connection, init_db
import sys, os

class FormDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Input Form")
        self.resize(300, 150)

        # ---- Input Fields ----
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        
        self.type_input = QComboBox()
        self.type_input.addItems(["Income", "Expense"])

        self.category_input = QLineEdit()
        self.amount_input = QLineEdit()
        self.note_input = QLineEdit()
        
        form_layout = QFormLayout()
        form_layout.addRow("Set Date:", self.date_input)
        form_layout.addRow("Type:", self.type_input)
        form_layout.addRow("Category:", self.category_input)
        form_layout.addRow("Amount:", self.amount_input)
        form_layout.addRow("Note:", self.note_input)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.validate_submit)
        self.buttons.rejected.connect(self.reject)
        
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def validate_submit(self):
        """Validates user inputs"""
        date = self.date_input.date().toString("MM-dd-yyyy")
        ttype = self.type_input.currentText()
        category = self.category_input.text()
        note = self.note_input.text()
        
        try:
            amount = float(self.amount_input.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Amount must be a number.")
            return

        if not category:
            QMessageBox.warning(self, "Error", "Category cannot be empty.")
            return
        
        if len(category) > 20:
            QMessageBox.warning(self, "Error", "Category name is too long! Please limit to 20 characters of fewer.")
            return
        
        if amount <= 0:
            QMessageBox.warning(self, "Error", "Amount must be a positive number.")
            return
        
        if amount > 9_999_999:
            QMessageBox.warning(self, "Error", "That’s a bit too high! The maximum amount you can enter is ₱9999999.00")
            return
        
        self.date = date
        self.ttype = ttype
        self.category = category
        self.amount = round(amount, 2)
        self.note = note
        
        self.accept()
        
    def get_data(self):
        """Returns data inputted by user after validation"""
        return {
            "date": self.date,
            "type": self.ttype,
            "category": self.category,
            "amount": self.amount,
            "note": self.note
        }
        
class FinanceTracker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personal Finance Tracker")
        self.resize(800,500)
        self.init_ui()
        self.load_transactions()

    def init_ui(self):
        """Initialize layouts, labels, buttons, and main table"""
        main_layout = QVBoxLayout()
        
        header_section = QHBoxLayout()
        button_section = QHBoxLayout()
        
        # ============== HEADER SECTION ==============
        
        # ---- Balance Container ----
        balance_container = QVBoxLayout()
        self.current_balance_label = QLabel("Current Balance: ")
        self.current_balance_label.setObjectName("current_balance_label")
        self.balance_label = QLabel("₱0.00")
        self.balance_label.setObjectName("balance")
        self.tracked_date_label = QLabel("Tracked Since: ")
        self.tracked_date_label.setObjectName("tracked_date")
        balance_container.addWidget(self.current_balance_label)
        balance_container.addWidget(self.balance_label)
        balance_container.addWidget(self.tracked_date_label)
        
        
        header_section.addLayout(balance_container)
        header_section.setSpacing(0.5)
        
        # ============== BUTTON and SEARCH BAR SECTION ==============
        self.add_transaction_btn = QPushButton("+ Add Transaction")
        self.add_transaction_btn.setObjectName("add_transaction_btn")
        self.add_transaction_btn.setFixedWidth(200)
        self.add_transaction_btn.setCursor(Qt.PointingHandCursor)
        self.add_transaction_btn.clicked.connect(self.open_form)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.filter_table)
        self.search_bar.setFixedWidth(200)
        
        button_section.addWidget(self.add_transaction_btn)
        button_section.addWidget(self.search_bar)
        button_section.addStretch() 
        
        # ---- Table ----
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date", "Type", "Category", "Amount", "Note"])
        
        main_layout.addLayout(header_section)
        main_layout.addLayout(button_section)
        main_layout.addWidget(self.table)
        
        self.setLayout(main_layout)
    
    def open_form(self):
        """Open the form dialog"""
        form = FormDialog()
        if form.exec():
            add_transaction_data = form.get_data()
            self.add_transaction(add_transaction_data)
    
    def load_transactions(self):
        """Load the database and display contents to table"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, date, type, category, amount, note FROM transactions ORDER BY date ASC")
        rows = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(rows))
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Date", "Type", "Category", "Amount", "Note", "", ""])

        if not rows:
            self.balance_label.setText("₱0.00")
            self.balance_label.setStyleSheet("color: black;")
            self.tracked_date_label.setText("Tracked Since: ")
            return
        
        # ---- Initialize Balance and Tracked Since Values ----
        balance = 0
        tracked_since_date = rows[0][1]

        for i, row in enumerate(rows):
            trans_id, date, ttype, category, amount, note = row

            self.table.setItem(i, 0, QTableWidgetItem(date))
            self.table.setItem(i, 1, QTableWidgetItem(ttype))
            self.table.setItem(i, 2, QTableWidgetItem(category))
            self.table.setItem(i, 3, QTableWidgetItem(f"{amount:.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(note))

            # ---- Color rows based on type ----
            if ttype.lower() == "income":
                brush = QBrush(QColor(183, 226, 188))  # light green
                balance += amount
            else:
                brush = QBrush(QColor(255, 182, 193))  # light red
                balance -= amount

            for col in range(5):  # Apply color to all 5 text columns
                item = self.table.item(i, col)
                if item:
                    item.setBackground(brush)

            # ---- Create action buttons ----
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("edit_btn")
            edit_btn.setCursor(Qt.PointingHandCursor)
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("delete_btn")
            delete_btn.setCursor(Qt.PointingHandCursor)
            
            edit_btn.clicked.connect(lambda _, tid=trans_id: self.edit_transaction(tid))
            delete_btn.clicked.connect(lambda _, tid=trans_id: self.delete_transaction(tid))

            self.table.setCellWidget(i, 5, edit_btn)
            self.table.setCellWidget(i, 6, delete_btn)

        # --- Update balance label styling ---
        if balance > 0:
            color = "#228B22"  # forest green
            arrow = "▲"
        elif balance < 0:
            color = "#B22222"  # firebrick red
            arrow = "▼"
        else:
            color = "black"
            arrow = ""
            
        self.balance_label.setText(f"₱{balance:.2f}{arrow}")
        self.balance_label.setStyleSheet(f"color: {color};")
        self.tracked_date_label.setText(f"Tracked Since: {tracked_since_date}")

    def edit_transaction(self, trans_id):
        """Open the form pre-filled for editing"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT date, type, category, amount, note FROM transactions WHERE id = ?", (trans_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            QMessageBox.warning(self, "Error", "Transaction not found.")
            return

        # ---- Pre-fill form with existing data ----
        form = FormDialog()
        form.date_input.setDate(QDate.fromString(row[0], "MM-dd-yyyy"))
        form.type_input.setCurrentText(row[1])
        form.category_input.setText(row[2])
        form.amount_input.setText(str(row[3]))
        form.note_input.setText(row[4])

        if form.exec():
            new_data = form.get_data()
            if new_data:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE transactions
                    SET date = ?, type = ?, category = ?, amount = ?, note = ?
                    WHERE id = ?
                """, (new_data["date"], new_data["type"], new_data["category"], new_data["amount"], new_data["note"], trans_id))
                conn.commit()
                conn.close()
                self.load_transactions()

    def delete_transaction(self, trans_id):
        """Delete a row by ID"""
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this transaction?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
            conn.commit()
            conn.close()
            self.load_transactions()
    
    def add_transaction(self, data):
        """Adds row to table and saves its data inputted by users to database"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO transactions (date, type, category, amount, note)
        VALUES (?, ?, ?, ?, ?)
        """, (data["date"], data["type"], data["category"], data["amount"], data["note"]))
        conn.commit()
        conn.close()
        self.load_transactions()

    def filter_table(self, text):
        """Filter table rows based on search text."""
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

# Dynamic Path Resolution (for deploying this script as .exe)
if getattr(sys, 'frozen', False):
    # If running as a bundle (PyInstaller creates a temporary directory in sys._MEIPASS)
    base_path = sys._MEIPASS
else:
    # If running in a normal Python environment
    base_path = os.path.dirname(os.path.abspath(__file__))

STYLE = os.path.join(base_path, "style.qss")
init_db()
app = QApplication()
with open(STYLE, "r") as f:
    app.setStyleSheet(f.read())
    
window = FinanceTracker()
window.show()
app.exec()