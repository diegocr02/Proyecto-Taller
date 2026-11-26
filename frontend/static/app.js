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

const ICONO_MENSAJE = { info: "i-info", exito: "i-check", error: "i-alert", advertencia: "i-alert" };

function icono(nombre, clase = "") {
    return `<svg class="${clase}"><use href="#${nombre}"/></svg>`;
}

function mostrarMensaje(contenedor, texto, tipo = "info") {
    contenedor.innerHTML = `<p class="mensaje ${tipo}">${icono(ICONO_MENSAJE[tipo] || "i-info")}${escapar(texto)}</p>`;
}

let temporizadorToast = null;
function mostrarToast(texto) {
    const toast = document.getElementById("toast");
    toast.textContent = texto;
    toast.hidden = false;
    clearTimeout(temporizadorToast);
    temporizadorToast = setTimeout(() => (toast.hidden = true), 3500);
}

// Insignia de color según el estado de la OT
function insigniaEstado(estado) {
    const valor = String(estado || "").toLowerCase();
    const clase = valor.includes("cerr") ? "exito" : valor.includes("proceso") ? "info" : "aviso";
    const texto = valor.replace("_", " ");
    return `<span class="insignia ${clase}">${escapar(texto.charAt(0).toUpperCase() + texto.slice(1))}</span>`;
}

