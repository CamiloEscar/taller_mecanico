from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, 
                             QLabel, QHeaderView,
                             QDialog, QDialogButtonBox, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from database import create_connection

class ProveedoresTab(QWidget):
    actualizar_proveedores = pyqtSignal()

    def __init__(self, comunicador):
        super().__init__()
        self.comunicador = comunicador
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Formulario para agregar proveedores
        form_layout = QHBoxLayout()
        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Nombre")
        self.telefono_input = QLineEdit()
        self.telefono_input.setPlaceholderText("Teléfono")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.direccion_input = QLineEdit()
        self.direccion_input.setPlaceholderText("Dirección")
        agregar_btn = QPushButton("Agregar Proveedor")
        agregar_btn.setIcon(QIcon('icons/add_supplier.png'))
        agregar_btn.clicked.connect(self.agregar_proveedor)

        form_layout.addWidget(self.nombre_input)
        form_layout.addWidget(self.telefono_input)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.direccion_input)
        form_layout.addWidget(agregar_btn)

        layout.addLayout(form_layout)

        # Tabla de proveedores
        self.tabla_proveedores = QTableWidget()
        self.tabla_proveedores.setColumnCount(5)
        self.tabla_proveedores.setHorizontalHeaderLabels(["ID", "Nombre", "Teléfono", "Email", "Dirección"])
        self.tabla_proveedores.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_proveedores.itemDoubleClicked.connect(self.editar_proveedor)
        layout.addWidget(self.tabla_proveedores)

        # Botones de acción
        action_layout = QHBoxLayout()
        editar_btn = QPushButton("Editar Proveedor")
        editar_btn.setIcon(QIcon('icons/edit_supplier.png'))
        editar_btn.clicked.connect(self.editar_proveedor_seleccionado)
        eliminar_btn = QPushButton("Eliminar Proveedor")
        eliminar_btn.setIcon(QIcon('icons/delete_supplier.png'))
        eliminar_btn.clicked.connect(self.eliminar_proveedor)
        action_layout.addWidget(editar_btn)
        action_layout.addWidget(eliminar_btn)
        layout.addLayout(action_layout)

        self.setLayout(layout)
        self.cargar_proveedores()

    def agregar_proveedor(self):
        nombre = self.nombre_input.text()
        telefono = self.telefono_input.text()
        email = self.email_input.text()
        direccion = self.direccion_input.text()

        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre del proveedor es obligatorio")
            return

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO proveedores (nombre, telefono, email, direccion) VALUES (?, ?, ?, ?)",
                       (nombre, telefono, email, direccion))
        conn.commit()
        conn.close()

        self.nombre_input.clear()
        self.telefono_input.clear()
        self.email_input.clear()
        self.direccion_input.clear()
        self.cargar_proveedores()
        self.actualizar_proveedores.emit()

    def cargar_proveedores(self):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM proveedores")
        proveedores = cursor.fetchall()
        conn.close()

        self.tabla_proveedores.setRowCount(len(proveedores))
        for row, proveedor in enumerate(proveedores):
            for col, valor in enumerate(proveedor):
                item = QTableWidgetItem(str(valor))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.tabla_proveedores.setItem(row, col, item)

        self.tabla_proveedores.resizeColumnsToContents()

    def editar_proveedor_seleccionado(self):
        current_row = self.tabla_proveedores.currentRow()
        if current_row >= 0:
            self.editar_proveedor(self.tabla_proveedores.item(current_row, 0))

    def editar_proveedor(self, item):
        proveedor_id = int(self.tabla_proveedores.item(item.row(), 0).text())
        dialog = EditarProveedorDialog(proveedor_id, self)
        if dialog.exec_():
            self.cargar_proveedores()
            self.actualizar_proveedores.emit()

    def eliminar_proveedor(self):
        current_row = self.tabla_proveedores.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Por favor, seleccione un proveedor para eliminar")
            return

        proveedor_id = int(self.tabla_proveedores.item(current_row, 0).text())
        nombre_proveedor = self.tabla_proveedores.item(current_row, 1).text()

        reply = QMessageBox.question(self, "Confirmar eliminación",
                                     f"¿Está seguro de que desea eliminar al proveedor '{nombre_proveedor}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM proveedores WHERE id = ?", (proveedor_id,))
            conn.commit()
            conn.close()
            self.cargar_proveedores()
            self.actualizar_proveedores.emit()
            QMessageBox.information(self, "Éxito", f"Proveedor '{nombre_proveedor}' eliminado correctamente")

class EditarProveedorDialog(QDialog):
    def __init__(self, proveedor_id, parent=None):
        super().__init__(parent)
        self.proveedor_id = proveedor_id
        self.setWindowTitle("Editar Proveedor")
        self.layout = QFormLayout(self)

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, telefono, email, direccion FROM proveedores WHERE id = ?", (proveedor_id,))
        proveedor = cursor.fetchone()
        conn.close()

        self.nombre_input = QLineEdit(proveedor[0])
        self.telefono_input = QLineEdit(proveedor[1])
        self.email_input = QLineEdit(proveedor[2])
        self.direccion_input = QLineEdit(proveedor[3])

        self.layout.addRow("Nombre:", self.nombre_input)
        self.layout.addRow("Teléfono:", self.telefono_input)
        self.layout.addRow("Email:", self.email_input)
        self.layout.addRow("Dirección:", self.direccion_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def accept(self):
        nombre = self.nombre_input.text()
        telefono = self.telefono_input.text()
        email = self.email_input.text()
        direccion = self.direccion_input.text()

        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre del proveedor es obligatorio")
            return

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE proveedores SET nombre = ?, telefono = ?, email = ?, direccion = ? WHERE id = ?",
                       (nombre, telefono, email, direccion, self.proveedor_id))
        conn.commit()
        conn.close()

        super().accept()

