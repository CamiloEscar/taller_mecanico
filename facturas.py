from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, 
                             QComboBox, QDateEdit, QDoubleSpinBox, QLabel, QHeaderView,
                             QDialog, QDialogButtonBox, QFormLayout, QTextEdit, QInputDialog)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QIcon, QColor
from database import create_connection
import pywhatkit
import qrcode
from PyQt5.QtWidgets import QFileDialog

class FacturasTab(QWidget):
    actualizar_facturas = pyqtSignal()

    def __init__(self, comunicador):
        super().__init__()
        self.comunicador = comunicador
        self.comunicador.actualizar_datos.connect(self.cargar_trabajos)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Formulario para agregar facturas
        form_layout = QHBoxLayout()
        self.trabajo_combo = QComboBox()
        self.fecha_input = QDateEdit()
        self.fecha_input.setDate(QDate.currentDate())
        self.monto_input = QDoubleSpinBox()
        self.monto_input.setRange(0, 1000000)
        self.monto_input.setPrefix("$")
        self.monto_input.setDecimals(2)
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["Pendiente", "Pagada"])
        agregar_btn = QPushButton("Agregar Factura")
        agregar_btn.setIcon(QIcon('icons/add_invoice.png'))
        agregar_btn.clicked.connect(self.agregar_factura)

        form_layout.addWidget(QLabel("Trabajo:"))
        form_layout.addWidget(self.trabajo_combo)
        form_layout.addWidget(QLabel("Fecha:"))
        form_layout.addWidget(self.fecha_input)
        form_layout.addWidget(QLabel("Monto:"))
        form_layout.addWidget(self.monto_input)
        form_layout.addWidget(QLabel("Estado:"))
        form_layout.addWidget(self.estado_combo)
        form_layout.addWidget(agregar_btn)

        layout.addLayout(form_layout)

        # Búsqueda y filtrado
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar factura...")
        self.search_input.textChanged.connect(self.filtrar_facturas)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todas", "Pendientes", "Pagadas"])
        self.filter_combo.currentTextChanged.connect(self.filtrar_facturas)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.filter_combo)
        layout.addLayout(search_layout)

        # Tabla de facturas
        self.tabla_facturas = QTableWidget()
        self.tabla_facturas.setColumnCount(6)
        self.tabla_facturas.setHorizontalHeaderLabels(["ID", "Trabajo", "Fecha", "Monto", "Estado", "Cliente"])
        self.tabla_facturas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_facturas.itemDoubleClicked.connect(self.editar_factura)
        layout.addWidget(self.tabla_facturas)

        # Botones de acción
        action_layout = QHBoxLayout()
        editar_btn = QPushButton("Editar Factura")
        editar_btn.setIcon(QIcon('icons/edit_invoice.png'))
        editar_btn.clicked.connect(self.editar_factura_seleccionada)
        eliminar_btn = QPushButton("Eliminar Factura")
        eliminar_btn.setIcon(QIcon('icons/delete_invoice.png'))
        eliminar_btn.clicked.connect(self.eliminar_factura)
        enviar_whatsapp_btn = QPushButton("Enviar por WhatsApp")
        enviar_whatsapp_btn.setIcon(QIcon('icons/whatsapp.png'))
        enviar_whatsapp_btn.clicked.connect(self.enviar_recibo_whatsapp)
        generar_qr_btn = QPushButton("Generar QR")
        generar_qr_btn.setIcon(QIcon('icons/qr.png'))
        generar_qr_btn.clicked.connect(self.generar_qr)
        action_layout.addWidget(editar_btn)
        action_layout.addWidget(eliminar_btn)
        action_layout.addWidget(enviar_whatsapp_btn)
        action_layout.addWidget(generar_qr_btn)
        layout.addLayout(action_layout)

        self.setLayout(layout)
        self.cargar_trabajos()
        self.cargar_facturas()

    def cargar_trabajos(self):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, c.nombre || ' - ' || t.descripcion
            FROM trabajos t 
            JOIN reservas r ON t.reserva_id = r.id
            JOIN clientes c ON r.cliente_id = c.id
            WHERE t.estado = 'Completado'
        """)
        trabajos = cursor.fetchall()
        conn.close()

        self.trabajo_combo.clear()
        for trabajo in trabajos:
            self.trabajo_combo.addItem(trabajo[1], trabajo[0])

    def agregar_factura(self):
        trabajo_id = self.trabajo_combo.currentData()
        fecha = self.fecha_input.date().toString(Qt.ISODate)
        monto = self.monto_input.value()
        estado = self.estado_combo.currentText()

        if not trabajo_id or monto <= 0:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios y el monto debe ser mayor que cero")
            return

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO facturas (trabajo_id, fecha, monto, estado)
            VALUES (?, ?, ?, ?)
        """, (trabajo_id, fecha, monto, estado))
        conn.commit()
        conn.close()

        self.monto_input.setValue(0)
        self.cargar_facturas()
        self.actualizar_facturas.emit()

    def cargar_facturas(self):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.id, t.descripcion, f.fecha, f.monto, f.estado, c.nombre
            FROM facturas f
            JOIN trabajos t ON f.trabajo_id = t.id
            JOIN reservas r ON t.reserva_id = r.id
            JOIN clientes c ON r.cliente_id = c.id
            ORDER BY f.fecha DESC
        """)
        facturas = cursor.fetchall()
        conn.close()

        self.tabla_facturas.setRowCount(len(facturas))
        for row, factura in enumerate(facturas):
            for col, valor in enumerate(factura):
                item = QTableWidgetItem(str(valor))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if col == 3:  # Columna de monto
                    item.setText(f"${valor:.2f}")
                elif col == 4:  # Columna de estado
                    if valor == "Pendiente":
                        item.setBackground(QColor(255, 255, 200))  # Amarillo claro
                    elif valor == "Pagada":
                        item.setBackground(QColor(200, 255, 200))  # Verde claro
                self.tabla_facturas.setItem(row, col, item)

        self.tabla_facturas.resizeColumnsToContents()

    def filtrar_facturas(self):
        busqueda = self.search_input.text().lower()
        filtro = self.filter_combo.currentText()

        for row in range(self.tabla_facturas.rowCount()):
            trabajo = self.tabla_facturas.item(row, 1).text().lower()
            cliente = self.tabla_facturas.item(row, 5).text().lower()
            estado = self.tabla_facturas.item(row, 4).text()
            
            mostrar = busqueda in trabajo or busqueda in cliente
            if filtro != "Todas" and estado != filtro:
                mostrar = False

            self.tabla_facturas.setRowHidden(row, not mostrar)

    def editar_factura_seleccionada(self):
        current_row = self.tabla_facturas.currentRow()
        if current_row >= 0:
            self.editar_factura(self.tabla_facturas.item(current_row, 0))

    def editar_factura(self, item):
        factura_id = int(self.tabla_facturas.item(item.row(), 0).text())
        dialog = EditarFacturaDialog(factura_id, self)
        if dialog.exec_():
            self.cargar_facturas()
            self.actualizar_facturas.emit()

    def eliminar_factura(self):
        current_row = self.tabla_facturas.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Por favor, seleccione una factura para eliminar")
            return

        factura_id = int(self.tabla_facturas.item(current_row, 0).text())
        trabajo = self.tabla_facturas.item(current_row, 1).text()

        reply = QMessageBox.question(self, "Confirmar eliminación",
                                     f"¿Está seguro de que desea eliminar la factura del trabajo '{trabajo}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM facturas WHERE id = ?", (factura_id,))
            conn.commit()
            conn.close()
            self.cargar_facturas()
            self.actualizar_facturas.emit()
            QMessageBox.information(self, "Éxito", f"Factura del trabajo '{trabajo}' eliminada correctamente")

    def enviar_recibo_whatsapp(self):
        current_row = self.tabla_facturas.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Por favor, seleccione una factura para enviar por WhatsApp")
            return

        factura_id = self.tabla_facturas.item(current_row, 0).text()
        trabajo = self.tabla_facturas.item(current_row, 1).text()
        monto = self.tabla_facturas.item(current_row, 3).text()
        cliente = self.tabla_facturas.item(current_row, 5).text()
        
        numero, ok = QInputDialog.getText(self, "Número de WhatsApp", "Ingrese el número de WhatsApp (con código de país):")
        if ok and numero:
            mensaje = f"Estimado/a {cliente},\n\nRecibo de trabajo: {trabajo}\nMonto: {monto}\nFactura ID: {factura_id}\n\nGracias por su preferencia!"
            try:
                pywhatkit.sendwhatmsg_instantly(numero, mensaje, wait_time=10)
                QMessageBox.information(self, "Éxito", "Recibo enviado por WhatsApp")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo enviar el recibo: {str(e)}")

    def generar_qr(self):
        current_row = self.tabla_facturas.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Por favor, seleccione una factura para generar el código QR")
            return

        factura_id = self.tabla_facturas.item(current_row, 0).text()
        trabajo = self.tabla_facturas.item(current_row, 1).text()
        monto = self.tabla_facturas.item(current_row, 3).text()
        cliente = self.tabla_facturas.item(current_row, 5).text()
        
        data = f"Factura ID: {factura_id}\nCliente: {cliente}\nTrabajo: {trabajo}\nMonto: {monto}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        file_name, _ = QFileDialog.getSaveFileName(self, "Guardar código QR", "", "PNG Files (*.png)")
        if file_name:
            img.save(file_name)
            QMessageBox.information(self, "Éxito", f"Código QR guardado en {file_name}")

class EditarFacturaDialog(QDialog):
    def __init__(self, factura_id, parent=None):
        super().__init__(parent)
        self.factura_id = factura_id
        self.setWindowTitle("Editar Factura")
        self.layout = QFormLayout(self)

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT trabajo_id, fecha, monto, estado FROM facturas WHERE id = ?", (factura_id,))
        factura = cursor.fetchone()
        cursor.execute("""
            SELECT t.id, c.nombre || ' - ' || t.descripcion
            FROM trabajos t 
            JOIN reservas r ON t.reserva_id = r.id
            JOIN clientes c ON r.cliente_id = c.id
            WHERE t.estado = 'Completado'
        """)
        trabajos = cursor.fetchall()
        conn.close()

        self.trabajo_combo = QComboBox()
        for trabajo in trabajos:
            self.trabajo_combo.addItem(trabajo[1], trabajo[0])
        self.trabajo_combo.setCurrentIndex(self.trabajo_combo.findData(factura[0]))

        self.fecha_input = QDateEdit()
        self.fecha_input.setDate(QDate.fromString(factura[1], Qt.ISODate))
        self.monto_input = QDoubleSpinBox()
        self.monto_input.setRange(0, 1000000)
        self.monto_input.setPrefix("$")
        self.monto_input.setDecimals(2)
        self.monto_input.setValue(factura[2])
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["Pendiente", "Pagada"])
        self.estado_combo.setCurrentText(factura[3])

        self.layout.addRow("Trabajo:", self.trabajo_combo)
        self.layout.addRow("Fecha:", self.fecha_input)
        self.layout.addRow("Monto:", self.monto_input)
        self.layout.addRow("Estado:", self.estado_combo)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def accept(self):
        trabajo_id = self.trabajo_combo.currentData()
        fecha = self.fecha_input.date().toString(Qt.ISODate)
        monto = self.monto_input.value()
        estado = self.estado_combo.currentText()

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE facturas 
            SET trabajo_id = ?, fecha = ?, monto = ?, estado = ? 
            WHERE id = ?
        """, (trabajo_id, fecha, monto, estado, self.factura_id))
        conn.commit()
        conn.close()

        super().accept()

