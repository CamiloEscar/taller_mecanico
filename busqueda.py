from PyQt5.QtWidgets import QLineEdit, QVBoxLayout

def agregar_busqueda(layout, tabla):
    busqueda_input = QLineEdit()
    busqueda_input.setPlaceholderText("Buscar...")
    busqueda_input.textChanged.connect(lambda text: filtrar_tabla(text, tabla))
    layout.insertWidget(0, busqueda_input)

def filtrar_tabla(texto, tabla):
    for row in range(tabla.rowCount()):
        mostrar = False
        for col in range(tabla.columnCount()):
            item = tabla.item(row, col)
            if item and texto.lower() in item.text().lower():
                mostrar = True
                break
        tabla.setRowHidden(row, not mostrar)