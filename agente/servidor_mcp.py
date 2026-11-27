# Historia: H-09 (servidor MCP de JorgeBot: 7 herramientas de solo lectura)
import os
import sqlite3
import unicodedata
from datetime import date

from mcp.server.fastmcp import FastMCP

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_DB_POR_DEFECTO = os.path.join(CARPETA, "..", "data", "taller.db")

mcp = FastMCP("herramientas-jorge-motors")


def _sin_tildes(texto):
    """Quita tildes y pasa a minusculas para comparar 'Batería' con 'bateria'."""
    if texto is None:
        return ""
    return "".join(c for c in unicodedata.normalize("NFD", str(texto)) if unicodedata.category(c) != "Mn").lower()


def consultar(sql: str, parametros: tuple = ()) -> list[dict]:
    """Ejecuta una consulta SELECT en modo solo lectura y devuelve filas como diccionarios."""
    ruta = os.getenv("TALLER_DB", RUTA_DB_POR_DEFECTO)
    conexion = sqlite3.connect(f"file:{os.path.abspath(ruta)}?mode=ro", uri=True)
    try:
        conexion.row_factory = sqlite3.Row
        conexion.create_function("sin_tildes", 1, _sin_tildes)
        return [dict(fila) for fila in conexion.execute(sql, parametros).fetchall()]
    finally:
        conexion.close()


def _escapar_like(texto: str) -> str:
    """Escapa los comodines de LIKE (% y _) para que el texto del usuario se busque literal (ESCAPE '!')."""
    return texto.replace("!", "!!").replace("%", "!%").replace("_", "!_")


def _raiz(palabra: str) -> str:
    """'pastillas' -> 'pastilla', 'baterías' -> 'bateria': asi el plural tambien encuentra el repuesto."""
    palabra = _sin_tildes(palabra).strip()
    return palabra[:-1] if len(palabra) > 4 and palabra.endswith("s") else palabra


@mcp.tool()
def buscar_repuesto(texto: str) -> dict:
    """Busca repuestos por nombre o por codigo (ej. 'pastillas de freno', 'bujia', 'REP-004')
    y devuelve el stock actual, el stock minimo y si hay que reponerlo.
    Usar cuando el usuario pregunte si hay un repuesto, cuanto stock queda o si esta disponible."""
    palabras = [_raiz(p) for p in texto.replace(",", " ").split() if len(p) >= 3]
    palabras = [p for p in palabras if p not in {"de", "del", "para", "los", "las", "hay", "stock"}] or [_raiz(texto)]
    # Solo se repite la estructura con "?"; los textos del usuario van siempre como parametros
    condiciones = " AND ".join(["(sin_tildes(r.nombre) LIKE ? ESCAPE '!' OR lower(r.codigo) LIKE ? ESCAPE '!')"] * len(palabras))
    parametros = tuple(v for p in palabras for v in (f"%{_escapar_like(p)}%", f"%{_escapar_like(p)}%"))
    filas = consultar(
        f"""SELECT r.codigo, r.nombre, s.cantidad, r.unidad, r.stock_minimo
            FROM repuestos r JOIN stock s ON s.id_repuesto = r.id
            WHERE {condiciones} ORDER BY r.nombre LIMIT 10""",
        parametros,
    )
    for fila in filas:
        fila["requiere_reposicion"] = fila["cantidad"] <= fila["stock_minimo"]
    return {"busqueda": texto, "encontrados": len(filas), "repuestos": filas}


@mcp.tool()
def listar_inventario(solo_disponibles: bool = False) -> dict:
    """Lista TODOS los repuestos del inventario con su stock actual, unidad, stock minimo y estado
    (agotado, en el minimo, bajo el minimo o disponible). Con solo_disponibles=True omite los agotados.
    Usar cuando el usuario pregunte en general que hay en stock, que productos o repuestos tiene,
    que hay disponible, el inventario completo o un resumen del almacen, sin nombrar un repuesto concreto."""
    filas = consultar(
        """SELECT r.codigo, r.nombre, s.cantidad AS cantidad_actual, r.unidad, r.stock_minimo
           FROM repuestos r JOIN stock s ON s.id_repuesto = r.id
           WHERE s.cantidad > 0 OR ? = 0
           ORDER BY r.nombre LIMIT 50""",
        (1 if solo_disponibles else 0,),
    )
    for fila in filas:
        if fila["cantidad_actual"] == 0:
            fila["estado"] = "agotado"
        elif fila["cantidad_actual"] < fila["stock_minimo"]:
            fila["estado"] = "bajo el minimo"
        elif fila["cantidad_actual"] == fila["stock_minimo"]:
            fila["estado"] = "en el minimo"
        else:
            fila["estado"] = "disponible"
    return {
        "total_repuestos": len(filas),
        "indicacion": f"Son {len(filas)} repuestos; menciona los {len(filas)}.",
        "repuestos": filas,
    }


@mcp.tool()
def repuestos_por_reponer() -> dict:
    """Lista los repuestos cuyo stock actual es menor o igual a su stock minimo, del mas critico al menos critico.
    TODOS los repuestos de la lista requieren reposicion (tambien los que estan justo en el minimo).
    Usar cuando el usuario pregunte que comprar, que reponer, que esta por agotarse o que alertas de stock hay."""
    filas = consultar(
        """SELECT r.codigo, r.nombre, s.cantidad AS cantidad_actual, r.unidad, r.stock_minimo
           FROM repuestos r JOIN stock s ON s.id_repuesto = r.id
           WHERE s.cantidad <= r.stock_minimo
           ORDER BY CAST(s.cantidad AS REAL) / r.stock_minimo, r.nombre LIMIT 20"""
    )
    for fila in filas:
        if fila["cantidad_actual"] == 0:
            fila["estado"] = "agotado - reponer"
        elif fila["cantidad_actual"] < fila["stock_minimo"]:
            fila["estado"] = "bajo el minimo - reponer"
        else:
            fila["estado"] = "en el minimo - reponer"
    return {
        "total_a_reponer": len(filas),
        "indicacion": f"Hay {len(filas)} repuestos por reponer; menciona los {len(filas)}.",
        "repuestos": filas,
    }


