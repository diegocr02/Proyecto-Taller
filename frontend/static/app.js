// Historia: H-01..H-09 (pantallas), H-07 (indicador de carga y timeouts)
// Lógica de cliente para la interfaz de Jorge Motors
"use strict";

// ---------------------------------------------------------------------------
// Peticiones con indicador de carga (2 s) y tiempo límite (30 s) — Requisito 7
// ---------------------------------------------------------------------------
const RETRASO_SPINNER_MS = 2000;
const TIEMPO_LIMITE_MS = 30000;
let peticionesActivas = 0;

class ErrorApi extends Error {
    constructor(mensaje, estado, cuerpo, reintentable) {
        super(mensaje);
        this.estado = estado;
        this.cuerpo = cuerpo;
        this.reintentable = reintentable;
    }
}

function mostrarSpinner() {
    document.getElementById("spinner").hidden = false;
}

function ocultarSpinnerSiCorresponde() {
    if (peticionesActivas === 0) document.getElementById("spinner").hidden = true;
}

async function peticion(url, opciones = {}) {
    const controlador = new AbortController();
    peticionesActivas++;
    const temporizadorSpinner = setTimeout(mostrarSpinner, RETRASO_SPINNER_MS);
    const temporizadorLimite = setTimeout(() => controlador.abort(), TIEMPO_LIMITE_MS);
    try {
        const respuesta = await fetch(url, { ...opciones, signal: controlador.signal });
        const esJson = (respuesta.headers.get("content-type") || "").includes("application/json");
        const cuerpo = esJson ? await respuesta.json() : await respuesta.text();
        if (!respuesta.ok) {
            const detalle = cuerpo && cuerpo.detail ? cuerpo.detail : "Error inesperado del servidor";
            throw new ErrorApi(String(detalle), respuesta.status, cuerpo, respuesta.status >= 500);
        }
        return cuerpo;
    } catch (error) {
        if (error instanceof ErrorApi) throw error;
        if (error.name === "AbortError") {
            throw new ErrorApi("La operación no pudo completarse: se superaron los 30 segundos sin respuesta.", 0, null, true);
        }
        throw new ErrorApi("No se pudo conectar con el servidor. Servicio no disponible.", 0, null, true);
    } finally {
        clearTimeout(temporizadorSpinner);
        clearTimeout(temporizadorLimite);
        peticionesActivas--;
        ocultarSpinnerSiCorresponde();
    }
}

function enviarJson(url, datos) {
    return peticion(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datos),
    });
}

// ---------------------------------------------------------------------------
// Utilidades de presentación
// ---------------------------------------------------------------------------
function escapar(valor) {
    const div = document.createElement("div");
    div.textContent = valor == null ? "" : String(valor);
    return div.innerHTML;
}

function mostrarMensaje(contenedor, texto, tipo = "info") {
    contenedor.innerHTML = `<p class="mensaje ${tipo}">${escapar(texto)}</p>`;
}

function mostrarError(contenedor, error, reintentar) {
    contenedor.innerHTML = `<p class="mensaje error">${escapar(error.message)}</p>`;
    if (error.reintentable && reintentar) {
        const boton = document.createElement("button");
        boton.type = "button";
        boton.className = "secundario";
        boton.textContent = "Reintentar";
        boton.addEventListener("click", reintentar);
        contenedor.appendChild(boton);
    }
}

// Ejecuta una acción asíncrona mostrando el error (con reintento) en el contenedor
async function ejecutar(contenedor, accion) {
    try {
        await accion();
    } catch (error) {
        if (!(error instanceof ErrorApi)) {
            console.error(error);
            error = new ErrorApi("Ocurrió un error inesperado.", 0, null, true);
        }
        mostrarError(contenedor, error, () => ejecutar(contenedor, accion));
    }
}

function tabla(columnas, filas, claseFila) {
    const cabecera = columnas.map((c) => `<th>${escapar(c.titulo)}</th>`).join("");
    const cuerpo = filas
        .map((fila) => {
            const clase = claseFila ? claseFila(fila) : "";
            const celdas = columnas.map((c) => `<td>${c.html ? c.html(fila) : escapar(fila[c.campo])}</td>`).join("");
            return `<tr class="${clase}" data-id="${escapar(fila.id ?? "")}">${celdas}</tr>`;
        })
        .join("");
    return `<div class="tabla-contenedor"><table><thead><tr>${cabecera}</tr></thead><tbody>${cuerpo}</tbody></table></div>`;
}

