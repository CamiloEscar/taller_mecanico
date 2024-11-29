import sqlite3
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, 
                             QSpinBox, QDoubleSpinBox, QLabel, QHeaderView, QComboBox,
                             QDialog, QDialogButtonBox, QFormLayout)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QColor
from database import create_connection

class InventarioTab(QWidget):
    def __init__(self, comunicador):
        super().__init__()
        self.comunicador = comunicador
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Formulario para agregar/editar items de inventario
        form_layout = QHBoxLayout()
        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Nombre del item")
        self.cantidad_input = QSpinBox()
        self.cantidad_input.setRange(0, 1000)
        self.precio_input = QDoubleSpinBox()
        self.precio_input.setRange(0, 10000)
        self.precio_input.setPrefix("$")
        self.precio_input.setDecimals(2)
        agregar_btn = QPushButton("Agregar/Actualizar Item")
        agregar_btn.setIcon(QIcon('icons/add.png'))
        agregar_btn.clicked.connect(self.agregar_actualizar_item)

        form_layout.addWidget(QLabel("Nombre:"))
        form_layout.addWidget(self.nombre_input)
        form_layout.addWidget(QLabel("Cantidad:"))
        form_layout.addWidget(self.cantidad_input)
        form_layout.addWidget(QLabel("Precio:"))
        form_layout.addWidget(self.precio_input)
        form_layout.addWidget(agregar_btn)

        layout.addLayout(form_layout)

        # Búsqueda y filtrado
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar item...")
        self.search_input.textChanged.connect(self.filtrar_inventario)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos", "Bajo stock", "Alto valor"])
        self.filter_combo.currentTextChanged.connect(self.filtrar_inventario)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.filter_combo)
        layout.addLayout(search_layout)

        # Tabla de inventario
        self.tabla_inventario = QTableWidget()
        self.tabla_inventario.setColumnCount(5)
        self.tabla_inventario.setHorizontalHeaderLabels(["ID", "Nombre", "Cantidad", "Precio", "Valor Total"])
        self.tabla_inventario.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_inventario.itemClicked.connect(self.cargar_item)
        layout.addWidget(self.tabla_inventario)

        # Botones de acción
        action_layout = QHBoxLayout()
        eliminar_btn = QPushButton("Eliminar Item")
        eliminar_btn.setIcon(QIcon('icons/delete.png'))
        eliminar_btn.clicked.connect(self.eliminar_item)
        exportar_btn = QPushButton("Exportar Inventario")
        exportar_btn.setIcon(QIcon('icons/export.png'))
        exportar_btn.clicked.connect(self.exportar_inventario)
        action_layout.addWidget(eliminar_btn)
        action_layout.addWidget(exportar_btn)
        layout.addLayout(action_layout)

        self.setLayout(layout)
        self.cargar_inventario()

        # Timer para actualizar el inventario periódicamente
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.cargar_inventario)
        self.timer.start(60000)  # Actualizar cada minuto

    def agregar_actualizar_item(self):
        nombre = self.nombre_input.text()
        cantidad = self.cantidad_input.value()
        precio = self.precio_input.value()

        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre del item es obligatorio")
            return

        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO inventario (nombre, cantidad, precio)
                VALUES (?, ?, ?)
                ON CONFLICT(nombre) DO UPDATE SET
                cantidad = cantidad + ?,
                precio = ?
            """, (nombre, cantidad, precio, cantidad, precio))
            conn.commit()
            QMessageBox.information(self, "Éxito", "Item agregado o actualizado correctamente")
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Error", f"No se pudo agregar o actualizar el item: {str(e)}")
        finally:
            conn.close()

        self.nombre_input.clear()
        self.cantidad_input.setValue(0)
        self.precio_input.setValue(0)
        self.cargar_inventario()

    def cargar_inventario(self):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, cantidad, precio, (cantidad * precio) as valor_total FROM inventario")
        items = cursor.fetchall()
        conn.close()

        self.tabla_inventario.setRowCount(len(items))
        for row, item in enumerate(items):
            for col, valor in enumerate(item):
                if col in [3, 4]:  # Columnas de precio y valor total
                    valor = f"${valor:.2f}"
                item_widget = QTableWidgetItem(str(valor))
                item_widget.setFlags(item_widget.flags() & ~Qt.ItemIsEditable)  # Hacer la celda de solo lectura
                if col == 2 and int(item[2]) < 10:  # Resaltar items con bajo stock
                    item_widget.setBackground(QColor(255, 200, 200))
                self.tabla_inventario.setItem(row, col, item_widget)

        self.tabla_inventario.resizeColumnsToContents()

    def cargar_item(self, item):
        row = item.row()
        self.nombre_input.setText(self.tabla_inventario.item(row, 1).text())
        self.cantidad_input.setValue(int(self.tabla_inventario.item(row, 2).text()))
        self.precio_input.setValue(float(self.tabla_inventario.item(row, 3).text().replace('$', '')))

    def filtrar_inventario(self):
        busqueda = self.search_input.text().lower()
        filtro = self.filter_combo.currentText()

        for row in range(self.tabla_inventario.rowCount()):
            item_nombre = self.tabla_inventario.item(row, 1).text().lower()
            item_cantidad = int(self.tabla_inventario.item(row, 2).text())
            item_precio = float(self.tabla_inventario.item(row, 3).text().replace('$', ''))
            
            mostrar = busqueda in item_nombre
            if filtro == "Bajo stock" and item_cantidad >= 10:
                mostrar = False
            elif filtro == "Alto valor" and item_precio < 100:
                mostrar = False

            self.tabla_inventario.setRowHidden(row, not mostrar)

    def eliminar_item(self):
        current_row = self.tabla_inventario.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Por favor, seleccione un item para eliminar")
            return

        item_id = self.tabla_inventario.item(current_row, 0).text()
        item_nombre = self.tabla_inventario.item(current_row, 1).text()

        reply = QMessageBox.question(self, "Confirmar eliminación",
                                     f"¿Está seguro de que desea eliminar el item '{item_nombre}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM inventario WHERE id = ?", (item_id,))
            conn.commit()
            conn.close()
            self.cargar_inventario()
            QMessageBox.information(self, "Éxito", f"Item '{item_nombre}' eliminado correctamente")

    def exportar_inventario(self):
        import csv
        from PyQt5.QtWidgets import QFileDialog

        filename, _ = QFileDialog.getSaveFileName(self, "Guardar inventario", "", "CSV Files (*.csv)")
        if filename:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, cantidad, precio, (cantidad * precio) as valor_total FROM inventario")
            items = cursor.fetchall()
            conn.close()

            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["ID", "Nombre", "Cantidad", "Precio", "Valor Total"])
                writer.writerows(items)

            QMessageBox.information(self, "Éxito", f"Inventario exportado correctamente a {filename}")

class AjusteInventarioDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajuste de Inventario")
        self.layout = QFormLayout(self)

        self.cantidad_input = QSpinBox()
        self.cantidad_input.setRange(-1000, 1000)
        self.layout.addRow("Ajuste de cantidad:", self.cantidad_input)

        self.razon_input = QLineEdit()
        self.layout.addRow("Razón del ajuste:", self.razon_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def get_values(self):
        return self.cantidad_input.value(), self.razon_input.text()

