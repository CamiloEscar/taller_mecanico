from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, 
                             QDateEdit, QTimeEdit, QComboBox, QLabel, QHeaderView,
                             QDialog, QDialogButtonBox, QFormLayout, QTextEdit)
from PyQt5.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt5.QtGui import QIcon, QColor
from database import create_connection

class ReservasTab(QWidget):
    actualizar_reservas = pyqtSignal()

    def __init__(self, comunicador):
        super().__init__()
        self.comunicador = comunicador
        self.comunicador.actualizar_datos.connect(self.cargar_clientes)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Formulario para agregar reservas
        form_layout = QHBoxLayout()
        self.cliente_combo = QComboBox()
        self.fecha_input = QDateEdit()
        self.fecha_input.setDate(QDate.currentDate())
        self.hora_input = QTimeEdit()
        self.hora_input.setTime(QTime.currentTime())
        self.descripcion_input = QLineEdit()
        self.descripcion_input.setPlaceholderText("Descripción")
        agregar_btn = QPushButton("Agregar Reserva")
        agregar_btn.setIcon(QIcon('icons/add_reservation.png'))
        agregar_btn.clicked.connect(self.agregar_reserva)

        form_layout.addWidget(QLabel("Cliente:"))
        form_layout.addWidget(self.cliente_combo)
        form_layout.addWidget(QLabel("Fecha:"))
        form_layout.addWidget(self.fecha_input)
        form_layout.addWidget(QLabel("Hora:"))
        form_layout.addWidget(self.hora_input)
        form_layout.addWidget(QLabel("Descripción:"))
        form_layout.addWidget(self.descripcion_input)
        form_layout.addWidget(agregar_btn)

        layout.addLayout(form_layout)

        # Búsqueda y filtrado
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar reserva...")
        self.search_input.textChanged.connect(self.filtrar_reservas)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todas", "Hoy", "Esta semana", "Este mes"])
        self.filter_combo.currentTextChanged.connect(self.filtrar_reservas)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.filter_combo)
        layout.addLayout(search_layout)

        # Tabla de reservas
        self.tabla_reservas = QTableWidget()
        self.tabla_reservas.setColumnCount(6)
        self.tabla_reservas.setHorizontalHeaderLabels(["ID", "Cliente", "Fecha", "Hora", "Descripción", "Estado"])
        self.tabla_reservas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_reservas.itemDoubleClicked.connect(self.editar_reserva)
        layout.addWidget(self.tabla_reservas)

        # Botones de acción
        action_layout = QHBoxLayout()
        editar_btn = QPushButton("Editar Reserva")
        editar_btn.setIcon(QIcon('icons/edit_reservation.png'))
        editar_btn.clicked.connect(self.editar_reserva_seleccionada)
        cancelar_btn = QPushButton("Cancelar Reserva")
        cancelar_btn.setIcon(QIcon('icons/cancel_reservation.png'))
        cancelar_btn.clicked.connect(self.cancelar_reserva)
        action_layout.addWidget(editar_btn)
        action_layout.addWidget(cancelar_btn)
        layout.addLayout(action_layout)

        self.setLayout(layout)
        self.cargar_clientes()
        self.cargar_reservas()

    def cargar_clientes(self):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM clientes")
        clientes = cursor.fetchall()
        conn.close()

        self.cliente_combo.clear()
        for cliente in clientes:
            self.cliente_combo.addItem(cliente[1], cliente[0])

    def agregar_reserva(self):
        cliente_id = self.cliente_combo.currentData()
        fecha = self.fecha_input.date().toString(Qt.ISODate)
        hora = self.hora_input.time().toString(Qt.ISODate)
        descripcion = self.descripcion_input.text()

        if not cliente_id:
            QMessageBox.warning(self, "Error", "Debe seleccionar un cliente")
            return

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reservas (cliente_id, fecha, hora, descripcion, estado) VALUES (?, ?, ?, ?, ?)",
                       (cliente_id, fecha, hora, descripcion, "Pendiente"))
        conn.commit()
        conn.close()

        self.descripcion_input.clear()
        self.cargar_reservas()
        self.actualizar_reservas.emit()

    def cargar_reservas(self):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, c.nombre, r.fecha, r.hora, r.descripcion, r.estado
            FROM reservas r 
            JOIN clientes c ON r.cliente_id = c.id
            ORDER BY r.fecha DESC, r.hora DESC
        """)
        reservas = cursor.fetchall()
        conn.close()

        self.tabla_reservas.setRowCount(len(reservas))
        for row, reserva in enumerate(reservas):
            for col, valor in enumerate(reserva):
                item = QTableWidgetItem(str(valor))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if col == 5:  # Columna de estado
                    if valor == "Pendiente":
                        item.setBackground(QColor(255, 255, 200))  # Amarillo claro
                    elif valor == "Completada":
                        item.setBackground(QColor(200, 255, 200))  # Verde claro
                    elif valor == "Cancelada":
                        item.setBackground(QColor(255, 200, 200))  # Rojo claro
                self.tabla_reservas.setItem(row, col, item)

        self.tabla_reservas.resizeColumnsToContents()

    def filtrar_reservas(self):
        busqueda = self.search_input.text().lower()
        filtro = self.filter_combo.currentText()
        fecha_actual = QDate.currentDate()

        for row in range(self.tabla_reservas.rowCount()):
            cliente = self.tabla_reservas.item(row, 1).text().lower()
            fecha = QDate.fromString(self.tabla_reservas.item(row, 2).text(), Qt.ISODate)
            descripcion = self.tabla_reservas.item(row, 4).text().lower()
            
            mostrar = busqueda in cliente or busqueda in descripcion
            if filtro == "Hoy" and fecha != fecha_actual:
                mostrar = False
            elif filtro == "Esta semana" and fecha < fecha_actual.addDays(-fecha_actual.dayOfWeek() + 1):
                mostrar = False
            elif filtro == "Este mes" and (fecha.year() != fecha_actual.year() or fecha.month() != fecha_actual.month()):
                mostrar = False

            self.tabla_reservas.setRowHidden(row, not mostrar)

    def editar_reserva_seleccionada(self):
        current_row = self.tabla_reservas.currentRow()
        if current_row >= 0:
            self.editar_reserva(self.tabla_reservas.item(current_row, 0))

    def editar_reserva(self, item):
        reserva_id = int(self.tabla_reservas.item(item.row(), 0).text())
        dialog = EditarReservaDialog(reserva_id, self)
        if dialog.exec_():
            self.cargar_reservas()
            self.actualizar_reservas.emit()

    def cancelar_reserva(self):
        current_row = self.tabla_reservas.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Por favor, seleccione una reserva para cancelar")
            return

        reserva_id = int(self.tabla_reservas.item(current_row, 0).text())
        cliente = self.tabla_reservas.item(current_row, 1).text()
        fecha = self.tabla_reservas.item(current_row, 2).text()
        hora = self.tabla_reservas.item(current_row, 3).text()

        reply = QMessageBox.question(self, "Confirmar cancelación",
                                     f"¿Está seguro de que desea cancelar la reserva de {cliente} para el {fecha} a las {hora}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE reservas SET estado = 'Cancelada' WHERE id = ?", (reserva_id,))
            conn.commit()
            conn.close()
            self.cargar_reservas()
            self.actualizar_reservas.emit()
            QMessageBox.information(self, "Éxito", "Reserva cancelada correctamente")

class EditarReservaDialog(QDialog):
    def __init__(self, reserva_id, parent=None):
        super().__init__(parent)
        self.reserva_id = reserva_id
        self.setWindowTitle("Editar Reserva")
        self.layout = QFormLayout(self)

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT cliente_id, fecha, hora, descripcion, estado FROM reservas WHERE id = ?", (reserva_id,))
        reserva = cursor.fetchone()
        cursor.execute("SELECT id, nombre FROM clientes")
        clientes = cursor.fetchall()
        conn.close()

        self.cliente_combo = QComboBox()
        for cliente in clientes:
            self.cliente_combo.addItem(cliente[1], cliente[0])
        self.cliente_combo.setCurrentIndex(self.cliente_combo.findData(reserva[0]))

        self.fecha_input = QDateEdit()
        self.fecha_input.setDate(QDate.fromString(reserva[1], Qt.ISODate))
        self.hora_input = QTimeEdit()
        self.hora_input.setTime(QTime.fromString(reserva[2], Qt.ISODate))
        self.descripcion_input = QTextEdit()
        self.descripcion_input.setPlainText(reserva[3])
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["Pendiente", "Completada", "Cancelada"])
        self.estado_combo.setCurrentText(reserva[4])

        self.layout.addRow("Cliente:", self.cliente_combo)
        self.layout.addRow("Fecha:", self.fecha_input)
        self.layout.addRow("Hora:", self.hora_input)
        self.layout.addRow("Descripción:", self.descripcion_input)
        self.layout.addRow("Estado:", self.estado_combo)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def accept(self):
        cliente_id = self.cliente_combo.currentData()
        fecha = self.fecha_input.date().toString(Qt.ISODate)
        hora = self.hora_input.time().toString(Qt.ISODate)
        descripcion = self.descripcion_input.toPlainText()
        estado = self.estado_combo.currentText()

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE reservas SET cliente_id = ?, fecha = ?, hora = ?, descripcion = ?, estado = ? WHERE id = ?",
                       (cliente_id, fecha, hora, descripcion, estado, self.reserva_id))
        conn.commit()
        conn.close()

        super().accept()