@mcp.tool()
def historial_vehiculo(placa: str) -> dict:
    """Devuelve los datos de un vehiculo y sus ordenes de trabajo (fecha, motivo, tecnico, estado),
    de la mas reciente a la mas antigua. La placa tiene el formato ABC-123.
    Usar cuando el usuario pregunte que trabajos se le hicieron a una placa o cuando fue su ultima visita."""
    placa = placa.strip().upper()
    if len(placa) == 6 and "-" not in placa:
        placa = f"{placa[:3]}-{placa[3:]}"
    vehiculo = consultar("SELECT placa, marca, modelo, anio FROM vehiculos WHERE placa = ? LIMIT 1", (placa,))
    if not vehiculo:
        return {"placa": placa, "encontrado": False, "mensaje": "No hay un vehiculo registrado con esa placa"}
    ordenes = consultar(
        """SELECT o.id AS ot, substr(o.fecha_hora, 1, 10) AS fecha, o.kilometraje, o.motivo, o.tecnico,
                  o.estado, o.observaciones
           FROM ordenes_trabajo o JOIN vehiculos v ON v.id = o.id_vehiculo
           WHERE v.placa = ? ORDER BY o.fecha_hora DESC LIMIT 10""",
        (placa,),
    )
    return {"encontrado": True, "vehiculo": vehiculo[0], "ordenes": ordenes}


@mcp.tool()
def historial_cliente(dni: str) -> dict:
    """Devuelve los vehiculos y las ordenes de trabajo de un cliente buscado por su DNI de 8 digitos.
    No devuelve el nombre del cliente. Usar cuando el usuario pregunte por el historial de un DNI."""
    dni = "".join(c for c in dni if c.isdigit())
    if len(dni) != 8:
        return {"encontrado": False, "mensaje": "El DNI debe tener 8 digitos"}
    ordenes = consultar(
        """SELECT o.id AS ot, substr(o.fecha_hora, 1, 10) AS fecha, v.placa, v.marca, v.modelo,
                  o.motivo, o.tecnico, o.estado
           FROM ordenes_trabajo o
           JOIN clientes c ON c.id = o.id_cliente
           JOIN vehiculos v ON v.id = o.id_vehiculo
           WHERE c.dni = ? ORDER BY o.fecha_hora DESC LIMIT 10""",
        (dni,),
    )
    if not ordenes:
        return {"dni": dni, "encontrado": False, "mensaje": "No hay ordenes de trabajo para ese DNI"}
    return {"dni": dni, "encontrado": True, "ordenes": ordenes}


@mcp.tool()
def ordenes_pendientes(tecnico: str = "") -> dict:
    """Lista las ordenes de trabajo que no estan cerradas (estado 'abierta' o 'en proceso'),
    con placa, motivo, tecnico y fecha de ingreso. Se puede filtrar por nombre del tecnico.
    Usar cuando el usuario pregunte que trabajos estan pendientes o en proceso, que tiene asignado un tecnico,
    o que vehiculos/carros/autos estan en el taller ahora (los que tienen una orden sin cerrar)."""
    filas = consultar(
        """SELECT o.id AS ot, substr(o.fecha_hora, 1, 10) AS fecha, v.placa, v.marca, v.modelo,
                  o.motivo, o.tecnico, o.estado
           FROM ordenes_trabajo o JOIN vehiculos v ON v.id = o.id_vehiculo
           WHERE o.estado <> 'cerrada' AND sin_tildes(o.tecnico) LIKE ? ESCAPE '!'
           ORDER BY o.fecha_hora LIMIT 20""",
        (f"%{_escapar_like(_sin_tildes(tecnico).strip())}%",),
    )
    return {"total": len(filas), "ordenes": filas}


@mcp.tool()
def resumen_ordenes_por_tecnico(fecha_inicio: str, fecha_fin: str) -> dict:
    """Cuenta las ordenes de trabajo de cada tecnico entre dos fechas (formato AAAA-MM-DD, ambas incluidas),
    separadas en abiertas, en proceso y cerradas.
    Usar cuando el usuario pregunte cuantas ordenes hubo en un periodo, quien atendio mas o por un reporte."""
    try:
        inicio, fin = date.fromisoformat(fecha_inicio), date.fromisoformat(fecha_fin)
    except ValueError:
        return {"error": "Las fechas deben tener el formato AAAA-MM-DD"}
    filas = consultar(
        """SELECT tecnico, COUNT(*) AS total,
                  SUM(estado = 'abierta') AS abiertas,
                  SUM(estado = 'en proceso') AS en_proceso,
                  SUM(estado = 'cerrada') AS cerradas
           FROM ordenes_trabajo
           WHERE substr(fecha_hora, 1, 10) BETWEEN ? AND ?
           GROUP BY tecnico ORDER BY total DESC LIMIT 20""",
        (inicio.isoformat(), fin.isoformat()),
    )
    return {"desde": inicio.isoformat(), "hasta": fin.isoformat(), "total_ordenes": sum(f["total"] for f in filas), "por_tecnico": filas}


if __name__ == "__main__":
    mcp.run()  # transporte stdio: lo enciende el agente
