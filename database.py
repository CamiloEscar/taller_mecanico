import sqlite3

DATABASE_NAME = 'taller_mecanico.db'


def create_connection():
    return sqlite3.connect(DATABASE_NAME)


def create_tables():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY,
        nombre TEXT NOT NULL,
        telefono TEXT,
        email TEXT,
        direccion TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        fecha TEXT NOT NULL,
        hora TEXT NOT NULL,
        descripcion TEXT,
        estado TEXT NOT NULL DEFAULT 'Pendiente',
        FOREIGN KEY (cliente_id) REFERENCES clientes (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trabajos (
        id INTEGER PRIMARY KEY,
        reserva_id INTEGER,
        descripcion TEXT NOT NULL,
        estado TEXT NOT NULL,
        fecha_inicio TEXT,
        fecha_fin TEXT,
        FOREIGN KEY (reserva_id) REFERENCES reservas (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS facturas (
        id INTEGER PRIMARY KEY,
        trabajo_id INTEGER,
        fecha TEXT NOT NULL,
        monto REAL NOT NULL,
        estado TEXT NOT NULL,
        FOREIGN KEY (trabajo_id) REFERENCES trabajos (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        cantidad INTEGER NOT NULL,
        precio REAL NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recordatorios (
        id INTEGER PRIMARY KEY,
        cliente TEXT NOT NULL,
        fecha TEXT NOT NULL,
        descripcion TEXT NOT NULL
    )
    ''')

    cursor.execute('''
CREATE TABLE IF NOT EXISTS proveedores (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    telefono TEXT,
    email TEXT,
    direccion TEXT
)
''')

    cursor.execute('''
CREATE TABLE IF NOT EXISTS vehiculos (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL,
    matricula TEXT NOT NULL,
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    anio INTEGER NOT NULL,
    kilometraje INTEGER,
    FOREIGN KEY (cliente_id) REFERENCES clientes (id)
)
''')

    conn.commit()
    conn.close()
