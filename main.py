import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QStyleFactory
from PyQt5.QtGui import QIcon, QPalette, QColor
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from clientes import ClientesTab
from reservas import ReservasTab
from trabajos import TrabajosTab
from facturas import FacturasTab
from reportes import ReportesTab
from inventario import InventarioTab
from database import create_tables
from recordatorios import RecordatoriosTab

class Comunicador(QObject):
    actualizar_datos = pyqtSignal()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Taller Mecánico")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon('icon.png'))

        self.comunicador = Comunicador()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        self.tabs.setMovable(True)
        layout.addWidget(self.tabs)

        self.clientes_tab = ClientesTab(self.comunicador)
        self.reservas_tab = ReservasTab(self.comunicador)
        self.trabajos_tab = TrabajosTab(self.comunicador)
        self.facturas_tab = FacturasTab(self.comunicador)
        self.reportes_tab = ReportesTab(self.comunicador)
        self.inventario_tab = InventarioTab(self.comunicador)
        self.recordatorios_tab = RecordatoriosTab(self.comunicador)

        self.tabs.addTab(self.clientes_tab, QIcon('icons/clientes.png'), "Clientes")
        self.tabs.addTab(self.reservas_tab, QIcon('icons/reservas.png'), "Reservas")
        self.tabs.addTab(self.trabajos_tab, QIcon('icons/trabajos.png'), "Trabajos")
        self.tabs.addTab(self.facturas_tab, QIcon('icons/facturas.png'), "Facturas")
        self.tabs.addTab(self.reportes_tab, QIcon('icons/reportes.png'), "Reportes")
        self.tabs.addTab(self.inventario_tab, QIcon('icons/inventario.png'), "Inventario")
        self.tabs.addTab(self.recordatorios_tab, QIcon('icons/recordatorio.png'), "Recordatorios")

        self.tabs.currentChanged.connect(self.actualizar_pestana_actual)

    def actualizar_pestana_actual(self, index):
        self.comunicador.actualizar_datos.emit()

def set_dark_theme(app):
    app.setStyle(QStyleFactory.create("Fusion"))
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    set_dark_theme(app)
    create_tables()
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

