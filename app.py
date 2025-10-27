from flask import Flask, render_template, request, redirect, send_file
import sqlite3
import csv
import io
import matplotlib.pyplot as plt
import base64

app = Flask(__name__)
STOCK_BAJO = 5

DB_PATH = "inventario.db"

# ---------------- Funciones ----------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_productos(filtro="", categoria=""):
    conn = get_db_connection()
    query = "SELECT * FROM productos WHERE 1=1"
    params = []
    if filtro:
        query += " AND nombre_producto LIKE ?"
        params.append(f"%{filtro}%")
    if categoria and categoria != "Todas":
        query += " AND categoria=?"
        params.append(categoria)
    productos = conn.execute(query, params).fetchall()
    conn.close()
    return productos

def get_categorias():
    conn = get_db_connection()
    categorias = [row[0] for row in conn.execute("SELECT DISTINCT categoria FROM productos").fetchall()]
    conn.close()
    return ["Todas"] + categorias

def agregar_producto_db(nombre, cantidad, precio, categoria):
    conn = get_db_connection()
    conn.execute("INSERT INTO productos (nombre_producto, cantidad, precio, categoria) VALUES (?, ?, ?, ?)",
                 (nombre, cantidad, precio, categoria))
    conn.commit()
    conn.close()

def editar_producto_db(id_prod, nombre, cantidad, precio, categoria):
    conn = get_db_connection()
    conn.execute("UPDATE productos SET nombre_producto=?, cantidad=?, precio=?, categoria=? WHERE id=?",
                 (nombre, cantidad, precio, categoria, id_prod))
    conn.commit()
    conn.close()

def eliminar_producto_db(id_prod):
    conn = get_db_connection()
    conn.execute("DELETE FROM productos WHERE id=?", (id_prod,))
    conn.commit()
    conn.close()

def generar_grafica():
    conn = get_db_connection()
    rows = conn.execute("SELECT categoria, SUM(cantidad) FROM productos GROUP BY categoria").fetchall()
    categorias = [r[0] for r in rows]
    cantidades = [r[1] for r in rows]

    rows_valor = conn.execute("SELECT categoria, SUM(cantidad*precio) FROM productos GROUP BY categoria").fetchall()
    categorias_valor = [r[0] for r in rows_valor]
    valores = [r[1] for r in rows_valor]
    conn.close()

    fig, ax = plt.subplots(1,2, figsize=(10,4))
    ax[0].bar(categorias, cantidades, color="#4CAF50")
    ax[0].set_title("Cantidad por Categoría")
    ax[0].set_ylabel("Cantidad")
    ax[0].set_xlabel("Categoría")
    ax[1].bar(categorias_valor, valores, color="#2196F3")
    ax[1].set_title("Valor por Categoría")
    ax[1].set_ylabel("Valor ($)")
    ax[1].set_xlabel("Categoría")
    for a in ax:
        for tick in a.get_xticklabels():
            tick.set_rotation(45)
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{graph_url}"

def dashboard_stats():
    conn = get_db_connection()
    total_prod = conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
    total_valor = conn.execute("SELECT SUM(cantidad*precio) FROM productos").fetchone()[0] or 0
    bajo_stock = conn.execute("SELECT COUNT(*) FROM productos WHERE cantidad < ?", (STOCK_BAJO,)).fetchone()[0]
    conn.close()
    return total_prod, total_valor, bajo_stock

# ---------------- Rutas ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    filtro = request.args.get("filtro", "")
    categoria = request.args.get("categoria", "Todas")
    productos = get_productos(filtro, categoria)
    categorias = get_categorias()
    total_prod, total_valor, bajo_stock = dashboard_stats()
    grafica_url = generar_grafica()
    return render_template("index.html",
                           productos=productos,
                           categorias=categorias,
                           filtro=filtro,
                           categoria=categoria,
                           total_prod=total_prod,
                           total_valor=total_valor,
                           bajo_stock=bajo_stock,
                           grafica_url=grafica_url)

@app.route("/agregar", methods=["POST"])
def agregar():
    nombre = request.form["nombre"]
    cantidad = int(request.form["cantidad"])
    precio = float(request.form["precio"])
    categoria = request.form["categoria"]
    agregar_producto_db(nombre, cantidad, precio, categoria)
    return redirect("/")

@app.route("/editar/<int:id_prod>", methods=["POST"])
def editar(id_prod):
    nombre = request.form["nombre"]
    cantidad = int(request.form["cantidad"])
    precio = float(request.form["precio"])
    categoria = request.form["categoria"]
    editar_producto_db(id_prod, nombre, cantidad, precio, categoria)
    return redirect("/")

@app.route("/eliminar/<int:id_prod>", methods=["POST"])
def eliminar(id_prod):
    eliminar_producto_db(id_prod)
    return redirect("/")

@app.route("/exportar")
def exportar():
    productos = get_productos()
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(["ID","Nombre","Cantidad","Precio","Categoría"])
    for p in productos:
        writer.writerow([p["id"], p["nombre_producto"], p["cantidad"], p["precio"], p["categoria"]])
    output = io.BytesIO()
    output.write(si.getvalue().encode("utf-8"))
    output.seek(0)
    return send_file(output, mimetype="text/csv", as_attachment=True, download_name="inventario.csv")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
