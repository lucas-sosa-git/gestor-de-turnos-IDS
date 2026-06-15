/*
 * Generación de reportes PDF del panel administrativo.
 *
 * Esta versión no utiliza html2pdf.js para construir el archivo.
 * Primero captura la sección con html2canvas y después arma cada
 * página con jsPDF. De esta manera se evita el problema de los
 * archivos que se descargaban correctamente pero quedaban blancos.
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

    function esperarRenderizado() {
        return new Promise(function (resolve) {
            window.requestAnimationFrame(function () {
                window.requestAnimationFrame(function () {
                    window.setTimeout(resolve, 150);
                });
            });
        });
    }

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

    function limpiarCopia(copia) {
        SELECTORES_EXCLUIDOS.forEach(function (selector) {
            copia
                .querySelectorAll(selector)
                .forEach(function (elemento) {
                    elemento.remove();
                });
        });

        /*
         * Evita IDs duplicados mientras existe la copia temporal.
         * Los IDs no son necesarios para dibujar el reporte.
         */
        copia
            .querySelectorAll("[id]")
            .forEach(function (elemento) {
                elemento.removeAttribute("id");
            });
    }

    function crearContenedorTemporal(
        seccionOriginal,
        tituloReporte
    ) {
        const copia = seccionOriginal.cloneNode(true);

        copia.removeAttribute("id");
        hacerVisible(copia);
        limpiarCopia(copia);

        const contenedor = document.createElement("div");
        contenedor.className =
            "pdf-contenedor-temporal pdf-exportando";

        contenedor.appendChild(
            crearEncabezado(tituloReporte)
        );

        contenedor.appendChild(copia);

        document.body.classList.add("pdf-modo-captura");
        document.body.appendChild(contenedor);

        return contenedor;
    }

    function validarDimensiones(elemento) {
        const ancho = Math.ceil(
            Math.max(
                elemento.offsetWidth,
                elemento.scrollWidth
            )
        );

        const alto = Math.ceil(
            Math.max(
                elemento.offsetHeight,
                elemento.scrollHeight
            )
        );

        if (ancho <= 0 || alto <= 0) {
            throw new Error(
                "La sección a exportar no tiene dimensiones visibles."
            );
        }

        return {
            ancho: ancho,
            alto: alto
        };
    }

    function calcularEscala(ancho, alto) {
        /*
         * Evita superar los límites máximos del canvas del
         * navegador cuando un reporte tiene mucho contenido.
         */
        const dimensionMaxima = 14000;
        const escalaPorAncho = dimensionMaxima / ancho;
        const escalaPorAlto = dimensionMaxima / alto;

        return Math.max(
            1,
            Math.min(
                1.5,
                escalaPorAncho,
                escalaPorAlto
            )
        );
    }

    function canvasTieneContenido(canvas) {
        const contexto = canvas.getContext(
            "2d",
            {
                willReadFrequently: true
            }
        );

        if (!contexto) {
            return false;
        }

        const ancho = canvas.width;
        const alto = canvas.height;
        const pasoX = Math.max(1, Math.floor(ancho / 40));
        const pasoY = Math.max(1, Math.floor(alto / 40));

        for (let y = 0; y < alto; y += pasoY) {
            for (let x = 0; x < ancho; x += pasoX) {
                const pixel = contexto.getImageData(
                    x,
                    y,
                    1,
                    1
                ).data;

                const esBlanco =
                    pixel[0] > 248 &&
                    pixel[1] > 248 &&
                    pixel[2] > 248;

                const esTransparente = pixel[3] === 0;

                if (!esBlanco && !esTransparente) {
                    return true;
                }
            }
        }

        return false;
    }

    function agregarCanvasAlPDF(canvas, nombreArchivo) {
        const jsPDF = window.jspdf.jsPDF;

        const pdf = new jsPDF({
            orientation: "portrait",
            unit: "mm",
            format: "a4",
            compress: true
        });

        const margen = 8;
        const anchoPagina =
            pdf.internal.pageSize.getWidth();

        const altoPagina =
            pdf.internal.pageSize.getHeight();

        const anchoUtil = anchoPagina - margen * 2;
        const altoUtil = altoPagina - margen * 2;

        /*
         * Cantidad de píxeles del canvas que entran en una
         * página A4 manteniendo la proporción.
         */
        const altoPaginaEnPixeles = Math.max(
            1,
            Math.floor(
                canvas.width *
                (altoUtil / anchoUtil)
            )
        );

        let posicionY = 0;
        let numeroPagina = 0;

        while (posicionY < canvas.height) {
            const altoFragmento = Math.min(
                altoPaginaEnPixeles,
                canvas.height - posicionY
            );

            const paginaCanvas =
                document.createElement("canvas");

            paginaCanvas.width = canvas.width;
            paginaCanvas.height = altoFragmento;

            const contexto =
                paginaCanvas.getContext("2d");

            contexto.fillStyle = "#ffffff";
            contexto.fillRect(
                0,
                0,
                paginaCanvas.width,
                paginaCanvas.height
            );

            contexto.drawImage(
                canvas,
                0,
                posicionY,
                canvas.width,
                altoFragmento,
                0,
                0,
                canvas.width,
                altoFragmento
            );

            if (numeroPagina > 0) {
                pdf.addPage();
            }

            const imagen = paginaCanvas.toDataURL(
                "image/jpeg",
                0.95
            );

            const altoImagen =
                altoFragmento *
                (anchoUtil / canvas.width);

            pdf.addImage(
                imagen,
                "JPEG",
                margen,
                margen,
                anchoUtil,
                altoImagen,
                undefined,
                "FAST"
            );

            posicionY += altoFragmento;
            numeroPagina += 1;
        }

        pdf.save(nombreArchivo);
    }

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

        if (typeof window.html2canvas !== "function") {
            window.alert(
                "No se cargó html2canvas. Revisá tu conexión a internet y recargá la página."
            );

            return;
        }

        if (
            !window.jspdf ||
            typeof window.jspdf.jsPDF !== "function"
        ) {
            window.alert(
                "No se cargó jsPDF. Revisá tu conexión a internet y recargá la página."
            );

            return;
        }

        let contenedorTemporal = null;

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

            contenedorTemporal =
                crearContenedorTemporal(
                    seccionOriginal,
                    tituloReporte
                );

            await esperarImagenes(contenedorTemporal);
            await esperarRenderizado();

            const dimensiones =
                validarDimensiones(
                    contenedorTemporal
                );

            const escala = calcularEscala(
                dimensiones.ancho,
                dimensiones.alto
            );

            const canvas = await window.html2canvas(
                contenedorTemporal,
                {
                    scale: escala,
                    useCORS: true,
                    allowTaint: false,
                    backgroundColor: "#ffffff",
                    scrollX: 0,
                    scrollY: 0,
                    logging: false,
                    width: dimensiones.ancho,
                    height: dimensiones.alto,
                    windowWidth: dimensiones.ancho,
                    windowHeight: dimensiones.alto,
                    foreignObjectRendering: false,
                    removeContainer: true,

                    onclone: function (documentoClonado) {
                        const contenedorClonado =
                            documentoClonado.querySelector(
                                ".pdf-contenedor-temporal"
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
                }
            );

            if (
                canvas.width <= 0 ||
                canvas.height <= 0 ||
                !canvasTieneContenido(canvas)
            ) {
                throw new Error(
                    "html2canvas generó una imagen vacía."
                );
            }

            agregarCanvasAlPDF(
                canvas,
                nombreArchivo
            );

        } catch (error) {
            console.error(
                "Error al generar el PDF:",
                error
            );

            window.alert(
                "No se pudo generar el PDF. Abrí la consola del navegador para ver el error."
            );

        } finally {
            if (contenedorTemporal) {
                contenedorTemporal.remove();
            }

            document.body.classList.remove(
                "pdf-modo-captura"
            );

            if (boton) {
                boton.disabled = false;
                boton.textContent = textoOriginalBoton;
            }
        }
    }

    window.generarPDF = generarPDF;

})();
