import sqlite3
import random

# Conexión a la base de datos
conn = sqlite3.connect("inventario.db")
cursor = conn.cursor()

# Crear tabla si no existe
cursor.execute("""
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_producto TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    precio REAL NOT NULL,
    categoria TEXT
)
""")
conn.commit()

# Ejemplos de categorías y nombres
categorias = ["Electrónica", "Ropa", "Alimentos", "Hogar", "Deportes", "Juguetes"]
productos_base = [
    "Producto A", "Producto B", "Producto C", "Producto D", "Producto E",
    "Producto F", "Producto G", "Producto H", "Producto I", "Producto J"
]

# Limpiar tabla antes de insertar (opcional)
cursor.execute("DELETE FROM productos")
conn.commit()

# Insertar 50 productos de ejemplo
for i in range(50):
    nombre = random.choice(productos_base) + f" {i+1}"
    cantidad = random.randint(0, 20)
    precio = round(random.uniform(10, 500), 2)
    categoria = random.choice(categorias)
    cursor.execute(
        "INSERT INTO productos (nombre_producto, cantidad, precio, categoria) VALUES (?, ?, ?, ?)",
        (nombre, cantidad, precio, categoria)
    )

conn.commit()
conn.close()
print("Base de datos 'inventario.db' creada con 50 productos de ejemplo.")
