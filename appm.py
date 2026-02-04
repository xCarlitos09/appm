import flet as ft
import pandas as pd
import io

# ==========================================
# 1. LÓGICA DEL NEGOCIO (TU MOTOR MATEMÁTICO)
# ==========================================

DEFAULT_REGLAS = {
    '1P': [(1, 1.0)],
    '1Y2N': [(1, 1.0), (2, -0.5)], 
    '2N': [(1, 1.0), (2, 0.0)],    
    '2Y2N': [(1, 1.0), (2, 0.5)],    
    '2P': [(1, 1.0), (2, 1.0)],
    '2Y3N': [(1, 1.0), (2, 1.0), (3, -0.5)], 
    '3N': [(1, 1.0), (2, 1.0), (3, 0.0)],
    '3Y3N': [(1, 1.0), (2, 1.0), (3, 0.5)],
    '3P': [(1, 1.0), (2, 1.0), (3, 1.0)],
    '3Y4N': [(1, 1.0), (2, 1.0), (3, 1.0), (4, -0.5)], 
    '4N': [(1, 1.0), (2, 1.0), (3, 1.0), (4, 0.0)],
    '4Y4N': [(1, 1.0), (2, 1.0), (3, 1.0), (4, 0.5)],
    '4P': [(1, 1.0), (2, 1.0), (3, 1.0), (4, 1.0)],
    '4Y5N': [(1, 1.0), (2, 1.0), (3, 1.0), (4, 1.0), (5, -0.5)], 
    '5N': [(1, 1.0), (2, 1.0), (3, 1.0), (4, 1.0), (5, 0.0)],
    '5Y5N': [(1, 1.0), (2, 1.0), (3, 1.0), (4, 1.0), (5, 0.5)],
    '5P': [(1, 1.0), (2, 1.0), (3, 1.0), (4, 1.0), (5, 1.0)],
}

def normalizar_tipo_apuesta(tipo_input):
    t = tipo_input.upper().strip()
    alias = {
        '1Y2': '1Y2N', '2Y2': '2Y2N', '2Y3': '2Y3N', '3Y3': '3Y3N', '3Y4': '3Y4N',
        'A9': '1P' 
    }
    return alias.get(t, t)

def obtener_posicion(caballo_num, lista_llegada):
    try:
        return lista_llegada.index(int(caballo_num)) + 1
    except (ValueError, TypeError):
        return 99

def mejor_posicion_grupo(lista_caballos_str, lista_llegada):
    if not lista_caballos_str or pd.isna(lista_caballos_str): return 99
    numeros = []
    partes = str(lista_caballos_str).replace(',', ' ').replace('X', ' ').replace('x', ' ').split()
    for x in partes:
        if x.isdigit():
            numeros.append(int(x))
    if not numeros: return 99
    
    mejores = [obtener_posicion(n, lista_llegada) for n in numeros]
    if not mejores: return 99
    return min(mejores)

def calcular_factor_cxc(caballos_t1, caballos_t2, llegada, cuota_g, cuota_a):
    pos_t1 = mejor_posicion_grupo(caballos_t1, llegada)
    pos_t2 = mejor_posicion_grupo(caballos_t2, llegada)
    
    if pos_t1 == 99 and pos_t2 == 99: return 0.0 
    if pos_t1 == pos_t2: return 0.0 
    if pos_t1 < pos_t2: return cuota_g / cuota_a 
    else: return -1.0 

def calcular_factor_posicional(caballos_t1, llegada, tipo_regla):
    # Usamos las reglas globales por defecto para simplificar la versión móvil
    pos_real = mejor_posicion_grupo(caballos_t1, llegada)
    if pos_real == 99: return -1.0 
    
    reglas = DEFAULT_REGLAS.get(tipo_regla, [])
    for puesto, factor in reglas:
        if puesto == pos_real: return factor
    return -1.0 