function mostrarError(contenedor, error, reintentar) {
    contenedor.innerHTML = `<p class="mensaje error">${icono("i-alert")}${escapar(error.message)}</p>`;
    if (error.reintentable && reintentar) {
        const boton = document.createElement("button");
        boton.type = "button";
        boton.className = "secundario";
        boton.innerHTML = `${icono("i-refresh")}Reintentar`;
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
    asistente: () => document.querySelector("#form-asistente textarea").focus(),
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
    document.getElementById("btn-campana").hidden = !permitidas.includes("alertas");
    let guardada = null;
    try { localStorage.setItem("rol", rolActual()); guardada = localStorage.getItem("pantalla"); } catch (e) { /* sin almacenamiento */ }
    mostrarPantalla(permitidas.includes(guardada) ? guardada : permitidas[0]);
}

// Contador de alertas en la pestaña y la campana (no bloquea si falla)
let codigosStockBajo = new Set();
async function actualizarContadorAlertas() {
    try {
        const datos = await peticion("/alertas");
        pintarContador(datos.alertas);
    } catch (e) { /* el contador es opcional */ }
}

function pintarContador(alertas) {
    codigosStockBajo = new Set(alertas.map((a) => a.codigo));
    const contador = document.getElementById("contador-alertas");
    contador.textContent = alertas.length;
    contador.hidden = alertas.length === 0;
    document.getElementById("punto-alertas").hidden = alertas.length === 0;
}

// ---------------------------------------------------------------------------
// Registro de OT (Requisito 1)
// ---------------------------------------------------------------------------
function actualizarResumenOT(form) {
    const valor = (n) => String(form.elements[n].value || "").trim();
    const vehiculo = [valor("placa").toUpperCase(), [valor("marca"), valor("modelo")].filter(Boolean).join(" ")].filter(Boolean).join(" · ");
    document.getElementById("res-vehiculo").textContent = vehiculo || "—";
    document.getElementById("res-cliente").textContent = valor("nombre") || "—";
    document.getElementById("res-tecnico").textContent = valor("tecnico") || "Sin asignar";

    let completos = 0;
    let total = 0;
    document.querySelectorAll("#progreso-ot li").forEach((li) => {
        const campos = [...form.querySelectorAll(`[data-grupo="${li.dataset.grupo}"]`)];
        const llenos = campos.filter((c) => String(c.value).trim() !== "").length;
        li.querySelector("b").textContent = `${llenos} / ${campos.length}`;
        li.classList.toggle("completo", llenos === campos.length);
        completos += llenos;
        total += campos.length;
    });
    document.getElementById("barra-ot").style.width = `${Math.round((completos / total) * 100)}%`;
    const aviso = document.getElementById("aviso-ot");
    const listo = completos === total;
    aviso.classList.toggle("listo", listo);
    aviso.innerHTML = listo
        ? `${icono("i-check", "mini")}Todo listo. Puedes registrar la OT.`
        : `${icono("i-info", "mini")}Completa todos los campos obligatorios para registrar la OT.`;
}

function iniciarOrdenes() {
    const form = document.getElementById("form-ot");
    const resultado = document.getElementById("resultado-ot");
    form.anio.max = new Date().getFullYear();

    form.addEventListener("input", (evento) => {
        evento.target.classList.remove("invalido");
        actualizarResumenOT(form);
    });
    form.addEventListener("reset", () => setTimeout(() => {
        resultado.innerHTML = "";
        form.querySelectorAll(".invalido").forEach((el) => el.classList.remove("invalido"));
        actualizarResumenOT(form);
    }));
    actualizarResumenOT(form);

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
                form.reset(); // solo se limpia tras éxito; ante error se conservan los datos (R1.7)
                setTimeout(() => mostrarMensaje(resultado, `${respuesta.mensaje}. Identificador de OT: ${respuesta.id_ot}`, "exito"));
                mostrarToast(`✓ OT ${respuesta.id_ot} registrada`);
            } catch (error) {
                if (error.estado === 422 && error.cuerpo && error.cuerpo.campos) {
                    error.cuerpo.campos.forEach((campo) => form.elements[campo] && form.elements[campo].classList.add("invalido"));
                    const primero = form.querySelector(".invalido");
                    if (primero) primero.focus();
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
                        { titulo: "OT", html: (o) => `<span class="mono">#${escapar(o.id)}</span>` },
                        { titulo: "Fecha", html: (o) => escapar(formatearFecha(o.fecha)) },
                        { titulo: "Motivo", campo: "motivo" },
                        { titulo: "Estado", html: (o) => insigniaEstado(o.estado) },
                    ],
                    datos.ordenes,
                    () => "seleccionable"
                );
        });
    });

    resultado.addEventListener("click", (evento) => {
        const fila = evento.target.closest("tr.seleccionable");
        if (!fila) return;
        resultado.querySelectorAll("tr.seleccionado").forEach((f) => f.classList.remove("seleccionado"));
        fila.classList.add("seleccionado");
        ejecutar(detalle, async () => {
            const ot = await peticion(`/historial/${encodeURIComponent(fila.dataset.id)}`);
            detalle.innerHTML = `
                <div class="tarjeta detalle-tarjeta">
                    <h3>${icono("i-file")}Orden de trabajo #${escapar(ot.id)} ${insigniaEstado(ot.estado)}</h3>
                    <dl class="detalle">
                        <div><dt>Fecha</dt><dd>${escapar(formatearFecha(ot.fecha))}</dd></div>
                        <div><dt>Técnico</dt><dd>${escapar(ot.tecnico)}</dd></div>
                        <div class="ancho-total"><dt>Motivo</dt><dd>${escapar(ot.motivo)}</dd></div>
                        <div class="ancho-total"><dt>Observaciones</dt><dd>${escapar(ot.observaciones || "—")}</dd></div>
                    </dl>
                </div>`;
            detalle.scrollIntoView({ behavior: "smooth", block: "nearest" });
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
            resultado.innerHTML =
                `<p class="nota">${datos.resultados.length} repuesto(s) encontrados.</p>` +
                tabla(
                    [
                        { titulo: "Repuesto", campo: "nombre" },
                        { titulo: "Código", html: (r) => `<span class="mono">${escapar(r.codigo)}</span>` },
                        { titulo: "Stock", html: (r) => `<b>${escapar(r.cantidad)}</b> ${escapar(r.unidad)}` },
                        {
                            titulo: "Estado",
                            html: (r) => r.cantidad === 0
                                ? '<span class="insignia error">Agotado</span>'
                                : codigosStockBajo.has(r.codigo)
                                    ? '<span class="insignia aviso">⚠ Stock bajo</span>'
                                    : '<span class="insignia exito">✓ En stock</span>',
                        },
                    ],
                    datos.resultados
                );
        });
    });
    document.getElementById("chips-inventario").addEventListener("click", (evento) => {
        const chip = evento.target.closest(".chip");
        if (!chip) return;
        form.q.value = chip.textContent;
        form.requestSubmit();
    });
}

