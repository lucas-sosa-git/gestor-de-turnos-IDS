/*
 * Genera archivos PDF a partir de las secciones HTML
 * que ya están cargadas en el panel administrativo.
 */

(function () {
    "use strict";

    const SELECTORES_EXCLUIDOS = [
        '[data-html2canvas-ignore="true"]',
        ".service-form-card",
        ".edit-service-form",
        ".delete-service-form",
        ".service-actions"
    ];

    /*
     * Espera dos ciclos de renderizado para que el navegador
     * termine de aplicar tamaños, grillas y estilos.
     */
    function esperarRenderizado() {
        return new Promise(function (resolve) {
            window.requestAnimationFrame(function () {
                window.requestAnimationFrame(resolve);
            });
        });
    }

    /*
     * Espera a que las imágenes de la sección terminen de cargar.
     * Si alguna imagen falla, el PDF igualmente se genera.
     */
    function esperarImagenes(elemento) {
        const imagenes = Array.from(
            elemento.querySelectorAll("img")
        );

        return Promise.all(
            imagenes.map(function (imagen) {
                if (imagen.complete) {
                    return Promise.resolve();
                }

                return new Promise(function (resolve) {
                    imagen.addEventListener("load", resolve, {
                        once: true
                    });

                    imagen.addEventListener("error", resolve, {
                        once: true
                    });
                });
            })
        );
    }

    /*
     * Crea el encabezado que aparece únicamente dentro del PDF.
     */
    function crearEncabezado(tituloReporte) {
        const encabezado = document.createElement("div");
        encabezado.className = "pdf-encabezado";

        const titulo = document.createElement("h1");
        titulo.textContent = tituloReporte;

        const fecha = document.createElement("p");
        fecha.textContent =
            "Generado el " +
            new Date().toLocaleString("es-AR");

        encabezado.appendChild(titulo);
        encabezado.appendChild(fecha);

        return encabezado;
    }

    /*
     * Fuerza a que la sección clonada sea visible tanto en el
     * documento real como en la copia interna de html2canvas.
     */
    function hacerVisible(elemento) {
        elemento.classList.add("active");

        elemento.style.setProperty(
            "display",
            "block",
            "important"
        );

        elemento.style.setProperty(
            "visibility",
            "visible",
            "important"
        );

        elemento.style.setProperty(
            "opacity",
            "1",
            "important"
        );

        elemento.style.setProperty(
            "position",
            "static",
            "important"
        );

        elemento.style.setProperty(
            "transform",
            "none",
            "important"
        );
    }

    /*
     * Quita de la copia botones y formularios que no deben salir
     * en el reporte. La dashboard original no se modifica.
     */
    function limpiarCopia(copia) {
        SELECTORES_EXCLUIDOS.forEach(function (selector) {
            copia
                .querySelectorAll(selector)
                .forEach(function (elemento) {
                    elemento.remove();
                });
        });
    }

    /*
     * Crea una copia temporal de la sección a exportar.
     */
    function crearContenedorTemporal(
        seccionOriginal,
        tituloReporte
    ) {
        const copia = seccionOriginal.cloneNode(true);
        const identificador =
            "pdf-temporal-" + Date.now();

        copia.removeAttribute("id");
        hacerVisible(copia);
        limpiarCopia(copia);

        const contenedor = document.createElement("div");
        contenedor.id = identificador;
        contenedor.className =
            "pdf-contenedor-temporal pdf-exportando";

        contenedor.appendChild(
            crearEncabezado(tituloReporte)
        );

        contenedor.appendChild(copia);
        document.body.appendChild(contenedor);

        return {
            elemento: contenedor,
            identificador: identificador
        };
    }

    /*
     * Comprueba que el elemento tenga dimensiones reales antes
     * de pedirle a html2canvas que lo capture.
     */
    function validarDimensiones(elemento) {
        const ancho = Math.max(
            elemento.offsetWidth,
            elemento.scrollWidth
        );

        const alto = Math.max(
            elemento.offsetHeight,
            elemento.scrollHeight
        );

        if (ancho <= 0 || alto <= 0) {
            throw new Error(
                "La sección a exportar no tiene dimensiones visibles."
            );
        }
    }

    /*
     * Función principal llamada por los botones de dashboard.html.
     */
    async function generarPDF(
        idSeccion,
        nombreArchivo,
        tituloReporte,
        boton
    ) {
        const seccionOriginal =
            document.getElementById(idSeccion);

        if (!seccionOriginal) {
            window.alert(
                "No se encontró la sección que se quiere exportar."
            );

            return;
        }

        if (typeof window.html2pdf !== "function") {
            console.error(
                "La librería html2pdf.js no está cargada."
            );

            window.alert(
                "No se pudo cargar la herramienta para generar el PDF. Revisá tu conexión a internet y recargá la página."
            );

            return;
        }

        let contenedorTemporal = null;
        let identificadorTemporal = null;

        const textoOriginalBoton =
            boton ? boton.textContent : "";

        if (boton) {
            boton.disabled = true;
            boton.textContent = "Generando PDF...";
        }

        try {
            if (document.fonts && document.fonts.ready) {
                await document.fonts.ready;
            }

            const temporal = crearContenedorTemporal(
                seccionOriginal,
                tituloReporte
            );

            contenedorTemporal = temporal.elemento;
            identificadorTemporal = temporal.identificador;

            await esperarImagenes(contenedorTemporal);
            await esperarRenderizado();

            validarDimensiones(contenedorTemporal);

            const opciones = {
                margin: [8, 8, 8, 8],
                filename: nombreArchivo,

                image: {
                    type: "jpeg",
                    quality: 0.98
                },

                html2canvas: {
                    scale: 1.5,
                    useCORS: true,
                    allowTaint: false,
                    backgroundColor: "#ffffff",
                    scrollX: 0,
                    scrollY: 0,
                    logging: false,

                    /*
                     * html2canvas clona internamente el documento.
                     * En esa segunda copia volvemos a forzar la
                     * visibilidad para evitar capturas blancas.
                     */
                    onclone: function (documentoClonado) {
                        const contenedorClonado =
                            documentoClonado.getElementById(
                                identificadorTemporal
                            );

                        if (!contenedorClonado) {
                            return;
                        }

                        contenedorClonado.style.setProperty(
                            "display",
                            "block",
                            "important"
                        );

                        contenedorClonado.style.setProperty(
                            "visibility",
                            "visible",
                            "important"
                        );

                        contenedorClonado.style.setProperty(
                            "opacity",
                            "1",
                            "important"
                        );

                        contenedorClonado
                            .querySelectorAll(
                                ".tab-pane-content"
                            )
                            .forEach(function (pestana) {
                                hacerVisible(pestana);
                            });
                    }
                },

                jsPDF: {
                    unit: "mm",
                    format: "a4",
                    orientation: "portrait"
                },

                pagebreak: {
                    mode: ["css", "legacy"],
                    avoid: [
                        ".kpi-card",
                        ".panel-card",
                        ".barbero-card-full",
                        ".service-card",
                        ".cita-row",
                        ".barbero-row",
                        ".servicio-row"
                    ]
                }
            };

            await window
                .html2pdf()
                .set(opciones)
                .from(contenedorTemporal)
                .save();

        } catch (error) {
            console.error(
                "Error al generar el PDF:",
                error
            );

            window.alert(
                "Ocurrió un error al generar el PDF. Abrí la consola del navegador para ver el detalle."
            );

        } finally {
            if (contenedorTemporal) {
                contenedorTemporal.remove();
            }

            if (boton) {
                boton.disabled = false;
                boton.textContent = textoOriginalBoton;
            }
        }
    }

    window.generarPDF = generarPDF;

})();