def procesar_texto(texto, id_carrera):
    data = []
    lines = [l.strip() for l in texto.split('\n') if l.strip()]
    
    for linea in lines:
        try:
            linea_clean = linea.upper().replace(',', ' ')
            partes = linea_clean.split()
            if len(partes) < 4: continue
            
            t1 = partes[0]
            monto_str = partes[-1].replace('K', '000')
            try:
                monto = float(monto_str)
                t2 = partes[-2]
                medio = partes[1:-2]
            except:
                continue
                
            tipo_apuesta = []
            c1_list = []
            c2_list = []
            cuota_gana = 10.0
            
            # 1. Buscar Cuotas
            indices_a_ignorar = []
            for i, item in enumerate(medio):
                if item.startswith('A') and len(item) > 1 and item[1:].replace('.','',1).isdigit():
                    cuota_gana = float(item[1:])
                    tipo_apuesta.append('CUOTAS')
                    indices_a_ignorar.append(i)
            
            medio_limpio = [item for i, item in enumerate(medio) if i not in indices_a_ignorar]
            
            # 2. Buscar CxC
            cxc_str = ""
            for item in medio_limpio:
                if 'X' in item:
                    cxc_str = item
                    tipo_apuesta.append('CXC')
                    break
            
            if cxc_str:
                if 'CUOTAS' in tipo_apuesta:
                    try: tipo_apuesta.remove('CUOTAS') 
                    except: pass
                nums = cxc_str.split('X')
                c1_list.append(nums[0])
                c2_list.append(nums[1])
            else:
                for item in medio_limpio:
                    norm = normalizar_tipo_apuesta(item)
                    if norm in DEFAULT_REGLAS:
                        tipo_apuesta.append(norm)
                    elif item.isdigit():
                        c1_list.append(item)
            
            c1 = ",".join(c1_list)
            c2 = ",".join(c2_list)
            
            if c1:
                data.append({
                    'ID_Carrera': id_carrera, 'T1': t1, 'T2': t2, 'Monto': monto,
                    'Cuota_Gana': cuota_gana, 'Cuota_Arriesga': 10.0,
                    'Tipo_Apuesta': tipo_apuesta,
                    'Caballos_T1': c1, 'Caballos_T2': c2,
                    'Calculado': 'No', 'Mejor_Factor': 0.0, 'Utilidad_T1': 0.0, 'Utilidad_T2': 0.0, 'Saldo_Neto': 0.0
                })
        except:
            pass
    return data

# ==========================================
# 2. INTERFAZ GRÁFICA FLET (MOBILE UI)
# ==========================================