// ---------------------------------------------------------------------------
// Alertas (Requisito 4)
// ---------------------------------------------------------------------------
function cargarAlertas() {
    const resultado = document.getElementById("resultado-alertas");
    ejecutar(resultado, async () => {
        const datos = await peticion("/alertas");
        pintarContador(datos.alertas);
        if (!datos.alertas.length) return mostrarMensaje(resultado, datos.mensaje, "exito");
        const criticas = datos.alertas.filter((a) => a.cantidad < a.stock_minimo).length;
        const faltan = datos.alertas.reduce((s, a) => s + Math.max(a.stock_minimo - a.cantidad, 0), 0);
        const tarjetas = datos.alertas
            .slice()
            .sort((a, b) => a.cantidad / (a.stock_minimo || 1) - b.cantidad / (b.stock_minimo || 1))
            .map((a) => {
                const critica = a.cantidad < a.stock_minimo;
                const pct = Math.min(100, Math.round((a.cantidad / (a.stock_minimo || 1)) * 100));
                return `
                <article class="tarjeta-alerta ${critica ? "critica" : ""}">
                    <div class="fila">
                        <div><h4>${escapar(a.nombre)}</h4><span class="mono">${escapar(a.codigo)}</span></div>
                        <span class="insignia ${critica ? "error" : "aviso"}">${critica ? "Bajo mínimo" : "En el mínimo"}</span>
                    </div>
                    <div class="numeros"><span>Actual <b>${escapar(a.cantidad)}</b></span><span>Mínimo <b>${escapar(a.stock_minimo)}</b></span></div>
                    <div class="medidor"><span style="width:${pct}%"></span></div>
                </article>`;
            })
            .join("");
        resultado.innerHTML = `
            <div class="resumen-kpi">
                <div class="kpi amarillo"><span>Repuestos en alerta</span><strong>${datos.alertas.length}</strong></div>
                <div class="kpi rojo"><span>Por debajo del mínimo</span><strong>${criticas}</strong></div>
                <div class="kpi azul"><span>Unidades para llegar al mínimo</span><strong>${faltan}</strong></div>
            </div>
            <div class="rejilla-alertas">${tarjetas}</div>`;
    });
}

