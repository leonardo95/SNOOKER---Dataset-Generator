import psycopg2
from psycopg2.extensions import connection
from PyQt5.QtCore import pyqtSignal
from Code.InterfaceUtils import InterfaceUtils 
from PyQt5.QtWidgets import QMainWindow, QLabel, QLineEdit, QPushButton

class SQLConnectionWindow(QMainWindow):
    
    dataSubmitted = pyqtSignal(connection)  # Signal with tuple type
    def __init__(self):
        super().__init__()

        # Set window title
        self.setWindowTitle("SQL Connection Configuration")

        # Create QLabel widgets
        label1 = QLabel("Host:", self)
        label1.move(20, 20)
        label2 = QLabel("Port:", self)
        label2.move(20, 60)
        label3 = QLabel("Database:", self)
        label3.move(20, 100)
        label4 = QLabel("User:", self)
        label4.move(20, 140)
        label5 = QLabel("Password:", self)
        label5.move(20, 180)

        # Create QLineEdit widgets
        self.hostEdit = QLineEdit(self)
        self.hostEdit.setGeometry(80, 20, 200, 20)
        self.portEdit = QLineEdit(self)
        self.portEdit.setGeometry(80, 60, 200, 20)
        self.databaseEdit = QLineEdit(self)
        self.databaseEdit.setGeometry(80, 100, 200, 20)
        self.userEdit = QLineEdit(self)
        self.userEdit.setGeometry(80, 140, 200, 20)
        self.passwordEdit = QLineEdit(self)
        self.passwordEdit.setEchoMode(QLineEdit.Password)
        self.passwordEdit.setGeometry(80, 180, 200, 20)

        # Create QPushButton widget
        button = QPushButton("Submit", self)
        button.setGeometry(120, 230, 80, 30)
        button.clicked.connect(self.submitClicked)

    def submitClicked(self):
        host = self.hostEdit.text()
        port = self.portEdit.text()
        database = self.databaseEdit.text()
        user = self.userEdit.text()
        password = self.passwordEdit.text()
        
        
        if host.strip() == '' or port.strip() == '' or database.strip() == '' or user.strip() == '' or password.strip() == '':
            print("There are empty fields")
            InterfaceUtils.pop_message(self, "Error", "Some parameters are missing! ")
        else:
            print("host:", host)
            print("port:", port)
            print("database:", database)
            print("user:", user)
            print("password:", password)
            try: 
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    database=database,
                    user=user,
                    password=password)
                print("Connection established")
                self.dataSubmitted.emit(conn)
                self.close()
                
            except psycopg2.OperationalError as e:
                print(e)