def main(page: ft.Page):
    page.title = "Banca P2P Pro Móvil"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = "adaptive"
    page.bgcolor = ft.Colors.GREY_100
    
    # --- ESTADO GLOBAL ---
    state = {
        "registro": pd.DataFrame(columns=[
            'ID_Carrera', 'T1', 'T2', 'Monto', 'Cuota_Gana', 'Cuota_Arriesga', 'Tipo_Apuesta', 
            'Caballos_T1', 'Caballos_T2', 'Calculado', 'Mejor_Factor', 'Utilidad_T1', 'Utilidad_T2', 'Saldo_Neto'
        ]),
        "comision_total": 0.0
    }

    # --- COMPONENTES UI ---
    
    # Componentes TAB 1: Carga
    txt_id_carrera = ft.TextField(label="ID Carrera", width=150, keyboard_type=ft.KeyboardType.NUMBER, border_color="blue")
    txt_input_apuestas = ft.TextField(
        label="Pegar Apuestas Aquí", 
        multiline=True, 
        min_lines=6, 
        max_lines=8, 
        text_size=12,
        hint_text="Ej: JUAN 1P 5 PEDRO 10"
    )
    
    # Componentes TAB 2: Cálculo
    dd_carreras = ft.Dropdown(label="Seleccionar Carrera", options=[])
    txt_pizarra = ft.TextField(label="Pizarra (Ej: 1-5-9)", keyboard_type=ft.KeyboardType.PHONE, prefix_icon=ft.Icons.FLAG)
    txt_comision = ft.TextField(label="Comisión %", value="5", width=100, keyboard_type=ft.KeyboardType.NUMBER, text_align=ft.TextAlign.RIGHT)
    
    # Componentes TAB 3: Resultados
    txt_resumen_whatsapp = ft.TextField(label="Para WhatsApp", multiline=True, read_only=True, min_lines=5)
    tabla_saldos = ft.DataTable(
        columns=[ft.DataColumn(ft.Text("Jugador")), ft.DataColumn(ft.Text("Saldo"), numeric=True)],
        rows=[]
    )
    
    # --- FUNCIONES DE EVENTOS ---

    def refrescar_carreras():
        if not state["registro"].empty:
            uniques = state["registro"]['ID_Carrera'].unique()
            dd_carreras.options = [ft.dropdown.Option(str(c)) for c in uniques]
            if not dd_carreras.value and len(uniques) > 0:
                dd_carreras.value = str(uniques[-1]) # Seleccionar el último por defecto
            page.update()

    def btn_cargar_click(e):
        if not txt_id_carrera.value:
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ Faltan el ID de Carrera"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return

        nuevos = procesar_texto(txt_input_apuestas.value, txt_id_carrera.value)
        if nuevos:
            df_new = pd.DataFrame(nuevos)
            state["registro"] = pd.concat([state["registro"], df_new], ignore_index=True)
            
            page.snack_bar = ft.SnackBar(ft.Text(f"✅ {len(nuevos)} apuestas cargadas correctamente"), bgcolor="green")
            page.snack_bar.open = True
            
            txt_input_apuestas.value = "" # Limpiar
            refrescar_carreras()
        else:
            page.snack_bar = ft.SnackBar(ft.Text("❌ No se detectaron apuestas válidas"), bgcolor="red")
            page.snack_bar.open = True
        page.update()

    def btn_calcular_click(e):
        carrera_calc = dd_carreras.value
        pizarra_raw = txt_pizarra.value
        
        if not carrera_calc or not pizarra_raw:
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ Selecciona carrera e ingresa pizarra"), bgcolor="orange")
            page.snack_bar.open = True
            page.update()
            return
            
        try:
            llegada = [int(x) for x in pizarra_raw.replace(',', ' ').replace('-', ' ').split() if x.isdigit()]
            comision_val = float(txt_comision.value)
            comision_dec = comision_val / 100
            
            mask = state["registro"]['ID_Carrera'] == carrera_calc
            indices = state["registro"][mask].index
            
            # --- LÓGICA DE CÁLCULO ---
            for i in indices:
                row = state["registro"].loc[i]
                tipos = row['Tipo_Apuesta']
                monto_total = row['Monto']
                cantidad_reglas = len(tipos)
                monto_por_regla = monto_total / cantidad_reglas if cantidad_reglas > 0 else 0
                
                utilidad_acumulada_bruta = 0.0
                factor_mostrado = 0.0
                
                for tipo in tipos:
                    f = 0.0
                    if tipo == 'CXC':
                        f = calcular_factor_cxc(row['Caballos_T1'], row['Caballos_T2'], llegada, row['Cuota_Gana'], row['Cuota_Arriesga'])
                    elif tipo == 'CUOTAS':
                         pos = mejor_posicion_grupo(row['Caballos_T1'], llegada)
                         if pos == 1: f = row['Cuota_Gana'] / row['Cuota_Arriesga']
                         else: f = -1.0
                    elif tipo in DEFAULT_REGLAS:
                         f = calcular_factor_posicional(row['Caballos_T1'], llegada, tipo)
                    
                    if abs(f) > abs(factor_mostrado): factor_mostrado = f
                    if f > 0: utilidad_acumulada_bruta += (monto_por_regla * f)
                    elif f < 0: utilidad_acumulada_bruta -= (monto_por_regla * abs(f))
                
                ut1, ut2, com = 0.0, 0.0, 0.0
                if utilidad_acumulada_bruta > 0: 
                    com = utilidad_acumulada_bruta * comision_dec
                    ut1 = utilidad_acumulada_bruta - com
                    ut2 = -utilidad_acumulada_bruta
                elif utilidad_acumulada_bruta < 0:
                    ganancia_t2 = abs(utilidad_acumulada_bruta)
                    com = ganancia_t2 * comision_dec
                    ut1 = -ganancia_t2
                    ut2 = ganancia_t2 - com
                
                # Actualizar DF Global
                state["registro"].at[i, 'Utilidad_T1'] = ut1
                state["registro"].at[i, 'Utilidad_T2'] = ut2
                state["registro"].at[i, 'Saldo_Neto'] = ut1 + ut2
                state["registro"].at[i, 'Calculado'] = 'Sí'
                state["registro"].at[i, 'Mejor_Factor'] = factor_mostrado

            # --- GENERAR TEXTO WHATSAPP ---
            df_calc = state["registro"][state["registro"]['Calculado'] == 'Sí']
            df_carrera = df_calc[df_calc['ID_Carrera'] == carrera_calc]
            
            txt_out = f"*🏇🏻 GRUPO TREBOL 🇻🇪*\n*CARRERA {carrera_calc}*\n\n"
            
            # Detalle jugadas
            for _, r in df_carrera.iterrows():
                if r['Saldo_Neto'] == 0: continue
                linea = f"{r['T1']} "
                # Simplificación visual para móvil
                tipos_clean = [t for t in r['Tipo_Apuesta'] if t not in ['CXC', 'CUOTAS']]
                if tipos_clean: linea += f"{' '.join(tipos_clean)} "
                linea += f"{r['Caballos_T1']} "
                if 'CXC' in r['Tipo_Apuesta']: linea += f"X {r['Caballos_T2']} "
                linea += f"{r['T2']} {int(r['Monto'])}"
                txt_out += f"{linea}\n"
            
            txt_out += f"\nLlegada: {txt_pizarra.value}\n\n"
            
            # Saldos
            t1 = df_calc[['T1', 'Utilidad_T1']].rename(columns={'T1': 'Jugador', 'Utilidad_T1': 'Saldo'})
            t2 = df_calc[['T2', 'Utilidad_T2']].rename(columns={'T2': 'Jugador', 'Utilidad_T2': 'Saldo'})
            total = pd.concat([t1, t2])
            saldos = total.groupby('Jugador')['Saldo'].sum().reset_index()
            saldos = saldos[(saldos['Jugador'] != 'BANCA') & (saldos['Saldo'].abs() > 0.01)]
            saldos = saldos.sort_values(by='Saldo', ascending=False)

            filas_tabla = []
            for _, s in saldos.iterrows():
                val = float(s['Saldo'])
                signo = "+" if val > 0 else ""
                txt_out += f"{s['Jugador']} {signo}{val:.2f}\n"
                
                # Llenar tabla UI
                color_num = "green" if val > 0 else "red"
                filas_tabla.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(s['Jugador'], weight="bold")),
                    ft.DataCell(ft.Text(f"{val:,.2f}", color=color_num, weight="bold")),
                ]))

            txt_resumen_whatsapp.value = txt_out
            tabla_saldos.rows = filas_tabla
            
            # Ir a pestaña resultados y notificar
            page.snack_bar = ft.SnackBar(ft.Text("✅ Cálculo Exitoso. Revisa Resultados."), bgcolor="green")
            page.snack_bar.open = True
            tabs.selected_index = 2 # Cambiar a tab resultados automáticamente
            
            page.update()
            
        except Exception as ex:
             page.snack_bar = ft.SnackBar(ft.Text(f"❌ Error en cálculo: {ex}"), bgcolor="red")
             page.snack_bar.open = True
             page.update()

    def btn_copiar_click(e):
        page.set_clipboard(txt_resumen_whatsapp.value)
        page.snack_bar = ft.SnackBar(ft.Text("📋 Copiado al portapapeles"))
        page.snack_bar.open = True
        page.update()
        
    def btn_reset_click(e):
        state["registro"] = pd.DataFrame(columns=state["registro"].columns)
        state["comision_total"] = 0.0
        tabla_saldos.rows = []
        txt_resumen_whatsapp.value = ""
        txt_input_apuestas.value = ""
        refrescar_carreras()
        page.snack_bar = ft.SnackBar(ft.Text("🧹 Todo borrado para nueva jornada"))
        page.snack_bar.open = True
        page.update()

    # --- DISEÑO DE PESTAÑAS ---
    
    # Botón acción principal
    btn_calcular = ft.ElevatedButton(
        "CALCULAR RESULTADOS", 
        on_click=btn_calcular_click, 
        icon=ft.Icons.CALCULATE, 
        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE, padding=15)
    )

    tab_carga = ft.Container(
        content=ft.Column([
            ft.Text("Registrar Apuestas", size=20, weight="bold", color="blue"),
            ft.Row([txt_id_carrera, ft.IconButton(icon=ft.Icons.DELETE_SWEEP, on_click=lambda e: setattr(txt_input_apuestas, 'value', '') or page.update())]),
            txt_input_apuestas,
            ft.ElevatedButton("CARGAR A SISTEMA", on_click=btn_cargar_click, icon=ft.Icons.SAVE, width=200, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color="white")),
        ], scroll=True),
        padding=15
    )

    tab_calculo = ft.Container(
        content=ft.Column([
            ft.Text("Panel de Carrera", size=20, weight="bold", color="blue"),
            ft.ElevatedButton("Refrescar Carreras", on_click=lambda e: refrescar_carreras(), icon=ft.Icons.REFRESH),
            dd_carreras,
            ft.Divider(),
            txt_pizarra,
            txt_comision,
            ft.Divider(),
            ft.Container(btn_calcular, alignment=ft.alignment.center),
        ], scroll=True),
        padding=15
    )

    tab_resultados = ft.Container(
        content=ft.Column([
            ft.Row([ft.Text("Resumen WhatsApp", weight="bold"), ft.IconButton(icon=ft.Icons.COPY, on_click=btn_copiar_click, icon_color="blue", tooltip="Copiar")]),
            txt_resumen_whatsapp,
            ft.Divider(),
            ft.Text("Saldos Globales", weight="bold"),
            tabla_saldos,
            ft.Container(height=50), # Espacio final
            ft.OutlinedButton("BORRAR TODO EL DÍA", on_click=btn_reset_click, icon=ft.Icons.DELETE_FOREVER, style=ft.ButtonStyle(color="red"))
        ], scroll=True),
        padding=15
    )

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Carga", icon=ft.Icons.INPUT, content=tab_carga),
            ft.Tab(text="Cálculo", icon=ft.Icons.SPORTS_HORSE, content=tab_calculo),
            ft.Tab(text="Resultados", icon=ft.Icons.LIST_ALT, content=tab_resultados),
        ],
        expand=1,
    )

    page.add(tabs)

ft.app(target=main)
