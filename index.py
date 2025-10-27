import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import csv
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# ---------------- Base de datos ----------------
conn = sqlite3.connect("inventario.db")
cursor = conn.cursor()
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

STOCK_BAJO = 5  # Stock mínimo para alerta

# ---------------- Funciones ----------------

def actualizar_tabla(filtro="", categoria_filtro=""):
    for row in tree.get_children():
        tree.delete(row)

    query = "SELECT * FROM productos WHERE 1=1"
    params = []

    if filtro:
        query += " AND nombre_producto LIKE ?"
        params.append(f"%{filtro}%")
    if categoria_filtro and categoria_filtro != "Todas":
        query += " AND categoria=?"
        params.append(categoria_filtro)

    cursor.execute(query, params)
    for producto in cursor.fetchall():
        tags = ()
        if producto[2] < STOCK_BAJO:
            tags = ("stock_bajo",)
        tree.insert("", tk.END, values=producto, tags=tags)

    actualizar_dashboard()

def agregar_producto():
    nombre = simpledialog.askstring("Producto", "Ingrese nombre del producto:")
    if not nombre:
        messagebox.showerror("Error", "El nombre es obligatorio")
        return
    cantidad = simpledialog.askinteger("Cantidad", "Ingrese cantidad disponible:", minvalue=0)
    if cantidad is None: return
    precio = simpledialog.askfloat("Precio", "Ingrese precio del producto:", minvalue=0.0)
    if precio is None: return
    categoria = simpledialog.askstring("Categoría", "Ingrese categoría del producto:")
    cursor.execute("INSERT INTO productos (nombre_producto, cantidad, precio, categoria) VALUES (?, ?, ?, ?)",
                   (nombre, cantidad, precio, categoria))
    conn.commit()
    actualizar_tabla()
    actualizar_categorias()

def editar_producto():
    try:
        selected = tree.selection()[0]
        id_editar = tree.item(selected)['values'][0]
    except IndexError:
        id_editar = simpledialog.askinteger("Editar", "Ingrese ID del producto:")

    cursor.execute("SELECT * FROM productos WHERE id=?", (id_editar,))
    producto = cursor.fetchone()
    if not producto:
        messagebox.showwarning("No encontrado", "Producto no existe")
        return

    nombre = simpledialog.askstring("Producto", "Nuevo nombre:", initialvalue=producto[1])
    if not nombre:
        messagebox.showerror("Error", "El nombre es obligatorio")
        return
    cantidad = simpledialog.askinteger("Cantidad", "Nueva cantidad:", initialvalue=producto[2], minvalue=0)
    if cantidad is None: return
    precio = simpledialog.askfloat("Precio", "Nuevo precio:", initialvalue=producto[3], minvalue=0.0)
    if precio is None: return
    categoria = simpledialog.askstring("Categoría", "Nueva categoría:", initialvalue=producto[4])

    cursor.execute("UPDATE productos SET nombre_producto=?, cantidad=?, precio=?, categoria=? WHERE id=?",
                   (nombre, cantidad, precio, categoria, id_editar))
    conn.commit()
    actualizar_tabla()
    actualizar_categorias()

def eliminar_producto():
    try:
        selected = tree.selection()[0]
        id_eliminar = tree.item(selected)['values'][0]
    except IndexError:
        id_eliminar = simpledialog.askinteger("Eliminar", "Ingrese ID del producto:")

    cursor.execute("SELECT * FROM productos WHERE id=?", (id_eliminar,))
    producto = cursor.fetchone()
    if not producto:
        messagebox.showwarning("No encontrado", "Producto no existe")
        return
    if messagebox.askyesno("Confirmar", f"¿Desea eliminar el producto {id_eliminar}?"):
        cursor.execute("DELETE FROM productos WHERE id=?", (id_eliminar,))
        conn.commit()
        actualizar_tabla()
        actualizar_categorias()

def exportar_csv():
    file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV files", "*.csv")],
                                             title="Guardar inventario como")
    if file_path:
        cursor.execute("SELECT * FROM productos")
        productos = cursor.fetchall()
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Nombre", "Cantidad", "Precio", "Categoría"])
            writer.writerows(productos)
        messagebox.showinfo("Éxito", f"Inventario exportado a {file_path}")

def buscar_producto(event):
    texto = entry_buscar.get()
    categoria = combo_categoria.get()
    actualizar_tabla(filtro=texto, categoria_filtro=categoria)

def actualizar_categorias():
    cursor.execute("SELECT DISTINCT categoria FROM productos")
    categorias = [row[0] for row in cursor.fetchall()]
    combo_categoria['values'] = ["Todas"] + categorias
    if combo_categoria.get() not in ["Todas"] + categorias:
        combo_categoria.set("Todas")
    actualizar_tabla(entry_buscar.get(), combo_categoria.get())

def mostrar_graficas():
    cursor.execute("SELECT categoria, SUM(cantidad) FROM productos GROUP BY categoria")
    rows = cursor.fetchall()
    categorias = [r[0] for r in rows]
    cantidades = [r[1] for r in rows]

    cursor.execute("SELECT categoria, SUM(cantidad*precio) FROM productos GROUP BY categoria")
    rows_valor = cursor.fetchall()
    categorias_valor = [r[0] for r in rows_valor]
    valores = [r[1] for r in rows_valor]

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

    canvas = FigureCanvasTkAgg(fig, master=frame_grafico)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    canvas.draw()

