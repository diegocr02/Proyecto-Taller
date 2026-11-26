# Historia: H-08 (solo datos simulados, Ley N.° 29733)
"""
Script para inicializar y poblar la base de datos SQLite data/taller.db
con datos simulados de clientes, vehiculos, repuestos, stock y ordenes de trabajo.
Cumple con la Ley N.° 29733 (datos no reales).
"""

import os
import sqlite3
from datetime import datetime, timedelta

RUTA_BASE_DATOS_POR_DEFECTO = os.path.join(os.path.dirname(__file__), "taller.db")


def inicializar_base_datos(ruta_db: str = RUTA_BASE_DATOS_POR_DEFECTO) -> None:
    """Crea las tablas de la base de datos si no existen."""
    directorio = os.path.dirname(ruta_db)
    if directorio and not os.path.exists(directorio):
        os.makedirs(directorio, exist_ok=True)

    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()

    # Habilitar claves foraneas y modo WAL
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA journal_mode = WAL;")

    # Tabla clientes
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            dni TEXT NOT NULL UNIQUE
        );
        """
    )

    # Tabla vehiculos
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS vehiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT NOT NULL UNIQUE,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            anio INTEGER NOT NULL,
            id_cliente INTEGER NOT NULL,
            FOREIGN KEY (id_cliente) REFERENCES clientes (id)
        );
        """
    )

    # Tabla ordenes_trabajo
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ordenes_trabajo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_vehiculo INTEGER NOT NULL,
            id_cliente INTEGER NOT NULL,
            kilometraje INTEGER NOT NULL,
            motivo TEXT NOT NULL,
            tecnico TEXT NOT NULL,
            estado TEXT NOT NULL,
            observaciones TEXT,
            fecha_hora TEXT NOT NULL,
            FOREIGN KEY (id_vehiculo) REFERENCES vehiculos (id),
            FOREIGN KEY (id_cliente) REFERENCES clientes (id)
        );
        """
    )

    # Tabla repuestos
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS repuestos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            unidad TEXT NOT NULL,
            stock_minimo INTEGER NOT NULL
        );
        """
    )

    # Tabla stock
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stock (
            id_repuesto INTEGER PRIMARY KEY,
            cantidad INTEGER NOT NULL,
            FOREIGN KEY (id_repuesto) REFERENCES repuestos (id)
        );
        """
    )

    # Tabla trazabilidad_ia
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS trazabilidad_ia (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            rol TEXT NOT NULL,
            pregunta TEXT NOT NULL,
            contexto_mcp TEXT NOT NULL,
            respuesta TEXT,
            error TEXT
        );
        """
    )

    # Tabla comparaciones_conteo (resultados del conteo fisico, Requisito 5)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS comparaciones_conteo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT NOT NULL,
            codigo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            sistema INTEGER NOT NULL,
            conteo INTEGER NOT NULL,
            diferencia INTEGER NOT NULL,
            descuadre INTEGER NOT NULL
        );
        """
    )

    conexion.commit()
    conexion.close()


def poblar_datos_simulados(ruta_db: str = RUTA_BASE_DATOS_POR_DEFECTO) -> None:
    """Inserta registros ficticios de prueba si no existen."""
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Clientes simulados (Ley N.° 29733)
    clientes_simulados = [
        (1, "Cliente Simulado Uno", "10000001"),
        (2, "Cliente Simulado Dos", "10000002"),
        (3, "Cliente Simulado Tres", "10000003"),
    ]
    # Clientes adicionales para que el agente tenga datos suficientes (15-20 por tabla)
    clientes_simulados += [(i, f"Cliente Simulado {i:02d}", f"100000{i:02d}") for i in range(4, 21)]
    cursor.executemany(
        """
        INSERT OR IGNORE INTO clientes (id, nombre, dni)
        VALUES (?, ?, ?);
        """,
        clientes_simulados,
    )

    # Vehiculos simulados
    vehiculos_simulados = [
        (1, "ABC-123", "Toyota", "Corolla", 2018, 1),
        (2, "XYZ-789", "Nissan", "Sentra", 2020, 2),
        (3, "MNO-456", "Hyundai", "Elantra", 2019, 3),
        (4, "BCD-234", "Kia", "Rio", 2017, 4),
        (5, "CDE-345", "Toyota", "Hilux", 2021, 5),
        (6, "DEF-456", "Suzuki", "Swift", 2019, 6),
        (7, "EFG-567", "Chevrolet", "Sail", 2016, 7),
        (8, "FGH-678", "Mitsubishi", "L200", 2020, 8),
        (9, "GHI-789", "Hyundai", "Accent", 2018, 9),
        (10, "HIJ-890", "Nissan", "Versa", 2022, 10),
        (11, "IJK-901", "Mazda", "CX-5", 2019, 11),
        (12, "JKL-012", "Volkswagen", "Gol", 2015, 12),
        (13, "KLM-123", "Toyota", "Yaris", 2023, 13),
        (14, "LMN-234", "Kia", "Sportage", 2020, 14),
        (15, "NOP-345", "Honda", "Civic", 2017, 15),
        (16, "OPQ-456", "Ford", "Ranger", 2021, 16),
        (17, "PQR-567", "Suzuki", "Vitara", 2022, 17),
        (18, "QRS-678", "Toyota", "RAV4", 2018, 18),
        (19, "RST-789", "Chevrolet", "Onix", 2021, 19),
        (20, "STU-890", "Hyundai", "Tucson", 2020, 20),
    ]
    cursor.executemany(
        """
        INSERT OR IGNORE INTO vehiculos (id, placa, marca, modelo, anio, id_cliente)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        vehiculos_simulados,
    )

    # Repuestos simulados
    repuestos_simulados = [
        (1, "REP-001", "Pastillas de freno delanteras", "juego", 5),
        (2, "REP-002", "Filtro de aceite sintetico", "unidad", 10),
        (3, "REP-003", "Aceite de motor 5W-30", "litro", 20),
        (4, "REP-004", "Bujia de iridio", "unidad", 8),
        (5, "REP-005", "Amortiguador delantero", "unidad", 4),
        (6, "REP-006", "Pastillas de freno traseras", "juego", 4),
        (7, "REP-007", "Filtro de aire de motor", "unidad", 6),
        (8, "REP-008", "Filtro de cabina", "unidad", 5),
        (9, "REP-009", "Bateria 12V 65Ah", "unidad", 3),
        (10, "REP-010", "Liquido de frenos DOT 4", "litro", 6),
        (11, "REP-011", "Refrigerante de motor", "galon", 5),
        (12, "REP-012", "Correa de distribucion", "unidad", 3),
        (13, "REP-013", "Disco de freno delantero", "unidad", 4),
        (14, "REP-014", "Amortiguador trasero", "unidad", 4),
        (15, "REP-015", "Plumilla limpiaparabrisas", "par", 6),
        (16, "REP-016", "Foco halogeno H4", "unidad", 10),
        (17, "REP-017", "Kit de embrague", "juego", 2),
        (18, "REP-018", "Bomba de agua", "unidad", 2),
        (19, "REP-019", "Filtro de combustible", "unidad", 6),
        (20, "REP-020", "Aceite de transmision ATF", "litro", 8),
    ]
    cursor.executemany(
        """
        INSERT OR IGNORE INTO repuestos (id, codigo, nombre, unidad, stock_minimo)
        VALUES (?, ?, ?, ?, ?);
        """,
        repuestos_simulados,
    )

    # Stock simulado (algunos por debajo del stock minimo para probar alertas)
    stock_simulado = [
        (1, 3),   # Menor que stock_minimo (5) -> Alerta
        (2, 15),  # Normal
        (3, 8),   # Menor que stock_minimo (20) -> Alerta
        (4, 12),  # Normal
        (5, 4),   # Igual a stock_minimo (4) -> Alerta
        (6, 2),   # Alerta
        (7, 14),
        (8, 9),
        (9, 1),   # Alerta
        (10, 11),
        (11, 7),
        (12, 3),  # En el minimo -> Alerta
        (13, 8),
        (14, 6),
        (15, 18),
        (16, 25),
        (17, 0),  # Agotado -> Alerta
        (18, 5),
        (19, 4),  # Alerta
        (20, 16),
    ]
    cursor.executemany(
        """
        INSERT OR IGNORE INTO stock (id_repuesto, cantidad)
        VALUES (?, ?);
        """,
        stock_simulado,
    )

    # Ordenes de trabajo simuladas
    ahora_iso = datetime.now().astimezone().isoformat(timespec="seconds")
    hoy = datetime.now().astimezone().replace(hour=9, minute=0, second=0, microsecond=0)

    def hace(dias: int, hora: int = 9) -> str:
        return (hoy - timedelta(days=dias)).replace(hour=hora).isoformat(timespec="seconds")

    ordenes_simuladas = [
        (1, 1, 1, 45000, "Mantenimiento preventivo 45k", "Luis Pachas", "cerrada", "Cambio de aceite y filtros", ahora_iso),
        (2, 2, 2, 60000, "Ruido al frenar", "Luis Luna", "en proceso", "Revision de pastillas y discos", ahora_iso),
        (3, 3, 3, 32000, "Fallo en encendido", "Miguel Torres", "abierta", "Pendiente diagnostico electrico", ahora_iso),
        (4, 4, 4, 88000, "Cambio de pastillas delanteras", "Luis Luna", "cerrada", "Se cambiaron pastillas REP-001", hace(80)),
        (5, 5, 5, 25000, "Mantenimiento 25k", "Luis Pachas", "cerrada", "Aceite, filtro de aceite y filtro de aire", hace(72)),
        (6, 6, 6, 54000, "Luz de check engine encendida", "Miguel Torres", "cerrada", "Sensor de oxigeno reemplazado", hace(65)),
        (7, 7, 7, 120000, "Cambio de correa de distribucion", "Luis Pachas", "cerrada", "Correa y bomba de agua cambiadas", hace(58)),
        (8, 8, 8, 67000, "Vibracion al frenar", "Luis Luna", "cerrada", "Rectificado de discos delanteros", hace(51)),
        (9, 9, 9, 73000, "Bateria descargada", "Miguel Torres", "cerrada", "Bateria nueva instalada", hace(45)),
        (10, 10, 10, 15000, "Primer mantenimiento 15k", "Luis Pachas", "cerrada", "Cambio de aceite", hace(40)),
        (11, 11, 11, 61000, "Ruido en suspension delantera", "Luis Luna", "cerrada", "Amortiguadores delanteros cambiados", hace(35)),
        (12, 12, 12, 150000, "Embrague patina", "Miguel Torres", "cerrada", "Kit de embrague reemplazado", hace(30)),
        (13, 13, 13, 9000, "Revision general", "Luis Pachas", "cerrada", "Sin observaciones", hace(26)),
        (14, 1, 1, 52000, "Cambio de aceite y filtro", "Luis Pachas", "cerrada", "Aceite 5W-30 y filtro sintetico", hace(21)),
        (15, 14, 14, 47000, "Aire acondicionado no enfria", "Luis Luna", "en proceso", "Esperando carga de gas", hace(14)),
        (16, 15, 15, 99000, "Sobrecalentamiento del motor", "Miguel Torres", "en proceso", "Revisar bomba de agua y refrigerante", hace(10)),
        (17, 16, 16, 38000, "Cambio de pastillas traseras", "Luis Luna", "cerrada", "Pastillas traseras REP-006", hace(8)),
        (18, 17, 17, 12000, "Mantenimiento 10k", "Luis Pachas", "cerrada", "Aceite y filtro de aceite", hace(6)),
        (19, 18, 18, 84000, "Fuga de aceite", "Miguel Torres", "en proceso", "Cambio de empaque de carter", hace(4)),
        (20, 19, 19, 30000, "Plumillas y focos", "Luis Luna", "cerrada", "Plumillas y foco H4 cambiados", hace(3)),
        (21, 20, 20, 56000, "Ruido al girar el volante", "Luis Pachas", "abierta", "Pendiente revisar direccion", hace(2)),
        (22, 2, 2, 61000, "Revision de frenos", "Luis Luna", "abierta", "Cliente reporta pedal esponjoso", hace(1)),
        (23, 5, 5, 31000, "Alineamiento y balanceo", "Miguel Torres", "abierta", "Programado para hoy", hace(0, 8)),
    ]
    cursor.executemany(
        """
        INSERT OR IGNORE INTO ordenes_trabajo (
            id, id_vehiculo, id_cliente, kilometraje, motivo, tecnico, estado, observaciones, fecha_hora
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        ordenes_simuladas,
    )

    conexion.commit()
    conexion.close()


def ejecutar_semilla(ruta_db: str = RUTA_BASE_DATOS_POR_DEFECTO) -> None:
    """Inicializa la estructura y puebla los datos."""
    inicializar_base_datos(ruta_db)
    poblar_datos_simulados(ruta_db)
    print(f"Base de datos inicializada exitosamente en: {ruta_db}")


if __name__ == "__main__":
    ejecutar_semilla()
