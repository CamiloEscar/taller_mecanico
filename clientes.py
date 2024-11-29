from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
                             QLabel, QHeaderView, QComboBox, QDialog, QFormLayout,
                             QDialogButtonBox, QDateEdit, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QIcon, QColor
from database import create_connection

class ClientesTab(QWidget):
    actualizar_clientes = pyqtSignal()

    def __init__(self, comunicador):
        super().__init__()
        self.comunicador = comunicador
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Formulario para agregar clientes
        form_layout = QHBoxLayout()
        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Nombre")
        self.telefono_input = QLineEdit()
        self.telefono_input.setPlaceholderText("Teléfono")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        agregar_btn = QPushButton("Agregar Cliente")
        agregar_btn.setIcon(QIcon('icons/add_user.png'))
        agregar_btn.clicked.connect(self.agregar_cliente)

        form_layout.addWidget(self.nombre_input)
        form_layout.addWidget(self.telefono_input)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(agregar_btn)

        layout.addLayout(form_layout)

        # Búsqueda y filtrado
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar cliente...")
        self.search_input.textChanged.connect(self.filtrar_clientes)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos", "Clientes frecuentes", "Clientes nuevos"])
        self.filter_combo.currentTextChanged.connect(self.filtrar_clientes)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.filter_combo)
        layout.addLayout(search_layout)

        # Tabla de clientes
        self.tabla_clientes = QTableWidget()
        self.tabla_clientes.setColumnCount(5)
        self.tabla_clientes.setHorizontalHeaderLabels(["ID", "Nombre", "Teléfono", "Email", "Última visita"])
        self.tabla_clientes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_clientes.itemDoubleClicked.connect(self.editar_cliente)
        layout.addWidget(self.tabla_clientes)

        # Botones de acción
        action_layout = QHBoxLayout()
        editar_btn = QPushButton("Editar Cliente")
        editar_btn.setIcon(QIcon('icons/edit_user.png'))
        editar_btn.clicked.connect(self.editar_cliente_seleccionado)
        eliminar_btn = QPushButton("Eliminar Cliente")
        eliminar_btn.setIcon(QIcon('icons/delete_user.png'))
        eliminar_btn.clicked.connect(self.eliminar_cliente)
        historial_btn = QPushButton("Ver Historial")
        historial_btn.setIcon(QIcon('icons/history.png'))
        historial_btn.clicked.connect(self.ver_historial)
        action_layout.addWidget(editar_btn)
        action_layout.addWidget(eliminar_btn)
        action_layout.addWidget(historial_btn)
        layout.addLayout(action_layout)

        self.setLayout(layout)
        self.cargar_clientes()

    def agregar_cliente(self):
        nombre = self.nombre_input.text()
        telefono = self.telefono_input.text()
        email = self.email_input.text()

        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre del cliente es obligatorio")
            return

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO clientes (nombre, telefono, email) VALUES (?, ?, ?)",
                       (nombre, telefono, email))
        conn.commit()
        conn.close()

        self.nombre_input.clear()
        self.telefono_input.clear()
        self.email_input.clear()
        self.cargar_clientes()
        self.comunicador.actualizar_datos.emit()

    def cargar_clientes(self):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.nombre, c.telefono, c.email, MAX(r.fecha) as ultima_visita
            FROM clientes c
            LEFT JOIN reservas r ON c.id = r.cliente_id
            GROUP BY c.id
        """)
        clientes = cursor.fetchall()
        conn.close()

        self.tabla_clientes.setRowCount(len(clientes))
        for row, cliente in enumerate(clientes):
            for col, valor in enumerate(cliente):
                item = QTableWidgetItem(str(valor) if valor is not None else "")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.tabla_clientes.setItem(row, col, item)

        self.tabla_clientes.resizeColumnsToContents()

    def filtrar_clientes(self):
        busqueda = self.search_input.text().lower()
        filtro = self.filter_combo.currentText()

        for row in range(self.tabla_clientes.rowCount()):
            cliente_nombre = self.tabla_clientes.item(row, 1).text().lower()
            ultima_visita = self.tabla_clientes.item(row, 4).text()
            
            mostrar = busqueda in cliente_nombre
            if filtro == "Clientes frecuentes" and (not ultima_visita or QDate.fromString(ultima_visita, Qt.ISODate) < QDate.currentDate().addMonths(-3)):
                mostrar = False
            elif filtro == "Clientes nuevos" and ultima_visita and QDate.fromString(ultima_visita, Qt.ISODate) < QDate.currentDate().addMonths(-1):
                mostrar = False

            self.tabla_clientes.setRowHidden(row, not mostrar)

    def editar_cliente_seleccionado(self):
        current_row = self.tabla_clientes.currentRow()
        if current_row >= 0:
            self.editar_cliente(self.tabla_clientes.item(current_row, 0))

    def editar_cliente(self, item):
        cliente_id = int(self.tabla_clientes.item(item.row(), 0).text())
        dialog = EditarClienteDialog(cliente_id, self)
        if dialog.exec_():
            self.cargar_clientes()
            self.comunicador.actualizar_datos.emit()

    def eliminar_cliente(self):
        current_row = self.tabla_clientes.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Por favor, seleccione un cliente para eliminar")
            return

        cliente_id = int(self.tabla_clientes.item(current_row, 0).text())
        cliente_nombre = self.tabla_clientes.item(current_row, 1).text()

        reply = QMessageBox.question(self, "Confirmar eliminación",
                                     f"¿Está seguro de que desea eliminar al cliente '{cliente_nombre}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
            conn.commit()
            conn.close()
            self.cargar_clientes()
            self.comunicador.actualizar_datos.emit()
            QMessageBox.information(self, "Éxito", f"Cliente '{cliente_nombre}' eliminado correctamente")

    def ver_historial(self):
        current_row = self.tabla_clientes.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Por favor, seleccione un cliente para ver su historial")
            return

        cliente_id = int(self.tabla_clientes.item(current_row, 0).text())
        cliente_nombre = self.tabla_clientes.item(current_row, 1).text()

        dialog = HistorialClienteDialog(cliente_id, cliente_nombre, self)
        dialog.exec_()

class EditarClienteDialog(QDialog):
    def __init__(self, cliente_id, parent=None):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.setWindowTitle("Editar Cliente")
        self.layout = QFormLayout(self)

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, telefono, email FROM clientes WHERE id = ?", (cliente_id,))
        cliente = cursor.fetchone()
        conn.close()

        self.nombre_input = QLineEdit(cliente[0])
        self.telefono_input = QLineEdit(cliente[1])
        self.email_input = QLineEdit(cliente[2])

        self.layout.addRow("Nombre:", self.nombre_input)
        self.layout.addRow("Teléfono:", self.telefono_input)
        self.layout.addRow("Email:", self.email_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def accept(self):
        nombre = self.nombre_input.text()
        telefono = self.telefono_input.text()
        email = self.email_input.text()

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE clientes SET nombre = ?, telefono = ?, email = ? WHERE id = ?",
                       (nombre, telefono, email, self.cliente_id))
        conn.commit()
        conn.close()

        super().accept()

class HistorialClienteDialog(QDialog):
    def __init__(self, cliente_id, cliente_nombre, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Historial de {cliente_nombre}")
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)

        self.tabla_historial = QTableWidget()
        self.tabla_historial.setColumnCount(4)
        self.tabla_historial.setHorizontalHeaderLabels(["Fecha", "Tipo", "Descripción", "Monto"])
        self.tabla_historial.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla_historial)

        self.cargar_historial(cliente_id)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Close, self)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def cargar_historial(self, cliente_id):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.fecha, 'Reserva' as tipo, r.descripcion, NULL as monto
            FROM reservas r
            WHERE r.cliente_id = ?
            UNION ALL
            SELECT f.fecha, 'Factura' as tipo, t.descripcion, f.monto
            FROM facturas f
            JOIN trabajos t ON f.trabajo_id = t.id
            JOIN reservas r ON t.reserva_id = r.id
            WHERE r.cliente_id = ?
            ORDER BY fecha DESC
        """, (cliente_id, cliente_id))
        historial = cursor.fetchall()
        conn.close()

        self.tabla_historial.setRowCount(len(historial))
        for row, evento in enumerate(historial):
            for col, valor in enumerate(evento):
                item = QTableWidgetItem(str(valor) if valor is not None else "")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if col == 3 and valor is not None:  # Columna de monto
                    item.setText(f"${valor:.2f}")
                self.tabla_historial.setItem(row, col, item)

        self.tabla_historial.resizeColumnsToContents()