function formatearFecha(iso) {
    const fecha = new Date(iso);
    return isNaN(fecha) ? iso : fecha.toLocaleString("es-PE");
}

// ---------------------------------------------------------------------------
// Navegación por rol
// ---------------------------------------------------------------------------
const PANTALLAS_POR_ROL = {
    Recepcionista: ["ordenes", "historial", "asistente"],
    "Técnico": ["historial", "inventario", "asistente"],
    Encargado_Compras: ["inventario", "alertas", "comparacion", "asistente"],
    Gerente: ["ordenes", "historial", "inventario", "alertas", "comparacion", "reportes", "asistente"],
};

const alMostrar = {
    alertas: cargarAlertas,
};

function rolActual() {
    return document.getElementById("rol").value;
}

function mostrarPantalla(nombre) {
    document.querySelectorAll(".pantalla").forEach((s) => (s.hidden = s.id !== `pantalla-${nombre}`));
    document.querySelectorAll("#pestanas button").forEach((b) => b.classList.toggle("activa", b.dataset.pantalla === nombre));
    try { localStorage.setItem("pantalla", nombre); } catch (e) { /* almacenamiento no disponible */ }
    if (alMostrar[nombre]) alMostrar[nombre]();
}

function aplicarRol() {
    const permitidas = PANTALLAS_POR_ROL[rolActual()];
    document.querySelectorAll("#pestanas button").forEach((b) => (b.hidden = !permitidas.includes(b.dataset.pantalla)));
    let guardada = null;
    try { localStorage.setItem("rol", rolActual()); guardada = localStorage.getItem("pantalla"); } catch (e) { /* sin almacenamiento */ }
    mostrarPantalla(permitidas.includes(guardada) ? guardada : permitidas[0]);
}

// ---------------------------------------------------------------------------
// Registro de OT (Requisito 1)
// ---------------------------------------------------------------------------
function iniciarOrdenes() {
    const form = document.getElementById("form-ot");
    const resultado = document.getElementById("resultado-ot");
    form.anio.max = new Date().getFullYear();

    form.addEventListener("submit", (evento) => {
        evento.preventDefault();
        form.querySelectorAll(".invalido").forEach((el) => el.classList.remove("invalido"));
        const datos = Object.fromEntries(new FormData(form));
        // Los campos vacíos se omiten para que el servidor indique cuál falta
        Object.keys(datos).forEach((k) => { if (String(datos[k]).trim() === "") delete datos[k]; });
        if (datos.anio) datos.anio = Number(datos.anio);
        if (datos.kilometraje) datos.kilometraje = Number(datos.kilometraje);

        ejecutar(resultado, async () => {
            try {
                const respuesta = await enviarJson("/ordenes", datos);
                mostrarMensaje(resultado, `${respuesta.mensaje}. Identificador de OT: ${respuesta.id_ot}`, "exito");
                form.reset(); // solo se limpia tras éxito; ante error se conservan los datos (R1.7)
            } catch (error) {
                if (error.estado === 422 && error.cuerpo && error.cuerpo.campos) {
                    error.cuerpo.campos.forEach((campo) => form.elements[campo] && form.elements[campo].classList.add("invalido"));
                }
                throw error;
            }
        });
    });
}

