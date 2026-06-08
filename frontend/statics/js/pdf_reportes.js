```javascript
/*
 * Genera archivos PDF a partir de las secciones
 * HTML ya cargadas en la dashboard.
 */

(function () {
    "use strict";

    /*
     * Espera dos ciclos de renderizado para asegurarse
     * de que el navegador haya aplicado los estilos.
     */
    function esperarRenderizado() {
        return new Promise(function (resolve) {
            window.requestAnimationFrame(function () {
                window.requestAnimationFrame(resolve);
            });
        });
    }

    /*
     * Crea el encabezado que aparecerá únicamente
     * dentro del archivo PDF.
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
     * Crea una copia de la sección que se quiere descargar.
     *
     * Se utiliza una copia para no modificar la dashboard
     * original mientras se genera el PDF.
     */
    function crearContenedorTemporal(
        seccionOriginal,
        tituloReporte
    ) {
        const copia = seccionOriginal.cloneNode(true);

        /*
         * Evita que existan dos elementos con el mismo ID.
         */
        copia.removeAttribute("id");

        /*
         * La sección puede estar oculta por pertenecer
         * a una pestaña que no está activa.
         */
        copia.classList.remove("active");
        copia.style.display = "block";

        /*
         * Elimina los botones de descarga de la copia
         * para que no aparezcan dentro del PDF.
         */
        copia
            .querySelectorAll(
                '[data-html2canvas-ignore="true"]'
            )
            .forEach(function (elemento) {
                elemento.remove();
            });

        /*
         * Crea un contenedor fuera de la pantalla.
         */
        const contenedor = document.createElement("div");

        contenedor.className =
            "pdf-contenedor-temporal pdf-exportando";

        contenedor.appendChild(
            crearEncabezado(tituloReporte)
        );

        contenedor.appendChild(copia);

        document.body.appendChild(contenedor);

        return contenedor;
    }

    /*
     * Función principal llamada desde los botones
     * de dashboard.html.
     */
    async function generarPDF(
        idSeccion,
        nombreArchivo,
        tituloReporte,
        boton
    ) {
        const seccionOriginal =
            document.getElementById(idSeccion);

        /*
         * Verifica que la sección exista.
         */
        if (!seccionOriginal) {
            window.alert(
                "No se encontró la sección que se quiere exportar."
            );

            return;
        }

        /*
         * Verifica que html2pdf.js se haya cargado.
         */
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

        const textoOriginalBoton =
            boton ? boton.textContent : "";

        /*
         * Desactiva el botón mientras se crea el PDF.
         */
        if (boton) {
            boton.disabled = true;
            boton.textContent = "Generando PDF...";
        }

        try {
            /*
             * Espera a que las fuentes terminen de cargar.
             */
            if (
                document.fonts &&
                document.fonts.ready
            ) {
                await document.fonts.ready;
            }

            /*
             * Crea la copia temporal del HTML.
             */
            contenedorTemporal =
                crearContenedorTemporal(
                    seccionOriginal,
                    tituloReporte
                );

            await esperarRenderizado();

            /*
             * Configuración del archivo PDF.
             */
            const opciones = {
                margin: [8, 8, 8, 8],

                filename: nombreArchivo,

                image: {
                    type: "jpeg",
                    quality: 0.98
                },

                html2canvas: {
                    scale: 2,
                    useCORS: true,
                    backgroundColor: "#ffffff",
                    scrollX: 0,
                    scrollY: 0
                },

                jsPDF: {
                    unit: "mm",
                    format: "a4",
                    orientation: "portrait"
                },

                pagebreak: {
                    mode: [
                        "avoid-all",
                        "css",
                        "legacy"
                    ],

                    avoid: [
                        ".kpi-card",
                        ".panel-card",
                        ".barbero-card-full",
                        ".servicio-card",
                        ".cita-row",
                        ".barbero-row",
                        ".servicio-row"
                    ]
                }
            };

            /*
             * Convierte el HTML en PDF
             * y descarga el archivo.
             */
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
                "Ocurrió un error al generar el PDF."
            );

        } finally {
            /*
             * Elimina la copia temporal.
             */
            if (contenedorTemporal) {
                contenedorTemporal.remove();
            }

            /*
             * Vuelve a habilitar el botón.
             */
            if (boton) {
                boton.disabled = false;
                boton.textContent = textoOriginalBoton;
            }
        }
    }

    /*
     * Hace que la función pueda ser utilizada
     * desde los onclick de dashboard.html.
     */
    window.generarPDF = generarPDF;

})();
```
