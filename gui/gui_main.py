import tkinter as tk
from tkinter import ttk
from monitor.historico import guardar_medicion
from monitor.reconocimiento import reconocimiento_inicial
from monitor.escenarios_prueba import obtener_escenarios_disponibles, aplicar_escenario
from utils import notificaciones
import traceback

class DiagnosticoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Diagnóstico y Auditoría")
        self.geometry("1100x650")
        self.configure(bg="#f4f4f4")

        self._construir_layout()

        # Registrar callback de notificaciones
        notificaciones.registrar_callback_gui(self._recibir_notificacion)

        # Primer mensaje
        notificaciones.info("Aplicación iniciada. Realizando reconocimiento inicial...")
        self._cargar_datos_iniciales()
        self._ultimo_escenario_id = None

    def _construir_layout(self):
        frame_info = ttk.LabelFrame(self, text="Reconocimiento de sistema")
        frame_info.pack(fill="x", padx=10, pady=5)

        self.lbl_so = ttk.Label(frame_info, text="SO: -")
        self.lbl_so.grid(row=0, column=0, sticky="w", padx=5, pady=2)

        self.lbl_vm = ttk.Label(frame_info, text="Tipo: -")
        self.lbl_vm.grid(row=0, column=1, sticky="w", padx=5, pady=2)

        self.lbl_host = ttk.Label(frame_info, text="Hostname: -")
        self.lbl_host.grid(row=0, column=2, sticky="w", padx=5, pady=2)

        # Fila 1: CPU (modelo y cores)
        self.lbl_cpu_model = ttk.Label(frame_info, text="CPU: -")
        self.lbl_cpu_model.grid(row=1, column=0, sticky="w", padx=5, pady=2)

        self.lbl_cpu_cores = ttk.Label(frame_info, text="Cores/Hilos: -")
        self.lbl_cpu_cores.grid(row=1, column=1, sticky="w", padx=5, pady=2)

        self.lbl_cpu_freq = ttk.Label(frame_info, text="Frecuencia: -")
        self.lbl_cpu_freq.grid(row=1, column=2, sticky="w", padx=5, pady=2)

        # Fila 2: RAM y disco
        self.lbl_ram_total = ttk.Label(frame_info, text="RAM total: -")
        self.lbl_ram_total.grid(row=2, column=0, sticky="w", padx=5, pady=2)

        self.lbl_disco_total = ttk.Label(frame_info, text="Disco total: -")
        self.lbl_disco_total.grid(row=2, column=1, sticky="w", padx=5, pady=2)

        # Opcional: tercera columna vacía o para otro dato
        frame_info.columnconfigure(0, weight=1)
        frame_info.columnconfigure(1, weight=1)
        frame_info.columnconfigure(2, weight=1)

        frame_zbx = ttk.LabelFrame(self, text="Estado desde Zabbix (WIN-LAPTOP)")
        frame_zbx.pack(fill="x", padx=10, pady=5)

        self.lbl_cpu_zbx = ttk.Label(frame_zbx, text="CPU uso: -")
        self.lbl_cpu_zbx.grid(row=0, column=0, sticky="w", padx=5, pady=2)

        self.lbl_ram = ttk.Label(frame_zbx, text="RAM uso: -")
        self.lbl_ram.grid(row=0, column=1, sticky="w", padx=5, pady=2)

        self.lbl_disco = ttk.Label(frame_zbx, text="Disco C: uso: -")
        self.lbl_disco.grid(row=0, column=2, sticky="w", padx=5, pady=2)

        self.lbl_uptime = ttk.Label(frame_zbx, text="Uptime: -")
        self.lbl_uptime.grid(row=1, column=0, sticky="w", padx=5, pady=2)

        self.lbl_swap = ttk.Label(frame_zbx, text="Swap libre: -")
        self.lbl_swap.grid(row=1, column=1, sticky="w", padx=5, pady=2)

        self.lbl_servicios = ttk.Label(frame_zbx, text="Servicios: -")
        self.lbl_servicios.grid(row=1, column=2, sticky="w", padx=5, pady=2)

        self.lbl_estado_global = ttk.Label(frame_zbx, text="Estado global: -")
        self.lbl_estado_global.grid(row=2, column=0, columnspan=3, sticky="w", padx=5, pady=(4, 2))

        self.lbl_red = ttk.Label(frame_zbx, text="Latencia Zabbix: -")
        self.lbl_red.grid(row=2, column=0, sticky="w", padx=5, pady=2)

        self.lbl_resumen = ttk.Label(frame_zbx, text="Resumen histórico: -")
        self.lbl_resumen.grid(row=2, column=1, columnspan=2,
                              sticky="w", padx=5, pady=2)

        self.lbl_netdata = ttk.Label(frame_zbx, text="Netdata: -")
        self.lbl_netdata.grid(row=3, column=0, columnspan=3, sticky="w", padx=5, pady=2)


        for col in range(3):
            frame_zbx.columnconfigure(col, weight=1)

        frame_acciones = ttk.LabelFrame(self, text="Acciones y notificaciones")
        frame_acciones.pack(fill="both", expand=True, padx=10, pady=5)
        frame_botones = ttk.Frame(frame_acciones)
        frame_botones.pack(fill="x", padx=5, pady=5)
        frame_botones = ttk.Frame(frame_acciones)
        frame_botones.pack(fill="x", padx=5, pady=5)

        btn_csv = ttk.Button(frame_botones, text="Exportar CSV", command=self._exportar_csv)
        btn_csv.pack(side="left", padx=5)

        btn_html = ttk.Button(frame_botones, text="Exportar HTML", command=self._exportar_html)
        btn_html.pack(side="left", padx=5)

        btn_refresh = ttk.Button(frame_botones, text="Refrescar diagnóstico", command=self._refrescar)
        btn_refresh.pack(side="left", padx=5)

        # Zona de pruebas
        frame_pruebas = ttk.LabelFrame(frame_acciones, text="Zona de pruebas de alertas")
        frame_pruebas.pack(fill="x", padx=5, pady=5)

        escenarios = obtener_escenarios_disponibles()
        self._mapa_escenarios = {e["nombre"]: e["id"] for e in escenarios}

        ttk.Label(frame_pruebas, text="Escenario:").grid(row=0, column=0, padx=5, pady=2, sticky="w")

        self.cbo_escenario = ttk.Combobox(
            frame_pruebas,
            values=list(self._mapa_escenarios.keys()),
            state="readonly",
            width=40
        )
        self.cbo_escenario.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        btn_probar = ttk.Button(frame_pruebas, text="Probar escenario", command=self._probar_escenario)
        btn_probar.grid(row=0, column=2, padx=5, pady=2)

        self.txt_notif = tk.Text(frame_acciones, height=8, state="disabled")
        self.txt_notif.pack(fill="both", expand=True, padx=5, pady=5)

    def _recibir_notificacion(self, tipo: str, linea: str) -> None:
        """
        Callback registrado en utils.notificaciones.
        Inserta la línea en el Text inferior.
        """
        self.txt_notif.configure(state="normal")

        if tipo == "ERROR":
            tag = "error"
        elif tipo == "WARN":
            tag = "warn"
        else:
            tag = "info"

        self.txt_notif.insert("end", linea + "\n", tag)
        self.txt_notif.see("end")
        self.txt_notif.configure(state="disabled")

        # Estilos básicos por tipo
        self.txt_notif.tag_config("info", foreground="black")
        self.txt_notif.tag_config("warn", foreground="orange")
        self.txt_notif.tag_config("error", foreground="red")

    def _cargar_datos_iniciales(self):
        try:
            datos = reconocimiento_inicial()
            guardar_medicion(datos)
            info = datos["sistema_local"]
            zbx = datos["zabbix"]
            recs = datos.get("recomendaciones", [])
            estado = datos.get("estado_global", "OK")
            motivos = datos.get("motivos_estado", [])

            texto_estado = f"Estado global: {estado}"
            self.lbl_estado_global.config(text=texto_estado)

            netdata = datos.get("netdata", {})
            if netdata and any(v is not None for v in netdata.values()):
                partes = []
                if netdata.get("cpu_avg_60s") is not None:
                    partes.append(f"CPU VM (Netdata, 60s): {netdata['cpu_avg_60s']:.1f} %")
                if netdata.get("load_avg_1m") is not None:
                    partes.append(f"Load 1m: {netdata['load_avg_1m']:.2f}")
                if netdata.get("ram_uso_pct") is not None:
                    partes.append(f"RAM VM (Netdata, 60s): {netdata['ram_uso_pct']:.1f} %")
                self.lbl_netdata.config(text=" | ".join(partes))
            else:
                self.lbl_netdata.config(text="Netdata: sin datos o deshabilitado")

            if motivos:
                for m in motivos:
                    if estado == "CRÍTICO":
                        notificaciones.error(m)
                    elif estado == "ADVERTENCIA":
                        notificaciones.advertencia(m)
                    else:
                        notificaciones.info(m)

            self.lbl_so.config(text=f"SO: {info['so']} {info['release']}")
            tipo = "Máquina virtual" if info.get("es_vm") else "Sistema físico"
            self.lbl_vm.config(text=f"Tipo: {tipo}")
            self.lbl_host.config(text=f"Hostname: {info['hostname']}")

            # CPU / RAM / Disco
            cpu_model = info.get("cpu_modelo", "-")
            cores_log = info.get("cpu_cores_logicos", "-")
            cores_fis = info.get("cpu_cores_fisicos", "-")
            freq_anun = info.get("cpu_freq_anunciada", "")
            ghz_actual = info.get("cpu_freq_actual_ghz")

            # Modelo
            self.lbl_cpu_model.config(text=f"CPU: {cpu_model}")

            # Núcleos / hilos
            self.lbl_cpu_cores.config(
                text=f"Cores/Hilos: {cores_fis} núcleos / {cores_log} hilos"
            )

            # Frecuencias
            if ghz_actual:
                texto_freq = f"Base: {freq_anun} | Actual: ~{ghz_actual:.2f} GHz"
            else:
                texto_freq = f"Base: {freq_anun}"
            self.lbl_cpu_freq.config(text=f"Frecuencia: {texto_freq}")

            # RAM y disco como antes
            ram_total_gb = info.get("ram_total_gb")
            if ram_total_gb is not None:
                self.lbl_ram_total.config(text=f"RAM total: {ram_total_gb:.2f} GB")

            disco_total_bytes = info.get("disco_total_bytes")
            if disco_total_bytes:
                disco_total_gb = disco_total_bytes / (1024 ** 3)
                self.lbl_disco_total.config(
                    text=f"Disco total: {disco_total_gb:.2f} GB"
                )

            cpu = zbx.get("cpu_uso_pct")
            ram = zbx.get("ram_uso_pct")
            disco = zbx.get("disco_c_uso_pct")

            # Uptime
            up = zbx.get("uptime_seg")
            if up is not None:
                horas = up / 3600
                self.lbl_uptime.config(text=f"Uptime: {horas:.1f} h")
            else:
                notificaciones.advertencia("No se pudo obtener uptime desde Zabbix.")

            # Swap
            swap_pfree = zbx.get("swap_pfree_pct")
            if swap_pfree is not None:
                self.lbl_swap.config(text=f"Swap libre: {swap_pfree:.1f} %")
            else:
                notificaciones.advertencia("No se pudo obtener swap desde Zabbix.")

            # Servicios críticos
            servicios = zbx.get("servicios", {})
            if servicios:
                estados = []
                for nombre, estado in servicios.items():
                    # Mapear estado numérico a texto legible
                    if estado == 0:
                        txt = "DETENIDO"
                    elif estado == 1:
                        txt = "EN EJECUCIÓN"
                    else:
                        txt = f"ESTADO={estado}"
                    estados.append(f"{nombre}: {txt}")
                self.lbl_servicios.config(text=" / ".join(estados))
            else:
                self.lbl_servicios.config(text="Servicios: (sin datos)")

            if cpu is not None:
                self.lbl_cpu_zbx.config(text=f"CPU uso: {cpu:.1f} %")
            else:
                notificaciones.advertencia("No se pudo obtener CPU desde Zabbix.")

            if ram is not None:
                self.lbl_ram.config(text=f"RAM uso: {ram:.1f} %")
            else:
                notificaciones.advertencia("No se pudo obtener RAM desde Zabbix.")

            if disco is not None:
                self.lbl_disco.config(text=f"Disco C: uso: {disco:.1f} %")
            else:
                notificaciones.advertencia("No se pudo obtener disco C: desde Zabbix.")

            # Red
            info_red = datos.get("red", {})
            lat = info_red.get("latencia_zabbix_ms")
            if lat is not None:
                self.lbl_red.config(text=f"Latencia Zabbix: {lat:.1f} ms")
            else:
                self.lbl_red.config(text="Latencia Zabbix: sin respuesta")

            # Resumen histórico
            resumen = datos.get("resumen", {})
            if resumen and resumen.get("muestras"):
                txt_res = (
                    f"Histórico ({int(resumen['muestras'])} muestras): "
                    f"CPU prom {resumen['cpu_prom']:.1f} %, "
                    f"RAM prom {resumen['ram_prom']:.1f} %, "
                    f"Disco C prom {resumen['disco_prom']:.1f} %"
                )
                self.lbl_resumen.config(text=txt_res)
            else:
                self.lbl_resumen.config(text="Resumen histórico: sin datos")

            for r in recs:
                notificaciones.advertencia(r)

            notificaciones.info("Reconocimiento inicial completado correctamente.")
        except Exception as e:
            traceback.print_exc()
            notificaciones.error(f"Error en reconocimiento inicial: {e}")
    
    def _exportar_csv(self):
        from utils.exportar import exportar_diagnostico_csv
        try:
            # 1) Obtener diagnóstico base (real)
            datos = reconocimiento_inicial()

            # 2) Si hay un escenario de prueba seleccionado, añadir alertas/recomendaciones simuladas
            if self._ultimo_escenario_id:
                esc = aplicar_escenario(self._ultimo_escenario_id)
                datos["alertas_simuladas"] = esc["alertas"]
                datos.setdefault("recomendaciones", []).extend(esc["recomendaciones"])

            # 3) Exportar
            ruta = exportar_diagnostico_csv(datos)
            notificaciones.info(f"CSV exportado: {ruta}")
        except Exception as e:
            notificaciones.error(f"Error exportando CSV: {e}")


    def _exportar_html(self):
        from utils.exportar import exportar_diagnostico_html
        try:
            datos = reconocimiento_inicial()

            if self._ultimo_escenario_id:
                esc = aplicar_escenario(self._ultimo_escenario_id)
                datos["alertas_simuladas"] = esc["alertas"]
                datos.setdefault("recomendaciones", []).extend(esc["recomendaciones"])

            ruta = exportar_diagnostico_html(datos)
            notificaciones.info(f"HTML exportado: {ruta}")
        except Exception as e:
            notificaciones.error(f"Error exportando HTML: {e}")


    def _refrescar(self):
        notificaciones.info("Refrescando diagnóstico...")
        self._cargar_datos_iniciales()
    
    def _probar_escenario(self):
        nombre = self.cbo_escenario.get()
        if not nombre:
            notificaciones.advertencia("Seleccione un escenario de prueba.")
            return

        escenario_id = self._mapa_escenarios.get(nombre)
        self._ultimo_escenario_id = escenario_id  # guardar para exportar luego

        datos = aplicar_escenario(escenario_id)

        for a in datos["alertas"]:
            notificaciones.advertencia(f"[PRUEBA] {a}")
        for r in datos["recomendaciones"]:
            notificaciones.info(f"[PRUEBA] Recomendación: {r}")

def lanzar_gui():
    app = DiagnosticoApp()
    app.mainloop()