// ---------------------------------------------------------------------------
// Historial (Requisito 2)
// ---------------------------------------------------------------------------
function iniciarHistorial() {
    const form = document.getElementById("form-historial");
    const resultado = document.getElementById("resultado-historial");
    const detalle = document.getElementById("detalle-historial");

    form.addEventListener("submit", (evento) => {
        evento.preventDefault();
        detalle.innerHTML = "";
        const q = form.q.value.trim();
        ejecutar(resultado, async () => {
            const datos = await peticion(`/historial?q=${encodeURIComponent(q)}`);
            if (!datos.ordenes.length) return mostrarMensaje(resultado, datos.mensaje);
            resultado.innerHTML =
                `<p class="nota">${datos.ordenes.length} orden(es) encontradas. Seleccione una para ver el detalle.</p>` +
                tabla(
                    [
                        { titulo: "OT", campo: "id" },
                        { titulo: "Fecha", html: (o) => escapar(formatearFecha(o.fecha)) },
                        { titulo: "Motivo", campo: "motivo" },
                        { titulo: "Estado", campo: "estado" },
                    ],
                    datos.ordenes,
                    () => "seleccionable"
                );
        });
    });

    resultado.addEventListener("click", (evento) => {
        const fila = evento.target.closest("tr.seleccionable");
        if (!fila) return;
        ejecutar(detalle, async () => {
            const ot = await peticion(`/historial/${encodeURIComponent(fila.dataset.id)}`);
            detalle.innerHTML = `
                <dl class="detalle">
                    <dt>Identificador</dt><dd>${escapar(ot.id)}</dd>
                    <dt>Fecha</dt><dd>${escapar(formatearFecha(ot.fecha))}</dd>
                    <dt>Motivo</dt><dd>${escapar(ot.motivo)}</dd>
                    <dt>Técnico</dt><dd>${escapar(ot.tecnico)}</dd>
                    <dt>Estado</dt><dd>${escapar(ot.estado)}</dd>
                    <dt>Observaciones</dt><dd>${escapar(ot.observaciones || "—")}</dd>
                </dl>`;
        });
    });
}

// ---------------------------------------------------------------------------
// Inventario (Requisito 3)
// ---------------------------------------------------------------------------
function iniciarInventario() {
    const form = document.getElementById("form-inventario");
    const resultado = document.getElementById("resultado-inventario");
    form.addEventListener("submit", (evento) => {
        evento.preventDefault();
        const q = form.q.value;
        ejecutar(resultado, async () => {
            const datos = await peticion(`/inventario?q=${encodeURIComponent(q)}`);
            if (!datos.resultados.length) return mostrarMensaje(resultado, datos.mensaje);
            resultado.innerHTML = tabla(
                [
                    { titulo: "Nombre", campo: "nombre" },
                    { titulo: "Código", campo: "codigo" },
                    { titulo: "Cantidad", campo: "cantidad" },
                    { titulo: "Unidad", campo: "unidad" },
                ],
                datos.resultados
            );
        });
    });
}

// ---------------------------------------------------------------------------
// Alertas (Requisito 4)
// ---------------------------------------------------------------------------
function cargarAlertas() {
    const resultado = document.getElementById("resultado-alertas");
    ejecutar(resultado, async () => {
        const datos = await peticion("/alertas");
        if (!datos.alertas.length) return mostrarMensaje(resultado, datos.mensaje, "exito");
        resultado.innerHTML = tabla(
            [
                { titulo: "Nombre", campo: "nombre" },
                { titulo: "Código", campo: "codigo" },
                { titulo: "Cantidad actual", campo: "cantidad" },
                { titulo: "Stock mínimo", campo: "stock_minimo" },
            ],
            datos.alertas,
            () => "alerta"
        );
    });
}

// ---------------------------------------------------------------------------
// Comparación de conteo físico (Requisito 5)
// ---------------------------------------------------------------------------
function agregarFilaConteo() {
    const fila = document.createElement("div");
    fila.className = "fila-conteo";
    fila.innerHTML = `
        <input name="codigo" placeholder="Código (ej. REP-001)" maxlength="20">
        <input name="conteo_fisico" type="number" min="0" placeholder="Conteo físico">
        <button type="button" class="quitar" aria-label="Quitar fila">✕</button>`;
    fila.querySelector(".quitar").addEventListener("click", () => fila.remove());
    document.getElementById("filas-conteo").appendChild(fila);
}