// ---------------------------------------------------------------------------
// Comparación de conteo físico (Requisito 5)
// ---------------------------------------------------------------------------
function agregarFilaConteo() {
    const fila = document.createElement("div");
    fila.className = "fila-conteo";
    fila.innerHTML = `
        <span class="entrada">${icono("i-box")}<input name="codigo" placeholder="Código (ej. REP-001)" maxlength="20"></span>
        <input name="conteo_fisico" type="number" min="0" placeholder="Conteo físico">
        <button type="button" class="quitar" aria-label="Quitar fila">${icono("i-x")}</button>`;
    fila.querySelector(".quitar").addEventListener("click", () => fila.remove());
    document.getElementById("filas-conteo").appendChild(fila);
    fila.querySelector("input").focus();
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
                const descuadres = datos.resultados.filter((r) => r.descuadre).length;
                html += `
                    <div class="resumen-kpi">
                        <div class="kpi azul"><span>Repuestos comparados</span><strong>${datos.resultados.length}</strong></div>
                        <div class="kpi verde"><span>Cuadran</span><strong>${datos.resultados.length - descuadres}</strong></div>
                        <div class="kpi rojo"><span>Con descuadre</span><strong>${descuadres}</strong></div>
                    </div>`;
                html += tabla(
                    [
                        { titulo: "Repuesto", campo: "nombre" },
                        { titulo: "Código", html: (r) => `<span class="mono">${escapar(r.codigo)}</span>` },
                        { titulo: "Sistema", campo: "sistema" },
                        { titulo: "Conteo físico", campo: "conteo" },
                        {
                            titulo: "Diferencia",
                            html: (r) => `<span class="${r.diferencia > 0 ? "diferencia-pos" : r.diferencia < 0 ? "diferencia-neg" : ""}">${escapar(r.diferencia > 0 ? `+${r.diferencia}` : r.diferencia)}</span>`,
                        },
                        {
                            titulo: "Estado",
                            html: (r) => (r.descuadre ? '<span class="insignia aviso etiqueta-descuadre">⚠ Descuadre</span>' : '<span class="insignia exito">✓ Cuadra</span>'),
                        },
                    ],
                    datos.resultados,
                    (r) => (r.descuadre ? "descuadre" : "")
                );
            }
            if (datos.mensaje) html += `<p class="mensaje advertencia">${icono("i-alert")}${escapar(datos.mensaje)}</p>`;
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
            const suma = (campo) => datos.reporte.reduce((s, r) => s + (Number(r[campo]) || 0), 0);
            const maximo = Math.max(...datos.reporte.map((r) => Number(r.total) || 0), 1);
            const ancho = (v) => `${((Number(v) || 0) / maximo) * 100}%`;
            const barras = datos.reporte
                .map((r) => `
                    <div class="grafico-fila">
                        <span>${escapar(r.tecnico)}</span>
                        <div class="grafico-barra" title="Abiertas ${escapar(r.abierta)} · En proceso ${escapar(r.en_proceso)} · Cerradas ${escapar(r.cerrada)}">
                            <span class="seg-abierta" style="width:${ancho(r.abierta)}"></span>
                            <span class="seg-proceso" style="width:${ancho(r.en_proceso)}"></span>
                            <span class="seg-cerrada" style="width:${ancho(r.cerrada)}"></span>
                        </div>
                        <b>${escapar(r.total)}</b>
                    </div>`)
                .join("");
            resultado.innerHTML = `
                <div class="resumen-kpi">
                    <div class="kpi azul"><span>Total de OT</span><strong>${suma("total")}</strong></div>
                    <div class="kpi amarillo"><span>Abiertas</span><strong>${suma("abierta")}</strong></div>
                    <div class="kpi azul"><span>En proceso</span><strong>${suma("en_proceso")}</strong></div>
                    <div class="kpi verde"><span>Cerradas</span><strong>${suma("cerrada")}</strong></div>
                </div>
                <div class="leyenda"><span><i class="seg-abierta"></i>Abiertas</span><span><i class="seg-proceso"></i>En proceso</span><span><i class="seg-cerrada"></i>Cerradas</span></div>
                <div class="grafico">${barras}</div>
                ${tabla(
                    [
                        { titulo: "Técnico", campo: "tecnico" },
                        { titulo: "Total OT", campo: "total" },
                        { titulo: "Abiertas", campo: "abierta" },
                        { titulo: "En proceso", campo: "en_proceso" },
                        { titulo: "Cerradas", campo: "cerrada" },
                    ],
                    datos.reporte
                )}
                <a class="boton" href="/reportes/csv?${parametros}" download>${icono("i-download")}Exportar CSV</a>`;
        });
    });
}

// ---------------------------------------------------------------------------
// Asistente IA (Requisito 9) — chat con conversaciones guardadas en el navegador
// ---------------------------------------------------------------------------
const CLAVE_CONVERSACIONES = "conversaciones_jorgebot";
let conversaciones = [];
let conversacionActual = null;
let esperandoRespuesta = false;

