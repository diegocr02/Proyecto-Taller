# Historia: H-08 (solo datos simulados, Ley N.° 29733)
"""
Copia data/taller.db (SQLite, la base que usa la app) a MySQL/MariaDB de XAMPP
para poder revisarla en phpMyAdmin.

Es solo una COPIA de lectura: la app sigue usando SQLite. Si se cambian datos
en phpMyAdmin, la app no los ve. Para actualizar la copia, se vuelve a correr:

    python data/exportar_a_xampp.py

Requisitos: XAMPP con MySQL encendido (panel de XAMPP -> MySQL -> Start).
Opcional en .env o en el entorno: XAMPP_MYSQL (ruta a mysql.exe),
XAMPP_USUARIO (por defecto root), XAMPP_CLAVE (por defecto vacia),
XAMPP_BD (por defecto jorge_motors_app).
"""

import os
import sqlite3
import subprocess
import sys

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_SQLITE = os.path.join(CARPETA, "taller.db")
MYSQL = os.getenv("XAMPP_MYSQL", r"C:\xampp\mysql\bin\mysql.exe")
USUARIO = os.getenv("XAMPP_USUARIO", "root")
CLAVE = os.getenv("XAMPP_CLAVE", "")
BD = os.getenv("XAMPP_BD", "jorge_motors_app")

# Mismas tablas y columnas que crea data/seed.py, con tipos de MySQL.
# El orden importa: primero las tablas a las que otras apuntan (claves foraneas).
TABLAS = {
    "clientes": """
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(150) NOT NULL,
        dni VARCHAR(8) NOT NULL UNIQUE""",
    "vehiculos": """
        id INT AUTO_INCREMENT PRIMARY KEY,
        placa VARCHAR(10) NOT NULL UNIQUE,
        marca VARCHAR(60) NOT NULL,
        modelo VARCHAR(60) NOT NULL,
        anio INT NOT NULL,
        id_cliente INT NOT NULL,
        FOREIGN KEY (id_cliente) REFERENCES clientes (id)""",
    "ordenes_trabajo": """
        id INT AUTO_INCREMENT PRIMARY KEY,
        id_vehiculo INT NOT NULL,
        id_cliente INT NOT NULL,
        kilometraje INT NOT NULL,
        motivo TEXT NOT NULL,
        tecnico VARCHAR(100) NOT NULL,
        estado VARCHAR(20) NOT NULL,
        observaciones TEXT,
        fecha_hora VARCHAR(30) NOT NULL,
        FOREIGN KEY (id_vehiculo) REFERENCES vehiculos (id),
        FOREIGN KEY (id_cliente) REFERENCES clientes (id)""",
    "repuestos": """
        id INT AUTO_INCREMENT PRIMARY KEY,
        codigo VARCHAR(20) NOT NULL UNIQUE,
        nombre VARCHAR(150) NOT NULL,
        unidad VARCHAR(30) NOT NULL,
        stock_minimo INT NOT NULL""",
    "stock": """
        id_repuesto INT PRIMARY KEY,
        cantidad INT NOT NULL,
        FOREIGN KEY (id_repuesto) REFERENCES repuestos (id)""",
    "trazabilidad_ia": """
        id VARCHAR(36) PRIMARY KEY,
        timestamp VARCHAR(40) NOT NULL,
        rol VARCHAR(30) NOT NULL,
        pregunta TEXT NOT NULL,
        contexto_mcp LONGTEXT NOT NULL,
        respuesta LONGTEXT,
        error TEXT""",
    "comparaciones_conteo": """
        id INT AUTO_INCREMENT PRIMARY KEY,
        fecha_hora VARCHAR(30) NOT NULL,
        codigo VARCHAR(20) NOT NULL,
        nombre VARCHAR(150) NOT NULL,
        sistema INT NOT NULL,
        conteo INT NOT NULL,
        diferencia INT NOT NULL,
        descuadre TINYINT NOT NULL""",
}


def valor_sql(valor):
    """Convierte un valor de Python en texto SQL seguro para MySQL."""
    if valor is None:
        return "NULL"
    if isinstance(valor, (int, float)):
        return str(valor)
    texto = str(valor).replace("\\", "\\\\").replace("'", "''")
    return f"'{texto}'"


def generar_sql(conexion):
    lineas = [
        f"DROP DATABASE IF EXISTS `{BD}`;",
        f"CREATE DATABASE `{BD}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
        f"USE `{BD}`;",
    ]
    conteos = {}
    for tabla, columnas in TABLAS.items():
        lineas.append(f"CREATE TABLE `{tabla}` ({columnas}\n) ENGINE=InnoDB;")
        cursor = conexion.execute(f"SELECT * FROM {tabla}")
        nombres = ", ".join(f"`{c[0]}`" for c in cursor.description)
        filas = cursor.fetchall()
        conteos[tabla] = len(filas)
        for fila in filas:
            valores = ", ".join(valor_sql(v) for v in fila)
            lineas.append(f"INSERT INTO `{tabla}` ({nombres}) VALUES ({valores});")
    return "\n".join(lineas) + "\n", conteos


def main():
    if not os.path.exists(RUTA_SQLITE):
        sys.exit(f"No existe {RUTA_SQLITE}. Primero corra: python data/seed.py")
    if not os.path.exists(MYSQL):
        sys.exit(f"No se encontro mysql.exe en {MYSQL}. Indique la ruta en XAMPP_MYSQL.")

    # Solo lectura: esta copia nunca modifica la base de la app
    conexion = sqlite3.connect(f"file:{RUTA_SQLITE}?mode=ro", uri=True)
    try:
        sql, conteos = generar_sql(conexion)
    finally:
        conexion.close()

    comando = [MYSQL, "-u", USUARIO, "--default-character-set=utf8mb4"]
    if CLAVE:
        comando.append(f"-p{CLAVE}")
    resultado = subprocess.run(comando, input=sql.encode("utf-8"), capture_output=True)
    if resultado.returncode != 0:
        error = resultado.stderr.decode("utf-8", "replace").strip()
        sys.exit(f"MySQL dio un error (¿esta encendido en el panel de XAMPP?):\n{error}")

    print(f"Copia lista en la base '{BD}' de XAMPP:")
    for tabla, total in conteos.items():
        print(f"  {tabla:<22} {total} filas")
    print("Revisela en http://localhost/phpmyadmin")


if __name__ == "__main__":
    main()
