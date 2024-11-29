import csv
from PyQt5.QtWidgets import QFileDialog

def exportar_a_csv(tabla, nombre_archivo):
    opciones = QFileDialog.Options()
    archivo, _ = QFileDialog.getSaveFileName(None, "Guardar CSV", nombre_archivo, "CSV Files (*.csv)", options=opciones)
    if archivo:
        with open(archivo, 'w', newline='') as stream:
            writer = csv.writer(stream)
            header = []
            for column in range(tabla.columnCount()):
                header.append(tabla.horizontalHeaderItem(column).text())
            writer.writerow(header)
            for row in range(tabla.rowCount()):
                rowdata = []
                for column in range(tabla.columnCount()):
                    item = tabla.item(row, column)
                    if item is not None:
                        rowdata.append(item.text())
                    else:
                        rowdata.append('')
                writer.writerow(rowdata)