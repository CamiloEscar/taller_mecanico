from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QDateEdit, QLineEdit,
                             QLabel, QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon
from database import create_connection

class RecordatoriosTab(QWidget):
    def __init__(self, comunicador):
        super().__init__()
        self.comunicador = comunicador
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Formulario para agregar recordatorios
        form_layout = QHBoxLayout()
        self.cliente_input = QLineEdit()
        self.cliente_input.setPlaceholderText("Cliente")
        self.fecha_input = QDateEdit()
        self.fecha_input.setDate(QDate.currentDate())
        self.descripcion_input = QLineEdit()
        self.descripcion_input.setPlaceholderText("Descripción")
        agregar_btn = QPushButton("Agregar Recordatorio")
        agregar_btn.setIcon(QIcon('icons/add.png'))
        agregar_btn.clicked.connect(self.agregar_recordatorio)

        form_layout.addWidget(QLabel("Cliente:"))
        form_layout.addWidget(self.cliente_input)
        form_layout.addWidget(QLabel("Fecha:"))
        form_layout.addWidget(self.fecha_input)
        form_layout.addWidget(QLabel("Descripción:"))
        form_layout.addWidget(self.descripcion_input)
        form_layout.addWidget(agregar_btn)

        layout.addLayout(form_layout)

        # Tabla de recordatorios
        self.tabla_recordatorios = QTableWidget()
        self.tabla_recordatorios.setColumnCount(4)
        self.tabla_recordatorios.setHorizontalHeaderLabels(["ID", "Cliente", "Fecha", "Descripción"])
        self.tabla_recordatorios.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla_recordatorios)

        self.setLayout(layout)
        self.cargar_recordatorios()

    def agregar_recordatorio(self):
        cliente = self.cliente_input.text()
        fecha = self.fecha_input.date().toString(Qt.ISODate)
        descripcion = self.descripcion_input.text()

        if not cliente or not descripcion:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios")
            return

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO recordatorios (cliente, fecha, descripcion)
            VALUES (?, ?, ?)
        """, (cliente, fecha, descripcion))
        conn.commit()
        conn.close()

        self.cliente_input.clear()
        self.descripcion_input.clear()
        self.cargar_recordatorios()

    def cargar_recordatorios(self):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recordatorios ORDER BY fecha")
        recordatorios = cursor.fetchall()
        conn.close()

        self.tabla_recordatorios.setRowCount(len(recordatorios))
        for row, recordatorio in enumerate(recordatorios):
            for col, valor in enumerate(recordatorio):
                item = QTableWidgetItem(str(valor))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.tabla_recordatorios.setItem(row, col, item)

        self.tabla_recordatorios.resizeColumnsToContents()

