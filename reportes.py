from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QComboBox, QDateEdit,
                             QLabel, QHeaderView)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon
from database import create_connection

class ReportesTab(QWidget):
    def __init__(self, comunicador):
        super().__init__()
        self.comunicador = comunicador
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Controles para generar reportes
        controls_layout = QHBoxLayout()
        self.tipo_reporte_combo = QComboBox()
        self.tipo_reporte_combo.addItems(["Ingresos por período", "Trabajos por estado", "Clientes frecuentes"])
        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setDate(QDate.currentDate().addDays(-30))
        self.fecha_fin = QDateEdit()
        self.fecha_fin.setDate(QDate.currentDate())
        generar_btn = QPushButton("Generar Reporte")
        generar_btn.setIcon(QIcon('icons/report.png'))
        generar_btn.clicked.connect(self.generar_reporte)

        controls_layout.addWidget(QLabel("Tipo de Reporte:"))
        controls_layout.addWidget(self.tipo_reporte_combo)
        controls_layout.addWidget(QLabel("Fecha Inicio:"))
        controls_layout.addWidget(self.fecha_inicio)
        controls_layout.addWidget(QLabel("Fecha Fin:"))
        controls_layout.addWidget(self.fecha_fin)
        controls_layout.addWidget(generar_btn)

        layout.addLayout(controls_layout)

        # Tabla de resultados
        self.tabla_resultados = QTableWidget()
        self.tabla_resultados.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla_resultados)

        self.setLayout(layout)

    def generar_reporte(self):
        tipo_reporte = self.tipo_reporte_combo.currentText()
        fecha_inicio = self.fecha_inicio.date().toString(Qt.ISODate)
        fecha_fin = self.fecha_fin.date().toString(Qt.ISODate)

        if tipo_reporte == "Ingresos por período":
            self.reporte_ingresos(fecha_inicio, fecha_fin)
        elif tipo_reporte == "Trabajos por estado":
            self.reporte_trabajos_estado(fecha_inicio, fecha_fin)
        elif tipo_reporte == "Clientes frecuentes":
            self.reporte_clientes_frecuentes(fecha_inicio, fecha_fin)

    def reporte_ingresos(self, fecha_inicio, fecha_fin):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DATE(f.fecha) as fecha, SUM(f.monto) as total
            FROM facturas f
            WHERE f.fecha BETWEEN ? AND ?
            GROUP BY DATE(f.fecha)
            ORDER BY fecha
        """, (fecha_inicio, fecha_fin))
        resultados = cursor.fetchall()
        conn.close()

        self.tabla_resultados.setColumnCount(2)
        self.tabla_resultados.setHorizontalHeaderLabels(["Fecha", "Total"])
        self.tabla_resultados.setRowCount(len(resultados))

        for row, resultado in enumerate(resultados):
            self.tabla_resultados.setItem(row, 0, QTableWidgetItem(str(resultado[0])))
            self.tabla_resultados.setItem(row, 1, QTableWidgetItem(f"${resultado[1]:.2f}"))

        self.tabla_resultados.resizeColumnsToContents()

    def reporte_trabajos_estado(self, fecha_inicio, fecha_fin):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.estado, COUNT(*) as cantidad
            FROM trabajos t
            WHERE t.fecha_inicio BETWEEN ? AND ?
            GROUP BY t.estado
        """, (fecha_inicio, fecha_fin))
        resultados = cursor.fetchall()
        conn.close()

        self.tabla_resultados.setColumnCount(2)
        self.tabla_resultados.setHorizontalHeaderLabels(["Estado", "Cantidad"])
        self.tabla_resultados.setRowCount(len(resultados))

        for row, resultado in enumerate(resultados):
            self.tabla_resultados.setItem(row, 0, QTableWidgetItem(str(resultado[0])))
            self.tabla_resultados.setItem(row, 1, QTableWidgetItem(str(resultado[1])))

        self.tabla_resultados.resizeColumnsToContents()

    def reporte_clientes_frecuentes(self, fecha_inicio, fecha_fin):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.nombre, COUNT(t.id) as cantidad_trabajos
            FROM clientes c
            JOIN reservas r ON c.id = r.cliente_id
            JOIN trabajos t ON r.id = t.reserva_id
            WHERE t.fecha_inicio BETWEEN ? AND ?
            GROUP BY c.id
            ORDER BY cantidad_trabajos DESC
            LIMIT 10
        """, (fecha_inicio, fecha_fin))
        resultados = cursor.fetchall()
        conn.close()

        self.tabla_resultados.setColumnCount(2)
        self.tabla_resultados.setHorizontalHeaderLabels(["Cliente", "Cantidad de Trabajos"])
        self.tabla_resultados.setRowCount(len(resultados))

        for row, resultado in enumerate(resultados):
            self.tabla_resultados.setItem(row, 0, QTableWidgetItem(str(resultado[0])))
            self.tabla_resultados.setItem(row, 1, QTableWidgetItem(str(resultado[1])))

        self.tabla_resultados.resizeColumnsToContents()

