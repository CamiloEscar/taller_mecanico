from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, 
                             QComboBox, QLabel, QHeaderView, QSpinBox,
                             QDialog, QDialogButtonBox, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from database import create_connection

class VehiculosTab(QWidget):
    actualizar_vehiculos = pyqtSignal()

    def __init__(self, comunicador):
        super().__init__()
        self.comunicador = comunicador
        self.comunicador.actualizar_datos.connect(self.cargar_clientes)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Formulario para agregar vehículos
        form_layout = QHBoxLayout()
        self.cliente_combo = QComboBox()
        self.matricula_input = QLineEdit()
        self.matricula_input.setPlaceholderText("Matrícula")
        self.marca_input = QLineEdit()
        self.marca_input.setPlaceholderText("Marca")
        self.modelo_input = QLineEdit()
        self.modelo_input.setPlaceholderText("Modelo")
        self.anio_input = QSpinBox()
        self.anio_input.setRange(1900, 2100)
        self.anio_input.setValue(2023)
        self.kilometraje_input = QSpinBox()
        self.kilometraje_input.setRange(0, 1000000)
        self.kilometraje_input.setSuffix(" km")
        agregar_btn = QPushButton("Agregar Vehículo")
        agregar_btn.setIcon(QIcon('icons/add_car.png'))
        agregar_btn.clicked.connect(self.agregar_vehiculo)

        form_layout.addWidget(QLabel("Cliente:"))
        form_layout.addWidget(self.cliente_combo)
        form_layout.addWidget(QLabel("Matrícula:"))
        form_layout.addWidget(self.matricula_input)
        form_layout.addWidget(QLabel("Marca:"))
        form_layout.addWidget(self.marca_input)
        form_layout.addWidget(QLabel("Modelo:"))
        form_layout.addWidget(self.modelo_input)
        form_layout.addWidget(QLabel("Año:"))
        form_layout.addWidget(self.anio_input)
        form_layout.addWidget(QLabel("Kilometraje:"))
        form_layout.addWidget(self.kilometraje_input)
        form_layout.addWidget(agregar_btn)

        layout.addLayout(form_layout)

        # Tabla de vehículos
        self.tabla_vehiculos = QTableWidget()
        self.tabla_vehiculos.setColumnCount(7)
        self.tabla_vehiculos.setHorizontalHeaderLabels(["ID", "Cliente", "Matrícula", "Marca", "Modelo", "Año", "Kilometraje"])
        self.tabla_vehiculos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_vehiculos.itemDoubleClicked.connect(self.editar_vehiculo)
        layout.addWidget(self.tabla_vehiculos)

        # Botones de acción
        action_layout = QHBoxLayout()
        editar_btn = QPushButton("Editar Vehículo")
        editar_btn.setIcon(QIcon('icons/edit_car.png'))
        editar_btn.clicked.connect(self.editar_vehiculo_seleccionado)
        eliminar_btn = QPushButton("Eliminar Vehículo")
        eliminar_btn.setIcon(QIcon('icons/delete_car.png'))
        eliminar_btn.clicked.connect(self.eliminar_vehiculo)
        action_layout.addWidget(editar_btn)
        action_layout.addWidget(eliminar_btn)
        layout.addLayout(action_layout)

        self.setLayout(layout)
        self.cargar_clientes()
        self.cargar_vehiculos()

    def cargar_clientes(self):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM clientes")
        clientes = cursor.fetchall()
        conn.close()

        self.cliente_combo.clear()
        for cliente in clientes:
            self.cliente_combo.addItem(cliente[1], cliente[0])

    def agregar_vehiculo(self):
        cliente_id = self.cliente_combo.currentData()
        matricula = self.matricula_input.text()
        marca = self.marca_input.text()
        modelo = self.modelo_input.text()
        anio = self.anio_input.value()
        kilometraje = self.kilometraje_input.value()

        if not cliente_id or not matricula or not marca or not modelo:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios")
            return

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO vehiculos (cliente_id, matricula, marca, modelo, anio, kilometraje)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cliente_id, matricula, marca, modelo, anio, kilometraje))
        conn.commit()
        conn.close()

        self.matricula_input.clear()
        self.marca_input.clear()
        self.modelo_input.clear()
        self.anio_input.setValue(2023)
        self.kilometraje_input.setValue(0)
        self.cargar_vehiculos()
        self.actualizar_vehiculos.emit()

    def cargar_vehiculos(self):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.id, c.nombre, v.matricula, v.marca, v.modelo, v.anio, v.kilometraje
            FROM vehiculos v
            JOIN clientes c ON v.cliente_id = c.id
            ORDER BY c.nombre, v.marca, v.modelo
        """)
        vehiculos = cursor.fetchall()
        conn.close()

        self.tabla_vehiculos.setRowCount(len(vehiculos))
        for row, vehiculo in enumerate(vehiculos):
            for col, valor in enumerate(vehiculo):
                item = QTableWidgetItem(str(valor))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.tabla_vehiculos.setItem(row, col, item)

        self.tabla_vehiculos.resizeColumnsToContents()

    def editar_vehiculo_seleccionado(self):
        current_row = self.tabla_vehiculos.currentRow()
        if current_row >= 0:
            self.editar_vehiculo(self.tabla_vehiculos.item(current_row, 0))

    def editar_vehiculo(self, item):
        vehiculo_id = int(self.tabla_vehiculos.item(item.row(), 0).text())
        dialog = EditarVehiculoDialog(vehiculo_id, self)
        if dialog.exec_():
            self.cargar_vehiculos()
            self.actualizar_vehiculos.emit()

    def eliminar_vehiculo(self):
        current_row = self.tabla_vehiculos.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Por favor, seleccione un vehículo para eliminar")
            return

        vehiculo_id = int(self.tabla_vehiculos.item(current_row, 0).text())
        matricula = self.tabla_vehiculos.item(current_row, 2).text()

        reply = QMessageBox.question(self, "Confirmar eliminación",
                                     f"¿Está seguro de que desea eliminar el vehículo con matrícula '{matricula}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vehiculos WHERE id = ?", (vehiculo_id,))
            conn.commit()
            conn.close()
            self.cargar_vehiculos()
            self.actualizar_vehiculos.emit()
            QMessageBox.information(self, "Éxito", f"Vehículo con matrícula '{matricula}' eliminado correctamente")

class EditarVehiculoDialog(QDialog):
    def __init__(self, vehiculo_id, parent=None):
        super().__init__(parent)
        self.vehiculo_id = vehiculo_id
        self.setWindowTitle("Editar Vehículo")
        self.layout = QFormLayout(self)

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT cliente_id, matricula, marca, modelo, anio, kilometraje FROM vehiculos WHERE id = ?", (vehiculo_id,))
        vehiculo = cursor.fetchone()
        cursor.execute("SELECT id, nombre FROM clientes")
        clientes = cursor.fetchall()
        conn.close()

        self.cliente_combo = QComboBox()
        for cliente in clientes:
            self.cliente_combo.addItem(cliente[1], cliente[0])
        self.cliente_combo.setCurrentIndex(self.cliente_combo.findData(vehiculo[0]))

        self.matricula_input = QLineEdit(vehiculo[1])
        self.marca_input = QLineEdit(vehiculo[2])
        self.modelo_input = QLineEdit(vehiculo[3])
        self.anio_input = QSpinBox()
        self.anio_input.setRange(1900, 2100)
        self.anio_input.setValue(vehiculo[4])
        self.kilometraje_input = QSpinBox()
        self.kilometraje_input.setRange(0, 1000000)
        self.kilometraje_input.setValue(vehiculo[5])
        self.kilometraje_input.setSuffix(" km")

        self.layout.addRow("Cliente:", self.cliente_combo)
        self.layout.addRow("Matrícula:", self.matricula_input)
        self.layout.addRow("Marca:", self.marca_input)
        self.layout.addRow("Modelo:", self.modelo_input)
        self.layout.addRow("Año:", self.anio_input)
        self.layout.addRow("Kilometraje:", self.kilometraje_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def accept(self):
        cliente_id = self.cliente_combo.currentData()
        matricula = self.matricula_input.text()
        marca = self.marca_input.text()
        modelo = self.modelo_input.text()
        anio = self.anio_input.value()
        kilometraje = self.kilometraje_input.value()

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE vehiculos 
            SET cliente_id = ?, matricula = ?, marca = ?, modelo = ?, anio = ?, kilometraje = ? 
            WHERE id = ?
        """, (cliente_id, matricula, marca, modelo, anio, kilometraje, self.vehiculo_id))
        conn.commit()
        conn.close()

        super().accept()