def actualizar_dashboard():
    cursor.execute("SELECT COUNT(*) FROM productos")
    total_prod = cursor.fetchone()[0]
    lbl_total.config(text=f"Total Productos: {total_prod}")

    cursor.execute("SELECT SUM(cantidad*precio) FROM productos")
    total_valor = cursor.fetchone()[0] or 0
    lbl_valor.config(text=f"Valor Total Inventario: ${total_valor:.2f}")

    cursor.execute("SELECT COUNT(*) FROM productos WHERE cantidad < ?", (STOCK_BAJO,))
    bajo_stock = cursor.fetchone()[0]
    lbl_stock.config(text=f"Productos Stock Bajo: {bajo_stock}")
    if bajo_stock > 0:
        messagebox.showwarning("Alerta Stock Bajo", f"Hay {bajo_stock} productos con stock bajo (<{STOCK_BAJO})")

# ---------------- Interfaz ----------------
root = tk.Tk()
root.title("Inventario Enterprise")
root.geometry("1100x700")
root.configure(bg="#f0f0f0")

# ---------- Estilos ----------
style = ttk.Style(root)
style.theme_use("clam")
style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"))
style.configure("Treeview", font=("Segoe UI", 10), rowheight=25)
style.map('Treeview', background=[('selected', '#347083')], foreground=[('selected', 'white')])
style.configure("TButton", font=("Segoe UI", 10, "bold"), foreground="white")

# ---------- Dashboard ----------
frame_dashboard = tk.Frame(root, bg="#f0f0f0")
frame_dashboard.pack(pady=10, fill=tk.X)

lbl_total = tk.Label(frame_dashboard, text="Total Productos: 0", font=("Segoe UI", 12, "bold"), bg="#f0f0f0")
lbl_total.pack(side=tk.LEFT, padx=20)
lbl_valor = tk.Label(frame_dashboard, text="Valor Total Inventario: $0.00", font=("Segoe UI", 12, "bold"), bg="#f0f0f0")
lbl_valor.pack(side=tk.LEFT, padx=20)
lbl_stock = tk.Label(frame_dashboard, text="Productos Stock Bajo: 0", font=("Segoe UI", 12, "bold"), bg="#f0f0f0", fg="red")
lbl_stock.pack(side=tk.LEFT, padx=20)

# ---------- Botones ----------
frame_btn = tk.Frame(root, bg="#f0f0f0")
frame_btn.pack(pady=5)
boton_config = {"width":18, "bg":"#4CAF50", "relief":"flat"}
tk.Button(frame_btn, text="Agregar Producto", command=agregar_producto, **boton_config).grid(row=0, column=0, padx=5)
tk.Button(frame_btn, text="Editar Producto", command=editar_producto, **boton_config).grid(row=0, column=1, padx=5)
tk.Button(frame_btn, text="Eliminar Producto", command=eliminar_producto, **boton_config).grid(row=0, column=2, padx=5)
tk.Button(frame_btn, text="Exportar CSV", command=exportar_csv, **boton_config).grid(row=0, column=3, padx=5)
tk.Button(frame_btn, text="Mostrar Gráficas", command=mostrar_graficas, **boton_config).grid(row=0, column=4, padx=5)

# ---------- Filtro y búsqueda ----------
frame_buscar = tk.Frame(root, bg="#f0f0f0")
frame_buscar.pack(pady=5)
tk.Label(frame_buscar, text="Buscar:", font=("Segoe UI", 10), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
entry_buscar = tk.Entry(frame_buscar, font=("Segoe UI", 10), width=30)
entry_buscar.pack(side=tk.LEFT, padx=5)
entry_buscar.bind("<KeyRelease>", buscar_producto)
tk.Label(frame_buscar, text="Categoría:", font=("Segoe UI", 10), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
combo_categoria = ttk.Combobox(frame_buscar, width=20)
combo_categoria.pack(side=tk.LEFT, padx=5)
combo_categoria.bind("<<ComboboxSelected>>", buscar_producto)

# ---------- Tabla ----------
tree = ttk.Treeview(root, columns=("ID", "Nombre", "Cantidad", "Precio", "Categoría"), show="headings")
tree.heading("ID", text="ID")
tree.heading("Nombre", text="Nombre")
tree.heading("Cantidad", text="Cantidad")
tree.heading("Precio", text="Precio")
tree.heading("Categoría", text="Categoría")
tree.pack(fill=tk.BOTH, expand=True, pady=10)
tree.tag_configure("stock_bajo", background="#FFCDD2")

def menu_click(event):
    try:
        tree.selection_set(tree.identify_row(event.y))
        menu.post(event.x_root, event.y_root)
    except: pass
menu = tk.Menu(root, tearoff=0)
menu.add_command(label="Editar", command=editar_producto)
menu.add_command(label="Eliminar", command=eliminar_producto)
tree.bind("<Button-3>", menu_click)

# ---------- Gráfico en ventana ----------
frame_grafico = tk.Frame(root, bg="#f0f0f0", height=300)
frame_grafico.pack(fill=tk.BOTH, expand=True)

# ---------- Inicialización ----------
actualizar_categorias()
actualizar_tabla()
root.mainloop()
conn.close()