function horaCorta(fecha = new Date()) {
    return fecha.toLocaleTimeString("es-PE", { hour: "2-digit", minute: "2-digit" });
}

function guardarConversaciones() {
    try { localStorage.setItem(CLAVE_CONVERSACIONES, JSON.stringify(conversaciones.slice(0, 15))); } catch (e) { /* sin almacenamiento */ }
}

// Convierte el texto plano de la IA en párrafos y listas (el texto se escapa primero)
function formatearRespuesta(texto) {
    const lineas = escapar(texto).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").split("\n");
    let html = "";
    let enLista = false;
    for (const linea of lineas) {
        const item = linea.match(/^\s*[-•*]\s+(.*)$/);
        if (item) {
            if (!enLista) { html += "<ul>"; enLista = true; }
            html += `<li>${item[1]}</li>`;
            continue;
        }
        if (enLista) { html += "</ul>"; enLista = false; }
        if (linea.trim()) html += `<p>${linea}</p>`;
    }
    return html + (enLista ? "</ul>" : "");
}

// Muestra qué herramienta MCP usó el agente para responder (útil para la demostración)
function htmlHerramientas(herramientas) {
    if (!herramientas || !herramientas.length) return "";
    const unicas = [...new Set(herramientas)];
    return `<div class="herramientas-usadas">${icono("i-wrench")}Herramienta MCP: ${unicas.map((h) => `<code>${escapar(h)}</code>`).join(" ")}</div>`;
}

function htmlMensaje(m) {
    if (m.rol === "usuario") {
        return `<div class="burbuja-fila usuario">
            <div class="avatar">${icono("i-user")}</div>
            <div class="burbuja"><p>${escapar(m.texto)}</p><span class="hora">${escapar(m.hora)} ✓✓</span></div>
        </div>`;
    }
    return `<div class="burbuja-fila bot">
        <img class="avatar-bot" src="/static/img/jorgebot.webp" alt="">
        <div class="burbuja ${m.error ? "error" : ""}">${formatearRespuesta(m.texto)}${htmlHerramientas(m.herramientas)}<span class="hora">${escapar(m.hora)}</span></div>
    </div>`;
}

function pintarChat() {
    const contenedor = document.getElementById("resultado-asistente");
    const mensajes = conversacionActual ? conversacionActual.mensajes : [];
    contenedor.innerHTML = mensajes.length
        ? mensajes.map(htmlMensaje).join("")
        : `<div class="bienvenida">
               <img src="/static/img/jorgebot.webp" alt="">
               <h3>¡Hola! Soy JorgeBot</h3>
               <p>Soy un asistente de inteligencia artificial. Consulto el sistema del taller para decirte el stock de repuestos, qué reponer, el historial de una placa o DNI, las órdenes pendientes y el resumen por técnico.</p>
           </div>`;
    if (esperandoRespuesta) {
        contenedor.insertAdjacentHTML("beforeend",
            `<div class="burbuja-fila bot"><img class="avatar-bot" src="/static/img/jorgebot.webp" alt="">
             <div class="burbuja escribiendo"><span></span><span></span><span></span></div></div>`);
    }
    contenedor.scrollTop = contenedor.scrollHeight;
    pintarRecientes();
}

function pintarRecientes() {
    const lista = document.getElementById("lista-recientes");
    if (!conversaciones.length) {
        lista.innerHTML = '<li class="vacio">Aún no hay conversaciones.</li>';
        return;
    }
    lista.innerHTML = conversaciones
        .map((c) => `<li data-id="${escapar(c.id)}" class="${c === conversacionActual ? "activa" : ""}">
            ${icono("i-msg")}<span>${escapar(c.titulo)}</span><small>${escapar(c.hora)}</small></li>`)
        .join("");
}