function iniciarComparacion() {
    const form = document.getElementById("form-comparacion");
    const resultado = document.getElementById("resultado-comparacion");
    document.getElementById("btn-agregar-fila").addEventListener("click", agregarFilaConteo);
    agregarFilaConteo();

    form.addEventListener("submit", (evento) => {
        evento.preventDefault();
        const items = [...form.querySelectorAll(".fila-conteo")]
            .map((f) => ({ codigo: f.querySelector("[name=codigo]").value.trim(), conteo: f.querySelector("[name=conteo_fisico]").value }))
            .filter((i) => i.codigo !== "" && i.conteo !== "")
            .map((i) => ({ codigo: i.codigo, conteo_fisico: Number(i.conteo) }));

        ejecutar(resultado, async () => {
            const datos = await enviarJson("/comparacion", { items });
            let html = "";
            if (datos.resultados.length) {
                html += tabla(
                    [
                        { titulo: "Nombre", campo: "nombre" },
                        { titulo: "Código", campo: "codigo" },
                        { titulo: "Sistema", campo: "sistema" },
                        { titulo: "Conteo físico", campo: "conteo" },
                        { titulo: "Diferencia", html: (r) => escapar(r.diferencia > 0 ? `+${r.diferencia}` : r.diferencia) },
                        { titulo: "Estado", html: (r) => (r.descuadre ? '<span class="etiqueta-descuadre">⚠ Descuadre</span>' : "✔ Cuadra") },
                    ],
                    datos.resultados,
                    (r) => (r.descuadre ? "descuadre" : "")
                );
            }
            if (datos.mensaje) html += `<p class="mensaje advertencia">${escapar(datos.mensaje)}</p>`;
            resultado.innerHTML = html;
        });
    });
}

// ---------------------------------------------------------------------------
// Reportes (Requisito 6)
// ---------------------------------------------------------------------------
function iniciarReportes() {
    const form = document.getElementById("form-reportes");
    const resultado = document.getElementById("resultado-reportes");
    const hoy = new Date();
    form.fecha_fin.value = hoy.toISOString().slice(0, 10);
    form.fecha_inicio.value = new Date(hoy.getFullYear(), hoy.getMonth(), 1).toISOString().slice(0, 10);

    form.addEventListener("submit", (evento) => {
        evento.preventDefault();
        const parametros = new URLSearchParams({ fecha_inicio: form.fecha_inicio.value, fecha_fin: form.fecha_fin.value });
        ejecutar(resultado, async () => {
            const datos = await peticion(`/reportes?${parametros}`);
            if (!datos.reporte.length) return mostrarMensaje(resultado, datos.mensaje);
            resultado.innerHTML =
                tabla(
                    [
                        { titulo: "Técnico", campo: "tecnico" },
                        { titulo: "Total OT", campo: "total" },
                        { titulo: "Abiertas", campo: "abierta" },
                        { titulo: "En proceso", campo: "en_proceso" },
                        { titulo: "Cerradas", campo: "cerrada" },
                    ],
                    datos.reporte
                ) + `<a class="boton" href="/reportes/csv?${parametros}" download>Exportar CSV</a>`;
        });
    });
}

// ---------------------------------------------------------------------------
// Asistente IA (Requisito 9)
// ---------------------------------------------------------------------------
function iniciarAsistente() {
    const form = document.getElementById("form-asistente");
    const resultado = document.getElementById("resultado-asistente");
    form.addEventListener("submit", (evento) => {
        evento.preventDefault();
        const pregunta = form.pregunta.value;
        ejecutar(resultado, async () => {
            const datos = await enviarJson("/asistente", { pregunta, rol: rolActual() });
            if (datos.asistencia === null) return mostrarMensaje(resultado, datos.mensaje, "advertencia");
            // Si Gemini aún usa **negrita** de Markdown, se muestra como negrita (el texto ya va escapado)
            const texto = escapar(datos.asistencia).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
            resultado.innerHTML = `<div class="respuesta-ia">${texto}</div>
                <p class="nota">Consulta registrada: ${escapar(datos.id_consulta)}</p>`;
        });
    });
}

// ---------------------------------------------------------------------------
// Arranque
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    const selectorRol = document.getElementById("rol");
    try {
        const rolGuardado = localStorage.getItem("rol");
        if (rolGuardado && PANTALLAS_POR_ROL[rolGuardado]) selectorRol.value = rolGuardado;
    } catch (e) { /* sin almacenamiento */ }

    document.querySelectorAll("#pestanas button").forEach((b) => b.addEventListener("click", () => mostrarPantalla(b.dataset.pantalla)));
    document.getElementById("btn-alertas").addEventListener("click", cargarAlertas);
    selectorRol.addEventListener("change", aplicarRol);

    iniciarOrdenes();
    iniciarHistorial();
    iniciarInventario();
    iniciarComparacion();
    iniciarReportes();
    iniciarAsistente();
    aplicarRol();
});
