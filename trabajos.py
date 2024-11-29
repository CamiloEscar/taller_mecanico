from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, 
                             QComboBox, QDateEdit, QLabel, QHeaderView,
                             QDialog, QDialogButtonBox, QFormLayout, QTextEdit)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QIcon, QColor
from database import create_connection

class TrabajosTab(QWidget):
    actualizar_trabajos = pyqtSignal()

    def __init__(self, comunicador):
        super().__init__()
        self.comunicador = comunicador
        self.comunicador.actualizar_datos.connect(self.cargar_reservas)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Formulario para agregar trabajos
        form_layout = QHBoxLayout()
        self.reserva_combo = QComboBox()
        self.descripcion_input = QLineEdit()
        self.descripcion_input.setPlaceholderText("Descripción")
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["Pendiente", "En progreso", "Completado"])
        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setDate(QDate.currentDate())
        self.fecha_fin = QDateEdit()
        self.fecha_fin.setDate(QDate.currentDate())
        agregar_btn = QPushButton("Agregar Trabajo")
        agregar_btn.setIcon(QIcon('icons/add_work.png'))
        agregar_btn.clicked.connect(self.agregar_trabajo)

        form_layout.addWidget(QLabel("Reserva:"))
        form_layout.addWidget(self.reserva_combo)
        form_layout.addWidget(QLabel("Descripción:"))
        form_layout.addWidget(self.descripcion_input)
        form_layout.addWidget(QLabel("Estado:"))
        form_layout.addWidget(self.estado_combo)
        form_layout.addWidget(QLabel("Fecha Inicio:"))
        form_layout.addWidget(self.fecha_inicio)
        form_layout.addWidget(QLabel("Fecha Fin:"))
        form_layout.addWidget(self.fecha_fin)
        form_layout.addWidget(agregar_btn)

        layout.addLayout(form_layout)

        # Búsqueda y filtrado
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar trabajo...")
        self.search_input.textChanged.connect(self.filtrar_trabajos)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos", "Pendientes", "En progreso", "Completados"])
        self.filter_combo.currentTextChanged.connect(self.filtrar_trabajos)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.filter_combo)
        layout.addLayout(search_layout)

        # Tabla de trabajos
        self.tabla_trabajos = QTableWidget()
        self.tabla_trabajos.setColumnCount(7)
        self.tabla_trabajos.setHorizontalHeaderLabels(["ID", "Reserva", "Descripción", "Estado", "Fecha Inicio", "Fecha Fin", "Duración"])
        self.tabla_trabajos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_trabajos.itemDoubleClicked.connect(self.editar_trabajo)
        layout.addWidget(self.tabla_trabajos)

        # Botones de acción
        action_layout = QHBoxLayout()
        editar_btn = QPushButton("Editar Trabajo")
        editar_btn.setIcon(QIcon('icons/edit_work.png'))
        editar_btn.clicked.connect(self.editar_trabajo_seleccionado)
        eliminar_btn = QPushButton("Eliminar Trabajo")
        eliminar_btn.setIcon(QIcon('icons/delete_work.png'))
        eliminar_btn.clicked.connect(self.eliminar_trabajo)
        action_layout.addWidget(editar_btn)
        action_layout.addWidget(eliminar_btn)
        layout.addLayout(action_layout)

        self.setLayout(layout)
        self.cargar_reservas()
        self.cargar_trabajos()

    def cargar_reservas(self):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, c.nombre || ' - ' || r.fecha || ' ' || r.hora
            FROM reservas r 
            JOIN clientes c ON r.cliente_id = c.id
            WHERE r.estado != 'Cancelada'
            ORDER BY r.fecha DESC, r.hora DESC
        """)
        reservas = cursor.fetchall()
        conn.close()

        self.reserva_combo.clear()
        for reserva in reservas:
            self.reserva_combo.addItem(reserva[1], reserva[0])

    def agregar_trabajo(self):
        reserva_id = self.reserva_combo.currentData()
        descripcion = self.descripcion_input.text()
        estado = self.estado_combo.currentText()
        fecha_inicio = self.fecha_inicio.date().toString(Qt.ISODate)
        fecha_fin = self.fecha_fin.date().toString(Qt.ISODate)

        if not reserva_id or not descripcion:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios")
            return

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trabajos (reserva_id, descripcion, estado, fecha_inicio, fecha_fin)
            VALUES (?, ?, ?, ?, ?)
        """, (reserva_id, descripcion, estado, fecha_inicio, fecha_fin))
        conn.commit()
        conn.close()

        self.descripcion_input.clear()
        self.cargar_trabajos()
        self.actualizar_trabajos.emit()

    def cargar_trabajos(self):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, c.nombre || ' - ' || r.fecha || ' ' || r.hora, t.descripcion, t.estado, t.fecha_inicio, t.fecha_fin,
                   CASE 
                       WHEN t.fecha_fin IS NOT NULL THEN julianday(t.fecha_fin) - julianday(t.fecha_inicio)
                       ELSE julianday('now') - julianday(t.fecha_inicio)
                   END as duracion
            FROM trabajos t
            JOIN reservas r ON t.reserva_id = r.id
            JOIN clientes c ON r.cliente_id = c.id
            ORDER BY t.fecha_inicio DESC
        """)
        trabajos = cursor.fetchall()
        conn.close()

        self.tabla_trabajos.setRowCount(len(trabajos))
        for row, trabajo in enumerate(trabajos):
            for col, valor in enumerate(trabajo):
                item = QTableWidgetItem(str(valor))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if col == 3:  # Columna de estado
                    if valor == "Pendiente":
                        item.setBackground(QColor(255, 255, 200))  # Amarillo claro
                    elif valor == "En progreso":
                        item.setBackground(QColor(200, 200, 255))  # Azul claro
                    elif valor == "Completado":
                        item.setBackground(QColor(200, 255, 200))  # Verde claro
                elif col == 6:  # Columna de duración
                    item.setText(f"{valor:.2f} días")
                self.tabla_trabajos.setItem(row, col, item)

        self.tabla_trabajos.resizeColumnsToContents()

    def filtrar_trabajos(self):
        busqueda = self.search_input.text().lower()
        filtro = self.filter_combo.currentText()

        for row in range(self.tabla_trabajos.rowCount()):
            reserva = self.tabla_trabajos.item(row, 1).text().lower()
            descripcion = self.tabla_trabajos.item(row, 2).text().lower()
            estado = self.tabla_trabajos.item(row, 3).text()
            
            mostrar = busqueda in reserva or busqueda in descripcion
            if filtro != "Todos" and estado != filtro:
                mostrar = False

            self.tabla_trabajos.setRowHidden(row, not mostrar)

    def editar_trabajo_seleccionado(self):
        current_row = self.tabla_trabajos.currentRow()
        if current_row >= 0:
            self.editar_trabajo(self.tabla_trabajos.item(current_row, 0))

    def editar_trabajo(self, item):
        trabajo_id = int(self.tabla_trabajos.item(item.row(), 0).text())
        dialog = EditarTrabajoDialog(trabajo_id, self)
        if dialog.exec_():
            self.cargar_trabajos()
            self.actualizar_trabajos.emit()

    def eliminar_trabajo(self):
        current_row = self.tabla_trabajos.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Por favor, seleccione un trabajo para eliminar")
            return

        trabajo_id = int(self.tabla_trabajos.item(current_row, 0).text())
        descripcion = self.tabla_trabajos.item(current_row, 2).text()

        reply = QMessageBox.question(self, "Confirmar eliminación",
                                     f"¿Está seguro de que desea eliminar el trabajo '{descripcion}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM trabajos WHERE id = ?", (trabajo_id,))
            conn.commit()
            conn.close()
            self.cargar_trabajos()
            self.actualizar_trabajos.emit()
            QMessageBox.information(self, "Éxito", f"Trabajo '{descripcion}' eliminado correctamente")

class EditarTrabajoDialog(QDialog):
    def __init__(self, trabajo_id, parent=None):
        super().__init__(parent)
        self.trabajo_id = trabajo_id
        self.setWindowTitle("Editar Trabajo")
        self.layout = QFormLayout(self)

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT reserva_id, descripcion, estado, fecha_inicio, fecha_fin FROM trabajos WHERE id = ?", (trabajo_id,))
        trabajo = cursor.fetchone()
        cursor.execute("""
            SELECT r.id, c.nombre || ' - ' || r.fecha || ' ' || r.hora
            FROM reservas r
            JOIN clientes c ON r.cliente_id = c.id
            WHERE r.estado != 'Cancelada'
        """)
        reservas = cursor.fetchall()
        conn.close()

        self.reserva_combo = QComboBox()
        for reserva in reservas:
            self.reserva_combo.addItem(reserva[1], reserva[0])
        self.reserva_combo.setCurrentIndex(self.reserva_combo.findData(trabajo[0]))

        self.descripcion_input = QTextEdit()
        self.descripcion_input.setPlainText(trabajo[1])
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["Pendiente", "En progreso", "Completado"])
        self.estado_combo.setCurrentText(trabajo[2])
        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setDate(QDate.fromString(trabajo[3], Qt.ISODate))
        self.fecha_fin = QDateEdit()
        if trabajo[4]:
            self.fecha_fin.setDate(QDate.fromString(trabajo[4], Qt.ISODate))
        else:
            self.fecha_fin.setDate(QDate.currentDate())

        self.layout.addRow("Reserva:", self.reserva_combo)
        self.layout.addRow("Descripción:", self.descripcion_input)
        self.layout.addRow("Estado:", self.estado_combo)
        self.layout.addRow("Fecha Inicio:", self.fecha_inicio)
        self.layout.addRow("Fecha Fin:", self.fecha_fin)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def accept(self):
        reserva_id = self.reserva_combo.currentData()
        descripcion = self.descripcion_input.toPlainText()
        estado = self.estado_combo.currentText()
        fecha_inicio = self.fecha_inicio.date().toString(Qt.ISODate)
        fecha_fin = self.fecha_fin.date().toString(Qt.ISODate)

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE trabajos 
            SET reserva_id = ?, descripcion = ?, estado = ?, fecha_inicio = ?, fecha_fin = ? 
            WHERE id = ?
        """, (reserva_id, descripcion, estado, fecha_inicio, fecha_fin, self.trabajo_id))
        conn.commit()
        conn.close()

        super().accept()