function nuevaConversacion() {
    conversacionActual = null;
    pintarChat();
    document.querySelector("#form-asistente textarea").focus();
}

async function enviarPregunta(pregunta) {
    pregunta = pregunta.trim();
    if (!pregunta || esperandoRespuesta) return;
    if (!conversacionActual) {
        conversacionActual = { id: String(Date.now()), titulo: pregunta.slice(0, 40), hora: horaCorta(), mensajes: [] };
        conversaciones.unshift(conversacionActual);
    }
    const conversacion = conversacionActual;
    const botonEnviar = document.querySelector("#form-asistente .enviar");
    conversacion.mensajes.push({ rol: "usuario", texto: pregunta, hora: horaCorta() });
    conversacion.hora = horaCorta();
    esperandoRespuesta = true;
    botonEnviar.disabled = true;
    pintarChat();

    try {
        const datos = await enviarJson("/asistente", { pregunta, rol: rolActual(), sesion: conversacion.id });
        if (datos.asistencia === null) {
            conversacion.mensajes.push({ rol: "bot", texto: datos.mensaje, hora: horaCorta(), error: true });
        } else {
            conversacion.mensajes.push({ rol: "bot", texto: datos.asistencia, hora: horaCorta(), herramientas: datos.herramientas });
        }
    } catch (error) {
        const texto = error instanceof ErrorApi ? error.message : "Ocurrió un error inesperado.";
        conversacion.mensajes.push({ rol: "bot", texto, hora: horaCorta(), error: true });
    } finally {
        esperandoRespuesta = false;
        botonEnviar.disabled = false;
        guardarConversaciones();
        pintarChat();
    }
}

function iniciarAsistente() {
    const form = document.getElementById("form-asistente");
    const area = form.pregunta;
    try { conversaciones = JSON.parse(localStorage.getItem(CLAVE_CONVERSACIONES)) || []; } catch (e) { conversaciones = []; }

    const ajustarAltura = () => { area.style.height = "auto"; area.style.height = `${Math.min(area.scrollHeight, 140)}px`; };
    area.addEventListener("input", ajustarAltura);
    area.addEventListener("keydown", (evento) => {
        if (evento.key === "Enter" && !evento.shiftKey) { evento.preventDefault(); form.requestSubmit(); }
    });
    form.addEventListener("submit", (evento) => {
        evento.preventDefault();
        const pregunta = area.value;
        area.value = "";
        ajustarAltura();
        enviarPregunta(pregunta);
    });
    document.getElementById("sugerencias").addEventListener("click", (evento) => {
        const chip = evento.target.closest(".chip");
        if (chip) enviarPregunta(chip.dataset.pregunta);
    });
    document.getElementById("btn-nueva-conversacion").addEventListener("click", nuevaConversacion);
    document.getElementById("btn-limpiar-chat").addEventListener("click", () => {
        if (!conversacionActual) return;
        // El agente también olvida esa conversación
        fetch(`/asistente/sesion/${encodeURIComponent(conversacionActual.id)}?rol=${encodeURIComponent(rolActual())}`, { method: "DELETE" }).catch(() => {});
        conversaciones = conversaciones.filter((c) => c !== conversacionActual);
        guardarConversaciones();
        nuevaConversacion();
    });
    document.getElementById("lista-recientes").addEventListener("click", (evento) => {
        const item = evento.target.closest("li[data-id]");
        if (!item || esperandoRespuesta) return;
        conversacionActual = conversaciones.find((c) => c.id === item.dataset.id) || null;
        pintarChat();
    });
    pintarChat();
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
    document.getElementById("btn-campana").addEventListener("click", () => mostrarPantalla("alertas"));
    selectorRol.addEventListener("change", aplicarRol);

    iniciarOrdenes();
    iniciarHistorial();
    iniciarInventario();
    iniciarComparacion();
    iniciarReportes();
    iniciarAsistente();
    aplicarRol();
    actualizarContadorAlertas();
});

