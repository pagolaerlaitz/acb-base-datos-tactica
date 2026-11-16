import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import requests
import os
import base64
import json
import mi_db as database 

# --- INICIALIZACIÓN DE BASE DE DATOS ---
ruta_bd = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ACB.db")
database.crear_base_datos(ruta_bd)

# --- CONFIGURACIÓN DE PÁGINA Y ESTILOS ---
st.set_page_config(page_title="Scouting ACB", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; margin-top: 0 !important; }
    header[data-testid="stHeader"] { display: none !important; }
    
    .stSelectbox div[data-baseweb="select"] > div, .stTextInput div[data-baseweb="base-input"] {
        border-color: #EA580C !important; border-width: 2px !important; border-style: solid !important;
        border-radius: 6px !important; background-color: #FFFFFF !important;
    }
    
    div[data-testid="stButton"] button {
        border: 2px solid #EA580C !important; border-radius: 6px !important; color: #000000 !important;
        background-color: #FFFFFF !important; padding: 5px 2px !important; height: 55px !important; 
        width: 100% !important; display: flex !important; align-items: center !important;
        justify-content: center !important; transition: all 0.2s ease-in-out !important;
    }
    div[data-testid="stButton"] button p {
        font-weight: 900 !important; font-size: 1.05em !important; color: #000000 !important;
        white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; 
        margin: 0 !important; width: 100% !important; text-align: center !important;
    }
    
    div[data-testid="stButton"] button[kind="primary"] { background-color: #EA580C !important; color: #FFFFFF !important; }
    div[data-testid="stButton"] button[kind="primary"] p { color: #FFFFFF !important; }
    
    div[data-testid="stButton"] button[kind="secondary"]:has(p:contains("Guardar Edición")) {
        background-color: #16A34A !important; border-color: #16A34A !important; color: #FFFFFF !important;
    }
    div[data-testid="stButton"] button[kind="secondary"]:has(p:contains("Guardar Edición")) p { color: #FFFFFF !important; }
    
    .box-pista {
        background-color: #FFFFFF; color: #000000; padding: 15px; border-radius: 8px;
        border: 2px solid #EA580C; margin-bottom: 20px; font-size: 0.9em; line-height: 1.5;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .scoreboard-container {
        display: flex; align-items: center; justify-content: space-between; background-color: #FFFFFF;
        border: 2px solid #EA580C; border-radius: 10px; padding: 10px 20px; margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 100%;
    }
    .team-info { display: flex; align-items: center; gap: 15px; font-size: 1.4em; font-weight: 800; color: #000000; width: 35%; }
    .team-info.visitor { justify-content: flex-end; text-align: right; }
    .score-text { font-size: 2.2em; font-weight: 900; color: #EA580C; text-align: center; width: 30%; letter-spacing: 2px; }
    .shield-img { width: 60px; height: 60px; object-fit: contain; }
    
    [data-testid="stProgress"] { margin-top: 0px !important; }
    [data-testid="stProgress"] > label { display: none !important; }
    [data-testid="stProgress"] > div > div { background-color: #FFFFFF !important; border: 2px solid #EA580C !important; border-radius: 5px !important; }
    [data-testid="stProgress"] > div > div > div { background-color: #EA580C !important; border-radius: 3px !important; }
    </style>
""", unsafe_allow_html=True)

DICCIONARIO_ACCIONES = {
    92: "Tiro libre anotado", 93: "Tiro de 2 anotado", 94: "Triple anotado",
    96: "Tiro libre fallado", 97: "Tiro de 2 fallado", 98: "Triple fallado",
    100: "Mate", 101: "Rebote ofensivo", 102: "Tapón", 103: "Recuperación",
    104: "Rebote defensivo", 105: "Tapón recibido", 106: "Pérdida",
    107: "Asistencia (T2)", 108: "Asistencia (Triple)", 109: "Falta en ataque",
    110: "Falta recibida", 112: "Entra a pista", 113: "Tiempo muerto",
    115: "Sale de pista", 116: "Final de cuarto", 119: "Asistencia (TL)",
    121: "Inicio de partido / cuarto", 122: "Balón al aire", 123: "Final del partido",
    159: "Falta personal", 160: "Falta personal 1TL", 161: "Falta personal 2TL",
    162: "Falta personal 3TL", 178: "Salto inicial ganado", 179: "Salto inicial perdido",
    200: "Descalificado", 408: "Revisión reloj", 416: "Challenge local", 417: "Challenge visitante",
    599: "Quinteto inicial", 600: "Posesión", 761: "Falta flagrante", 783: "Falta técnica"
}

TIPOS_JUGADA = ["", "Misc", "Isolation", "Transition", "Pick & Roll Handler", "Pick & Roll Roller", "Spot Up", "Post Up", "Cut", "Offscreen", "Handoff", "Putback"]
TIPOS_COVERAGE = ["", "Show", "Drop", "Under", "Switch", "Trap", "Ice"]
TIPOS_DEFENSA = ["", "Man", "3-2", "2-3", "1-3-1", "Special"]

def get_image_base64(path):
    if not path or not os.path.exists(path): return ""
    with open(path, "rb") as img_file:
        b64_string = base64.b64encode(img_file.read()).decode()
    ext = path.split('.')[-1].lower()
    mime = f"image/{ext}" if ext in ['png', 'jpg', 'jpeg'] else "image/png"
    return f"data:{mime};base64,{b64_string}"

def calcular_marcador(partido_plano, orden_limite):
    pts_loc, pts_vis = 0, 0
    for play in partido_plano:
        if play["orden"] >= orden_limite: break
        ev = play["codigo_acb"]
        pts = 0
        if ev == 92: pts = 1
        elif ev in [93, 100]: pts = 2
        elif ev == 94: pts = 3
        if pts > 0:
            if play["es_local"]: pts_loc += pts
            else: pts_vis += pts
    return pts_loc, pts_vis

ORDEN_POSICIONES = {"Base": 1, "Escolta": 2, "Alero": 3, "Ala-Pivot": 4, "Ala pivot": 4, "Ala-pívot": 4, "Pivot": 5, "Pívot": 5}

def ordenar_quinteto(lista_ids_acb, dict_datos_jugadores):
    def peso(id_acb):
        datos = dict_datos_jugadores.get(id_acb, {})
        pos = datos.get("posicion") or ""
        return ORDEN_POSICIONES.get(pos.title(), 99)
    return sorted(lista_ids_acb, key=peso)

def sincronizar_quinteto(acb_ids, dict_datos, persisted_q):
    if not persisted_q:
        q = ordenar_quinteto(acb_ids, dict_datos)
        while len(q) < 5: q.append(None)
        return q
    
    acb_set = set(x for x in acb_ids if x)
    persisted_set = set(x for x in persisted_q if x)
    
    if acb_set == persisted_set:
        return persisted_q 
    
    new_q = []
    for p in persisted_q:
        if p in acb_set:
            new_q.append(p)
        else:
            new_q.append(None) 
            
    nuevos = list(acb_set - persisted_set)
    nuevos_ordenados = ordenar_quinteto(nuevos, dict_datos)
    
    for n in nuevos_ordenados:
        if None in new_q:
            idx = new_q.index(None)
            new_q[idx] = n
        else:
            new_q.append(n)
            
    return new_q[:5]

def extraer_jugadas_reales(match_id, nombre_local, nombre_visitante):
    headers = {
        'accept': '*/*', 'accept-language': 'es', 'cache-control': 'no-cache',
        'origin': 'https://live.acb.com', 'pragma': 'no-cache', 'referer': 'https://live.acb.com/',
        'user-agent': 'Mozilla/5.0', 'x-apikey': os.environ.get('ACB_API_KEY', ''),
    }
    respuesta = requests.get('https://api2.acb.com/api/matchdata/PlayByPlay/play-by-play', params={'matchId': match_id}, headers=headers)
    if respuesta.status_code != 200:
        st.error(f"Error al conectar con la API: {respuesta.status_code}")
        return [], [], {}

    datos_partido = respuesta.json()
    jugadas = datos_partido.get("plays", [])
    
    partido_plano = []
    mapeo_jugadores = {} 
    en_pista_local, en_pista_visitante = set(), set()
    
    for jugada in jugadas:
        evento_id = jugada.get("playType")
        jugador_id = jugada.get("playerLicenseId")
        es_local = jugada.get("local", False)
        
        if not jugador_id or jugada.get("playerName") == "Acción de equipo":
            jugador_nombre = f"EQUIPO: {nombre_local if es_local else nombre_visitante}"
        else:
            jugador_nombre = jugada.get("playerName")
            mapeo_jugadores[jugador_id] = jugador_nombre

        if jugador_id:
            if evento_id in [599, 112]: 
                if es_local: en_pista_local.add(jugador_id)
                else: en_pista_visitante.add(jugador_id)
            elif evento_id == 115: 
                if es_local: en_pista_local.discard(jugador_id)
                else: en_pista_visitante.discard(jugador_id)
        
        partido_plano.append({
            "orden": jugada.get("order"),
            "minuto": f"Q{jugada.get('quarter')} - {jugada.get('minute', 0):02d}:{jugada.get('second', 0):02d}",
            "jugador": jugador_nombre,
            "jugador_id": jugador_id, 
            "accion": DICCIONARIO_ACCIONES.get(evento_id, f"Acción ({evento_id})"),
            "codigo_acb": evento_id,
            "es_local": es_local,
            "quinto_local_ids": list(en_pista_local), 
            "quinto_visitante_ids": list(en_pista_visitante),
            "num_viaje": None
        })

    datos_wizard = []
    i = 0
    num_viaje_actual = 1
    
    FIN_POSESION = [93, 94, 97, 98, 100, 106, 161, 162] 
    EVENTOS_PREVIOS = [103, 107, 108, 109, 110, 119] 
    EVENTOS_POSTERIORES = [92, 96, 101, 102, 103, 104, 105, 107, 108, 109, 110, 119, 159, 160] 
    IGNORAR_INTERMEDIOS = [112, 113, 115, 408, 416, 417] 

    while i < len(partido_plano):
        play = partido_plano[i]
        evento_id = play["codigo_acb"]
        
        if evento_id in FIN_POSESION:
            k = i - 1
            eventos_previos = []
            while k >= 0:
                prev_play = partido_plano[k]
                if prev_play["num_viaje"] is not None: break 
                if play["orden"] - prev_play["orden"] > 15: break 
                if prev_play["codigo_acb"] in EVENTOS_PREVIOS:
                    prev_play["num_viaje"] = num_viaje_actual
                    eventos_previos.insert(0, prev_play)
                elif prev_play["codigo_acb"] not in IGNORAR_INTERMEDIOS:
                    break
                k -= 1
                
            j = i + 1
            eventos_posteriores = []
            max_fts = 0
            if evento_id == 161: max_fts = 2
            elif evento_id == 162: max_fts = 3
            elif evento_id in [93, 94, 100]: max_fts = 1
            fts_lanzados = 0
            
            while j < len(partido_plano):
                next_play = partido_plano[j]
                c = next_play["codigo_acb"]
                if c in FIN_POSESION: break 
                
                if c in EVENTOS_POSTERIORES:
                    next_play["num_viaje"] = num_viaje_actual
                    eventos_posteriores.append(next_play)
                    if c == 160: max_fts = 1 
                    if c in [92, 96]:
                        fts_lanzados += 1
                        if fts_lanzados >= max_fts:
                            if c == 92:
                                j += 1
                                break
                    if c in [101, 102, 104, 105]:
                        j += 1
                        break
                elif c not in IGNORAR_INTERMEDIOS:
                    break
                j += 1
                
            todos_eventos = eventos_previos + [play] + eventos_posteriores
            principal = play
            
            if evento_id in [161, 162]:
                falta_recibida = next((e for e in todos_eventos if e["codigo_acb"] == 110), None)
                if falta_recibida:
                    principal = falta_recibida
            
            pts = 0
            for e in todos_eventos:
                if e["codigo_acb"] in [93, 100]: pts += 2
                elif e["codigo_acb"] == 94: pts += 3
                elif e["codigo_acb"] == 92: pts += 1
            
            play["num_viaje"] = num_viaje_actual
            
            paquete = {
                "num_viaje": num_viaje_actual,
                "minuto": principal["minuto"],
                "jugador_principal": principal["jugador"],
                "id_jugador_principal": principal["jugador_id"],
                "accion_principal": principal["accion"],
                "codigo_principal": play["codigo_acb"], 
                "es_local": principal["es_local"],
                "eventos_agrupados": todos_eventos, 
                "puntos_totales": pts,
                "quinto_local_ids": play["quinto_local_ids"],
                "quinto_visitante_ids": play["quinto_visitante_ids"],
                "orden_base": principal["orden"] 
            }
            
            datos_wizard.append(paquete)
            num_viaje_actual += 1
            i = j
        else:
            i += 1
            
    return partido_plano, datos_wizard, mapeo_jugadores

def handle_swap(equipo, idx):
    if st.session_state.get('selected_swap') is None:
        st.session_state.selected_swap = (equipo, idx)
    else:
        equipo_previo, idx_previo = st.session_state.selected_swap
        if equipo_previo == equipo and idx_previo != idx:
            if equipo == 'local':
                q = st.session_state.current_q_loc
                q[idx_previo], q[idx] = q[idx], q[idx_previo]
                st.session_state.persisted_q_loc = list(q)
            else:
                q = st.session_state.current_q_vis
                q[idx_previo], q[idx] = q[idx], q[idx_previo]
                st.session_state.persisted_q_vis = list(q)
        st.session_state.selected_swap = None

def get_dropdown_index_by_string(opciones, valor, default=0):
    return opciones.index(valor) if valor in opciones else default

def get_dropdown_index_by_id(opciones_dict, target_id, default=0):
    if target_id is None: return default
    values = list(opciones_dict.values())
    return values.index(target_id) if target_id in values else default

def iniciar_partido(temp_data):
    database.obtener_ids_propios(ruta_bd, temp_data["mapeo"])
    database.registrar_convocatorias(ruta_bd, temp_data["match_id"], temp_data["mapeo"])
    
    st.session_state.partido_plano = temp_data["plano"]
    st.session_state.jugadas_wizard = temp_data["wizard"]
    st.session_state.mapeo_jugadores = temp_data["mapeo"]
    st.session_state.match_id_actual = temp_data["match_id"]
    st.session_state.id_equipo_local = temp_data["id_loc"]
    st.session_state.id_equipo_visitante = temp_data["id_vis"]
    
    st.session_state.persisted_q_loc = []
    st.session_state.persisted_q_vis = []
    
    ruta_escudo_L, ruta_escudo_V, dict_datos_jugadores = database.obtener_metadatos_partido(
        ruta_bd, temp_data["id_loc"], temp_data["id_vis"]
    )
    st.session_state.img_local_b64 = get_image_base64(ruta_escudo_L)
    st.session_state.img_visit_b64 = get_image_base64(ruta_escudo_V)
    st.session_state.dict_datos_jugadores = dict_datos_jugadores
    st.session_state.nombre_local = temp_data["local_sel"]
    st.session_state.nombre_visitante = temp_data["visit_sel"]
    
    st.session_state.datos_guardados = json.loads(temp_data.get("progreso_json", "[]")) if temp_data.get("progreso_json") else []
    st.session_state.indice_jugada = len(st.session_state.datos_guardados)
    st.session_state.partido_cargado = True


# --- INICIALIZACIÓN DE VARIABLES DE SESIÓN ---
if 'partido_cargado' not in st.session_state: st.session_state.partido_cargado = False
if 'partido_plano' not in st.session_state: st.session_state.partido_plano = []
if 'jugadas_wizard' not in st.session_state: st.session_state.jugadas_wizard = []
if 'indice_jugada' not in st.session_state: st.session_state.indice_jugada = 0
if 'datos_guardados' not in st.session_state: st.session_state.datos_guardados = []
if 'mapeo_jugadores' not in st.session_state: st.session_state.mapeo_jugadores = {}
if 'match_id_actual' not in st.session_state: st.session_state.match_id_actual = ""

if 'modo_edicion' not in st.session_state: st.session_state.modo_edicion = False
if 'indice_retorno' not in st.session_state: st.session_state.indice_retorno = None
if 'mostrar_lista_edicion' not in st.session_state: st.session_state.mostrar_lista_edicion = False

if 'resolviendo_desconocidos' not in st.session_state: st.session_state.resolviendo_desconocidos = False
if 'jugadores_desconocidos' not in st.session_state: st.session_state.jugadores_desconocidos = []
if 'temp_match_data' not in st.session_state: st.session_state.temp_match_data = None
if 'persisted_q_loc' not in st.session_state: st.session_state.persisted_q_loc = []
if 'persisted_q_vis' not in st.session_state: st.session_state.persisted_q_vis = []

# --- MENÚ PRINCIPAL ---
if not st.session_state.partido_cargado:
    
    if st.session_state.resolviendo_desconocidos:
        st.warning(f"⚠️ Atención: Hay jugadores de la ACB que no han sido reconocidos en tu Base de Datos ({len(st.session_state.jugadores_desconocidos)} pendientes).")
        id_acb, nombre_acb = st.session_state.jugadores_desconocidos[0]
        st.error(f"Jugador no encontrado: **{nombre_acb}** (ID ACB: {id_acb})")
        temp_data = st.session_state.temp_match_data
        plantilla = database.obtener_plantilla_equipos(ruta_bd, temp_data["id_loc"], temp_data["id_vis"])
        opciones_manuales = {f"{p[2]} - {p[1]}": p[0] for p in plantilla}
        
        tab_manual, tab_nuevo = st.tabs(["🔗 Asignar manualmente (Vincular)", "➕ Añadir nuevo jugador"])
        with tab_manual:
            if opciones_manuales:
                sel_jugador = st.selectbox("Selecciona un jugador ya existente en tu base de datos:", list(opciones_manuales.keys()))
                if st.button("Vincular Jugador", type="primary"):
                    id_jugador_db = opciones_manuales[sel_jugador]
                    database.vincular_id_acb(ruta_bd, id_jugador_db, id_acb)
                    st.session_state.jugadores_desconocidos.pop(0)
                    if not st.session_state.jugadores_desconocidos:
                        st.session_state.resolviendo_desconocidos = False
                        iniciar_partido(st.session_state.temp_match_data)
                    st.rerun()
            else:
                st.info("No hay jugadores sin ID vinculada en las plantillas de estos equipos. Usa 'Añadir nuevo jugador'.")
                
        with tab_nuevo:
            with st.form("form_nuevo_jugador"):
                col1, col2 = st.columns(2)
                nombre_def = nombre_acb.split()[0] if nombre_acb else ""
                apellido_def = " ".join(nombre_acb.split()[1:]) if nombre_acb and len(nombre_acb.split()) > 1 else ""
                nombre_new = col1.text_input("Nombre", value=nombre_def)
                apellido_new = col2.text_input("Apellido", value=apellido_def)
                col_eq, col_dor = st.columns(2)
                dict_eqs = {temp_data["local_sel"]: temp_data["id_loc"], temp_data["visit_sel"]: temp_data["id_vis"]}
                equipo_new = col_eq.selectbox("Equipo", list(dict_eqs.keys()))
                dorsal_new = col_dor.text_input("Dorsal")
                col_pos, col_cond = st.columns(2)
                pos_new = col_pos.selectbox("Posición", ["Base", "Escolta", "Alero", "Ala-Pivot", "Pivot"])
                cond_new = col_cond.selectbox("Condición", ["Alta", "Lesionado", "Descartado"])
                col_alt, col_edad = st.columns(2)
                altura_new = col_alt.text_input("Altura (ej. 1.95)")
                edad_new = col_edad.text_input("Edad")
                foto_new = st.text_input("URL / Ruta de la Foto (opcional)")
                if st.form_submit_button("Guardar y Añadir a la Base de Datos"):
                    database.crear_nuevo_jugador(ruta_bd, nombre_new, apellido_new, dorsal_new, pos_new, cond_new, altura_new, edad_new, foto_new, dict_eqs[equipo_new], id_acb)
                    st.session_state.jugadores_desconocidos.pop(0)
                    if not st.session_state.jugadores_desconocidos:
                        st.session_state.resolviendo_desconocidos = False
                        iniciar_partido(st.session_state.temp_match_data)
                    st.rerun()

    else:
        st.write("Bienvenido al Scouting ACB. Selecciona una opción para comenzar.")
        diccionario_equipos = database.obtener_equipos(ruta_bd)
        lista_nombres = list(diccionario_equipos.keys())
        
        tab1, tab2 = st.tabs(["🏀 Registrar Nuevo Partido", "🔄 Continuar Partido"])
        with tab1:
            st.write("Introduce los datos del nuevo partido:")
            col1, col2 = st.columns(2)
            with col1: jornada_input = st.text_input("**Jornada:**", value="1")
            with col2: fecha_input = st.date_input("**Fecha:**")
            col3, col4 = st.columns(2)
            with col3: hora_input = st.time_input("**Hora:**")
            with col4: match_id_input = st.text_input("**ID Partido ACB:**", value="105683")
            col5, col6 = st.columns(2)
            with col5: local_sel = st.selectbox("**Equipo Local:**", lista_nombres, key="loc_nuevo")
            with col6: visit_sel = st.selectbox("**Equipo Visitante:**", lista_nombres, key="vis_nuevo")
            
            if st.button("Guardar Partido y Empezar", type="primary", use_container_width=True):
                if local_sel == visit_sel:
                    st.error("El equipo local y visitante no pueden ser el mismo.")
                elif not match_id_input.strip():
                    st.error("El ID del partido ACB es obligatorio.")
                else:
                    with st.spinner("Registrando partido y comprobando jugadores..."):
                        id_loc = diccionario_equipos[local_sel]
                        id_vis = diccionario_equipos[visit_sel]
                        database.registrar_partido(ruta_bd, match_id_input, id_loc, id_vis, jornada_input, str(fecha_input), str(hora_input))
                        plano, wizard, mapeo = extraer_jugadas_reales(match_id_input, local_sel, visit_sel)
                        
                        if plano:
                            desconocidos = database.obtener_jugadores_desconocidos(ruta_bd, mapeo)
                            temp_data = {
                                "plano": plano, "wizard": wizard, "mapeo": mapeo,
                                "id_loc": id_loc, "id_vis": id_vis,
                                "local_sel": local_sel, "visit_sel": visit_sel,
                                "match_id": match_id_input, "progreso_json": None
                            }
                            if desconocidos:
                                st.session_state.temp_match_data = temp_data
                                st.session_state.jugadores_desconocidos = desconocidos
                                st.session_state.resolviendo_desconocidos = True
                                st.rerun()
                            else:
                                iniciar_partido(temp_data)
                                st.rerun()

        with tab2:
            en_curso = database.obtener_partidos_en_curso(ruta_bd)
            if not en_curso:
                st.info("No hay partidos pendientes de terminar.")
            else:
                opciones = {f"Jornada {c[5]} | {c[3]} vs {c[4]} ({c[6]}) - ID ACB: {c[0]}": c for c in en_curso}
                sel_cont = st.selectbox("Selecciona un partido en curso:", list(opciones.keys()))
                
                if st.button("Cargar Partido Guardado", type="primary", use_container_width=True):
                    datos_partido = opciones[sel_cont]
                    match_id_input = str(datos_partido[0])
                    id_loc = datos_partido[1]
                    id_vis = datos_partido[2]
                    local_sel = datos_partido[3]
                    visit_sel = datos_partido[4]
                    progreso_json = datos_partido[7]
                    
                    with st.spinner("Recuperando jugadas y comprobando jugadores..."):
                        plano, wizard, mapeo = extraer_jugadas_reales(match_id_input, local_sel, visit_sel)
                        
                        if plano:
                            desconocidos = database.obtener_jugadores_desconocidos(ruta_bd, mapeo)
                            temp_data = {
                                "plano": plano, "wizard": wizard, "mapeo": mapeo,
                                "id_loc": id_loc, "id_vis": id_vis,
                                "local_sel": local_sel, "visit_sel": visit_sel,
                                "match_id": match_id_input, "progreso_json": progreso_json
                            }
                            if desconocidos:
                                st.session_state.temp_match_data = temp_data
                                st.session_state.jugadores_desconocidos = desconocidos
                                st.session_state.resolviendo_desconocidos = True
                                st.rerun()
                            else:
                                iniciar_partido(temp_data)
                                st.rerun()

if st.session_state.partido_cargado:
    total_jugadas = len(st.session_state.jugadas_wizard)
    indice = st.session_state.indice_jugada

    if indice >= total_jugadas:
        st.success("Partido completado y etiquetado.")
        bd_final = []
        tags_tacticos = {j["num_viaje"]: j for j in st.session_state.datos_guardados}
        
        for jugada in st.session_state.partido_plano:
            jugada_final = jugada.copy()
            viaje = jugada.get("num_viaje")
            
            ml, mv = calcular_marcador(st.session_state.partido_plano, jugada["orden"] + 1)
            jugada_final["marcador_local"] = ml
            jugada_final["marcador_visitante"] = mv
            
            if viaje and viaje in tags_tacticos:
                jugada_final["play_type"] = tags_tacticos[viaje].get("play_type", "")
                jugada_final["secondary_play_type"] = tags_tacticos[viaje].get("secondary_play_type", "")
                jugada_final["splayer"] = tags_tacticos[viaje].get("splayer", None)
                jugada_final["jugador_defensa"] = tags_tacticos[viaje].get("jugador_defensa", None)
                jugada_final["pnr_handler"] = tags_tacticos[viaje].get("pnr_handler", None)
                jugada_final["pnr_roller"] = tags_tacticos[viaje].get("pnr_roller", None)
                jugada_final["pnr_handler_defense"] = tags_tacticos[viaje].get("pnr_handler_defense", None)
                jugada_final["pnr_roller_defense"] = tags_tacticos[viaje].get("pnr_roller_defense", None)
                jugada_final["pnr_coverage"] = tags_tacticos[viaje].get("pnr_coverage", "")
                jugada_final["defense_type"] = tags_tacticos[viaje].get("defense_type", "")
                jugada_final["coordenada_x"] = tags_tacticos[viaje].get("coordenada_x", None)
                jugada_final["coordenada_y"] = tags_tacticos[viaje].get("coordenada_y", None)
            else:
                jugada_final["play_type"] = ""
                jugada_final["secondary_play_type"] = ""
                jugada_final["splayer"] = None
                jugada_final["jugador_defensa"] = None
                jugada_final["pnr_handler"] = None
                jugada_final["pnr_roller"] = None
                jugada_final["pnr_handler_defense"] = None
                jugada_final["pnr_roller_defense"] = None
                jugada_final["pnr_coverage"] = ""
                jugada_final["defense_type"] = ""
                jugada_final["coordenada_x"] = None
                jugada_final["coordenada_y"] = None
            
            bd_final.append(jugada_final)
            
        pts_loc_final, pts_vis_final = calcular_marcador(st.session_state.partido_plano, float('inf'))
            
        if st.button("Guardar en Base de Datos (SQLite)"):
            with st.spinner("Inyectando eventos en Play_By_Play..."):
                try:
                    database.volcar_partido_completo(
                        ruta_bd, bd_final, st.session_state.match_id_actual, 
                        st.session_state.mapeo_jugadores, 
                        st.session_state.id_equipo_local, st.session_state.id_equipo_visitante,
                        pts_loc_final, pts_vis_final
                    )
                    st.success("Base de datos actualizada con éxito.")
                except Exception as e:
                    st.error(f"Error en la base de datos: {e}")
        
        st.write("---")
        if st.button("Volver al inicio (Borrar memoria)"):
            st.session_state.partido_cargado = False
            st.session_state.indice_jugada = 0
            st.session_state.datos_guardados = []
            st.session_state.modo_edicion = False
            st.rerun()
            
    else:
        jugada_actual = st.session_state.jugadas_wizard[indice]
        
        if 'last_indice' not in st.session_state or st.session_state.last_indice != indice:
            if st.session_state.modo_edicion:
                st.session_state.current_q_loc = st.session_state.datos_guardados[indice]["quinto_local_ids"]
                st.session_state.current_q_vis = st.session_state.datos_guardados[indice]["quinto_visitante_ids"]
            else:
                q_loc = sincronizar_quinteto(jugada_actual['quinto_local_ids'], st.session_state.dict_datos_jugadores, st.session_state.persisted_q_loc)
                q_vis = sincronizar_quinteto(jugada_actual['quinto_visitante_ids'], st.session_state.dict_datos_jugadores, st.session_state.persisted_q_vis)
                
                st.session_state.current_q_loc = q_loc
                st.session_state.current_q_vis = q_vis
                st.session_state.persisted_q_loc = list(q_loc)
                st.session_state.persisted_q_vis = list(q_vis)
                
            st.session_state.last_indice = indice
            st.session_state.selected_swap = None
        
        saved_data = st.session_state.datos_guardados[indice] if st.session_state.modo_edicion else {}
        
        # 1. SCOREBOARD Y QUINTETOS
        orden_inicio_posesion = jugada_actual['eventos_agrupados'][0]['orden']
        pts_loc, pts_vis = calcular_marcador(st.session_state.partido_plano, orden_inicio_posesion)
        
        tag_img_L = f'<img src="{st.session_state.img_local_b64}" class="shield-img">' if st.session_state.img_local_b64 else ''
        tag_img_V = f'<img src="{st.session_state.img_visit_b64}" class="shield-img">' if st.session_state.img_visit_b64 else ''

        scoreboard_html = f"""
        <div class="scoreboard-container">
            <div class="team-info">
                {tag_img_L} <span>{st.session_state.nombre_local}</span>
            </div>
            <div class="score-text">
                {pts_loc} - {pts_vis}
            </div>
            <div class="team-info visitor">
                <span>{st.session_state.nombre_visitante}</span> {tag_img_V}
            </div>
        </div>
        """
        st.markdown(scoreboard_html, unsafe_allow_html=True)
        
        if st.session_state.modo_edicion:
            st.warning("⚠️ ESTÁS EN MODO EDICIÓN. Modifica la jugada y pulsa 'Guardar Edición y Volver' al final.")
        
        col_q_loc, col_espacio, col_q_vis = st.columns([1, 0.05, 1])
        
        def render_botones_jugadores(equipo_key, lista_ids):
            cols = st.columns(5)
            for i in range(5):
                jid = lista_ids[i]
                with cols[i]:
                    if jid:
                        nombre_entero = st.session_state.mapeo_jugadores.get(jid, "N/A")
                        nombre_corto = nombre_entero.split(" ")[-1] if " " in nombre_entero else nombre_entero
                        dorsal = st.session_state.dict_datos_jugadores.get(jid, {}).get("dorsal", "")
                        texto_mostrar = f"#{dorsal} - {nombre_corto}" if dorsal else f"{nombre_corto}"
                        is_selected = (st.session_state.get('selected_swap') == (equipo_key, i))
                        btn_tipo = "primary" if is_selected else "secondary"
                        st.button(texto_mostrar, key=f"btn_{equipo_key}_{i}_{indice}", type=btn_tipo, use_container_width=True, on_click=handle_swap, args=(equipo_key, i))
                    else:
                        st.button("...", key=f"btn_{equipo_key}_{i}_{indice}_vacio", disabled=True, use_container_width=True)

        with col_q_loc:
            render_botones_jugadores('local', st.session_state.current_q_loc)
        with col_espacio:
            st.write("") 
        with col_q_vis:
            render_botones_jugadores('visitante', st.session_state.current_q_vis)
        
        # 2. BARRA DE PROGRESO 
        if not st.session_state.modo_edicion:
            st.progress((indice + 1) / total_jugadas if total_jugadas > 0 else 0)
        st.markdown("<br>", unsafe_allow_html=True) 
        
        # 3. PANTALLA DIVIDIDA Y LOGICA DE EVENTOS
        col_izq, col_der = st.columns(2)
        
        id_principal = jugada_actual.get("id_jugador_principal")
        ruta_foto = database.obtener_foto_jugador(ruta_bd, id_principal) if id_principal else None
        b64_foto = get_image_base64(ruta_foto)

        if b64_foto:
            tag_foto = f'<img src="{b64_foto}" style="width: 140px; height: 140px; object-fit: cover; object-position: top center; border-radius: 50%; border: 3px solid #EA580C; background-color: #FFFFFF; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">'
        else:
            tag_foto = '<div style="width: 140px; height: 140px; border-radius: 50%; background-color: #FFFFFF; display: flex; align-items: center; justify-content: center; border: 3px solid #EA580C; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"></div>'

        with col_izq:
            st.markdown(f"""
                <div class='box-pista' style='height: 100%; min-height: 200px; display: flex; align-items: center; gap: 25px;'>
                    <div style="flex-shrink: 0;">{tag_foto}</div>
                    <div>
                        <div style='font-size: 1.1em; font-weight: bold; color: #000000; margin-bottom: 5px;'>{jugada_actual['minuto']}</div>
                        <div style='font-size: 1.8em; font-weight: 900; color: #000000; margin-bottom: 5px; line-height: 1.1;'>{jugada_actual['jugador_principal']}</div>
                        <div style='font-size: 1.15em; color: #000000; margin-bottom: 12px;'>{jugada_actual['accion_principal']}</div>
                        <div style='color: #EA580C; font-weight: bold; font-size: 1.15em;'>Puntos generados: {jugada_actual['puntos_totales']}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        with col_der:
            orden_principal = jugada_actual["orden_base"]
            secundarias = [e for e in jugada_actual['eventos_agrupados'] if e['orden'] != orden_principal]
            if secundarias:
                eventos_html = "".join([f"<li style='margin-bottom: 10px;'><b style='color: #000000;'>{e['jugador']}</b> <span style='color: #000000;'>- {e['accion']}</span></li>" for e in secundarias])
            else:
                eventos_html = "<li style='color: #000000; list-style: none; margin-left: -20px;'><i>Sin acciones secundarias asociadas</i></li>"

            st.markdown(f"""
                <div class='box-pista' style='height: 100%; min-height: 200px;'>
                    <div style='font-weight: 800; font-size: 1.25em; color: #000000; border-bottom: 2px solid #EA580C; padding-bottom: 8px; margin-bottom: 15px;'>Acciones Secundarias</div>
                    <ul style='margin-top: 0; margin-bottom: 0; padding-left: 20px; font-size: 1.05em; line-height: 1.5; color: #000000;'>
                        {eventos_html}
                    </ul>
                </div>
            """, unsafe_allow_html=True)
            
        # 🚀 LÓGICA DE DETECCIÓN DE TIPOS DE JUGADA
        codigo_principal = jugada_actual.get("codigo_principal", 0)
        es_tiro_campo = codigo_principal in [93, 94, 97, 98, 100]
        es_falta_tl = codigo_principal in [161, 162]
        es_perdida = codigo_principal == 106
        
        mostrar_tactica = True
        es_tiro = False
        tipo_falta_val = None
        
        if es_falta_tl:
            st.write("---")
            val_def = saved_data.get("tipo_falta", "Falta de tiro") if st.session_state.modo_edicion else "Falta de tiro"
            tipo_falta_val = st.radio("🏀 **¿Motivo de los tiros libres?**", ["Falta de tiro", "Bonus"], index=0 if val_def=="Falta de tiro" else 1, key=f"tf_{indice}", horizontal=True)
            if tipo_falta_val == "Bonus":
                mostrar_tactica = False
                st.info("Falta por bonus. No es necesario registrar táctica. Pulsa Guardar y Siguiente.")
            else:
                es_tiro = True
        elif es_tiro_campo:
            es_tiro = True

        coord_x, coord_y = None, None
        defense_type, tipo_jugada, tipo_secundaria = "", "", ""
        dplayer_id, splayer_id = None, None
        pnr_h_id, pnr_r_id, pnr_hd_id, pnr_rd_id = None, None, None, None
        pnr_coverage = ""
        
        # Flags para la validación de campos obligatorios
        mostrar_dp = False
        mostrar_sp = False
        mostrar_pnr = False
        
        if mostrar_tactica:
            st.write("---")
            col_layout_izq, col_espaciador, col_layout_der = st.columns([1.2, 0.1, 1])
            
            with col_layout_izq:
                if es_tiro:
                    st.write("**📍 Ubicación del Tiro (Obligatorio):**")
                    ruta_cancha = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "cancha.png")
                    if os.path.exists(ruta_cancha):
                        img_cancha = Image.open(ruta_cancha).convert("RGB")
                        ancho_fijo = 550 
                        if img_cancha.width != ancho_fijo:
                            proporcion = ancho_fijo / float(img_cancha.width)
                            alto_fijo = int((float(img_cancha.height) * float(proporcion)))
                            img_cancha = img_cancha.resize((ancho_fijo, alto_fijo), Image.Resampling.LANCZOS)
                            
                        key_cancha = f"cancha_edit_{indice}" if st.session_state.modo_edicion else f"cancha_{indice}"
                        coords_actuales = st.session_state.get(key_cancha)
                        
                        if coords_actuales:
                            coord_x = coords_actuales["x"]
                            coord_y = coords_actuales["y"]
                        elif st.session_state.modo_edicion and saved_data.get("coordenada_x") is not None:
                            coord_x = saved_data["coordenada_x"]
                            coord_y = saved_data["coordenada_y"]
                            
                        if coord_x is not None and coord_y is not None:
                            es_anotado = any(e.get("codigo_acb") in [93, 94, 100] for e in jugada_actual['eventos_agrupados'])
                            color_punto = "#16A34A" if es_anotado else "#DC2626"
                            draw = ImageDraw.Draw(img_cancha)
                            r = 9 
                            draw.ellipse((coord_x - r, coord_y - r, coord_x + r, coord_y + r), fill=color_punto, outline="#FFFFFF", width=2)
                        streamlit_image_coordinates(img_cancha, key=key_cancha)
                    else:
                        st.warning("⚠️ Falta el archivo 'cancha.png'.")
                else:
                    st.info("Esta jugada no es un tiro de campo. No hay ubicación.")
            
            with col_layout_der:
                st.write("**⚙️ Añade datos tácticos (Obligatorios):**")
                if jugada_actual["es_local"]:
                    q_ataque_full = st.session_state.current_q_loc
                    q_defensa_full = st.session_state.current_q_vis
                else:
                    q_ataque_full = st.session_state.current_q_vis
                    q_defensa_full = st.session_state.current_q_loc
                    
                ids_ataque = [j for j in q_ataque_full if j is not None]
                ids_defensa = [j for j in q_defensa_full if j is not None]
                    
                def formatear_jugador_lista(jid):
                    nombre = st.session_state.mapeo_jugadores.get(jid, "N/A")
                    dorsal = st.session_state.dict_datos_jugadores.get(jid, {}).get("dorsal", "")
                    return f"#{dorsal} - {nombre}" if dorsal else nombre
                    
                dict_ataque = {"Ninguno": None}
                for jid in ids_ataque: dict_ataque[formatear_jugador_lista(jid)] = jid
                dict_defensa = {"Ninguno": None}
                for jid in ids_defensa: dict_defensa[formatear_jugador_lista(jid)] = jid

                idx_dt = get_dropdown_index_by_string(TIPOS_DEFENSA, saved_data.get("defense_type", "Man"), default=1)
                idx_pt = get_dropdown_index_by_string(TIPOS_JUGADA, saved_data.get("play_type", ""))
                idx_spt = get_dropdown_index_by_string(TIPOS_JUGADA, saved_data.get("secondary_play_type", ""))
                
                if es_perdida:
                    col_t1, col_t2 = st.columns(2)
                    with col_t1: defense_type = st.selectbox("**Defense Type:**", TIPOS_DEFENSA, index=idx_dt, key=f"dt_{indice}")
                    with col_t2: tipo_jugada = st.selectbox("**Playtype:**", TIPOS_JUGADA, index=idx_pt, key=f"pt_{indice}")
                    mostrar_pnr = tipo_jugada in ["Pick & Roll Handler", "Pick & Roll Roller"]
                else:
                    col_t1, col_t2, col_t3 = st.columns(3)
                    with col_t1: defense_type = st.selectbox("**Defense Type:**", TIPOS_DEFENSA, index=idx_dt, key=f"dt_{indice}")
                    with col_t2: tipo_jugada = st.selectbox("**Playtype:**", TIPOS_JUGADA, index=idx_pt, key=f"pt_{indice}")
                    with col_t3: tipo_secundaria = st.selectbox("**Secondary Playtype:**", TIPOS_JUGADA, index=idx_spt, key=f"spt_{indice}")
                    
                    mostrar_dp = tipo_jugada in ["Isolation", "Post Up"]
                    mostrar_sp = tipo_secundaria != "" and tipo_secundaria not in ["Pick & Roll Handler", "Pick & Roll Roller"]
                    mostrar_pnr = tipo_jugada in ["Pick & Roll Handler", "Pick & Roll Roller"] or tipo_secundaria in ["Pick & Roll Handler", "Pick & Roll Roller"]

                    if mostrar_dp or mostrar_sp:
                        col_dp, col_sp = st.columns(2)
                        with col_dp:
                            if mostrar_dp:
                                idx_principal = q_ataque_full.index(id_principal) if id_principal in q_ataque_full else -1
                                def_dplayer_id = q_defensa_full[idx_principal] if idx_principal != -1 else None
                                idx_dp_calc = get_dropdown_index_by_id(dict_defensa, def_dplayer_id, 0)
                                idx_dp = get_dropdown_index_by_id(dict_defensa, saved_data.get("jugador_defensa"), idx_dp_calc)
                                dplayer_str = st.selectbox("**DPlayer:**", list(dict_defensa.keys()), index=idx_dp, key=f"dp_{indice}")
                                dplayer_id = dict_defensa[dplayer_str]
                            else: st.write("")
                        with col_sp:
                            if mostrar_sp:
                                idx_sp = get_dropdown_index_by_id(dict_ataque, saved_data.get("splayer"), 0)
                                splayer_str = st.selectbox("**Secondary Player:**", list(dict_ataque.keys()), index=idx_sp, key=f"sp_{indice}")
                                splayer_id = dict_ataque[splayer_str]
                            else: st.write("")

                if mostrar_pnr:
                    st.write("---")
                    st.write("**Detalles del Pick & Roll:**")
                    def_h_off_id, def_r_off_id, def_h_def_id, def_r_def_id = None, None, None, None
                    if tipo_jugada == "Pick & Roll Handler":
                        def_h_off_id = id_principal
                        idx_principal = q_ataque_full.index(id_principal) if id_principal in q_ataque_full else -1
                        def_h_def_id = q_defensa_full[idx_principal] if idx_principal != -1 else None
                        def_r_off_id = q_ataque_full[4] 
                        def_r_def_id = q_defensa_full[4] 
                    elif tipo_jugada == "Pick & Roll Roller":
                        def_r_off_id = id_principal
                        idx_principal = q_ataque_full.index(id_principal) if id_principal in q_ataque_full else -1
                        def_r_def_id = q_defensa_full[idx_principal] if idx_principal != -1 else None
                        def_h_off_id = q_ataque_full[0] 
                        def_h_def_id = q_defensa_full[0] 
                    elif tipo_secundaria in ["Pick & Roll Handler", "Pick & Roll Roller"]:
                        def_h_off_id = q_ataque_full[0] 
                        def_h_def_id = q_defensa_full[0] 
                        def_r_off_id = q_ataque_full[4] 
                        def_r_def_id = q_defensa_full[4] 
                        
                    idx_ho_calc = get_dropdown_index_by_id(dict_ataque, def_h_off_id, 0)
                    idx_ro_calc = get_dropdown_index_by_id(dict_ataque, def_r_off_id, 0)
                    idx_hd_calc = get_dropdown_index_by_id(dict_defensa, def_h_def_id, 0)
                    idx_rd_calc = get_dropdown_index_by_id(dict_defensa, def_r_def_id, 0)
                    
                    idx_ho = get_dropdown_index_by_id(dict_ataque, saved_data.get("pnr_handler"), idx_ho_calc)
                    idx_ro = get_dropdown_index_by_id(dict_ataque, saved_data.get("pnr_roller"), idx_ro_calc)
                    idx_hd = get_dropdown_index_by_id(dict_defensa, saved_data.get("pnr_handler_defense"), idx_hd_calc)
                    idx_rd = get_dropdown_index_by_id(dict_defensa, saved_data.get("pnr_roller_defense"), idx_rd_calc)
                    idx_cov = get_dropdown_index_by_string(TIPOS_COVERAGE, saved_data.get("pnr_coverage", ""))
                    
                    col_pnr1, col_pnr2 = st.columns(2)
                    with col_pnr1:
                        h_off_str = st.selectbox("**Handler Offense:**", list(dict_ataque.keys()), index=idx_ho, key=f"ho_{indice}")
                        h_def_str = st.selectbox("**Handler Defense:**", list(dict_defensa.keys()), index=idx_hd, key=f"hd_{indice}")
                        pnr_coverage = st.selectbox("**P&R Coverage:**", TIPOS_COVERAGE, index=idx_cov, key=f"cov_{indice}")
                    with col_pnr2:
                        r_off_str = st.selectbox("**Roller Offense:**", list(dict_ataque.keys()), index=idx_ro, key=f"ro_{indice}")
                        r_def_str = st.selectbox("**Roller Defense:**", list(dict_defensa.keys()), index=idx_rd, key=f"rd_{indice}")
                        
                    pnr_h_id = dict_ataque[h_off_str]
                    pnr_r_id = dict_ataque[r_off_str]
                    pnr_hd_id = dict_defensa[h_def_str]
                    pnr_rd_id = dict_defensa[r_def_str]
            
        if st.session_state.mostrar_lista_edicion:
            st.write("---")
            st.write("**📝 Selecciona una jugada reciente para editar:**")
            start_idx = max(0, st.session_state.indice_jugada - 5)
            for i in range(start_idx, st.session_state.indice_jugada):
                jp = st.session_state.jugadas_wizard[i]
                if st.button(f"Modificar Jugada {i+1}: {jp['minuto']} - {jp['jugador_principal']} ({jp['accion_principal']})", key=f"btn_edit_list_{i}", use_container_width=True):
                    st.session_state.modo_edicion = True
                    st.session_state.indice_retorno = st.session_state.indice_jugada
                    st.session_state.indice_jugada = i
                    st.session_state.mostrar_lista_edicion = False
                    st.rerun()

        st.write("---")
        
        error_container = st.empty()
        
        # 🚀 BOTONES DE NAVEGACIÓN
        col_atras, col_editar, col_medio, col_siguiente = st.columns([1, 1.2, 2, 1.2])
        
        with col_atras:
            if indice > 0 or st.session_state.modo_edicion:
                if st.button("⬅️ Atrás", use_container_width=True):
                    if st.session_state.modo_edicion:
                        st.session_state.indice_jugada = st.session_state.indice_retorno
                        st.session_state.modo_edicion = False
                        st.session_state.indice_retorno = None
                    else:
                        st.session_state.indice_jugada -= 1
                        st.session_state.datos_guardados.pop()
                    st.rerun()
                    
        with col_editar:
            if not st.session_state.modo_edicion and st.session_state.indice_jugada > 0:
                if st.button("✏️ Editar últimas 5", use_container_width=True):
                    st.session_state.mostrar_lista_edicion = not st.session_state.mostrar_lista_edicion
                    st.rerun()
                    
        with col_medio:
            if not st.session_state.modo_edicion:
                if st.button("💾 Guardar y Continuar más adelante", use_container_width=True):
                    progreso = json.dumps(st.session_state.datos_guardados)
                    database.guardar_progreso_json(ruta_bd, st.session_state.match_id_actual, progreso)
                    st.session_state.partido_cargado = False
                    st.session_state.indice_jugada = 0
                    st.session_state.datos_guardados = []
                    st.rerun()
                    
        with col_siguiente:
            label_boton = "Guardar Edición" if st.session_state.modo_edicion else "Guardar y Siguiente ➡️"
            tipo_boton = "secondary" if st.session_state.modo_edicion else "primary"
            
            if st.button(label_boton, use_container_width=True, type=tipo_boton):
                
                # --- SISTEMA DE VALIDACIÓN ---
                errores = []
                
                if es_tiro and (coord_x is None or coord_y is None):
                    errores.append("📍 Falta marcar la ubicación del tiro en la cancha.")
                    
                if mostrar_tactica:
                    if not defense_type:
                        errores.append("🛡️ El campo 'Defense Type' es obligatorio.")
                    if not tipo_jugada:
                        errores.append("📋 El campo 'Playtype' es obligatorio.")
                        
                    if mostrar_dp and dplayer_id is None:
                        errores.append("👤 El campo 'DPlayer' (Defensor) es obligatorio para la acción principal elegida.")
                        
                    if mostrar_sp and splayer_id is None:
                        errores.append("👥 El campo 'Secondary Player' es obligatorio al seleccionar un Secondary Playtype.")
                        
                    if mostrar_pnr:
                        if not pnr_coverage:
                            errores.append("🛡️ El campo 'P&R Coverage' es obligatorio.")
                        if pnr_h_id is None or pnr_r_id is None or pnr_hd_id is None or pnr_rd_id is None:
                            errores.append("🔄 Faltan jugadores por asignar en el menú de Pick & Roll (no pueden ser 'Ninguno').")

                if errores:
                    with error_container.container():
                        for e in errores:
                            st.error(e)
                else:
                    nuevo_dato = {
                        "orden_base": jugada_actual["orden_base"],
                        "num_viaje": jugada_actual["num_viaje"],
                        "play_type": tipo_jugada,
                        "secondary_play_type": tipo_secundaria,
                        "splayer": splayer_id,
                        "jugador_defensa": dplayer_id,
                        "defense_type": defense_type,
                        "pnr_handler": pnr_h_id,
                        "pnr_roller": pnr_r_id,
                        "pnr_handler_defense": pnr_hd_id,
                        "pnr_roller_defense": pnr_rd_id,
                        "pnr_coverage": pnr_coverage,
                        "coordenada_x": coord_x,
                        "coordenada_y": coord_y,
                        "quinto_local_ids": st.session_state.current_q_loc,
                        "quinto_visitante_ids": st.session_state.current_q_vis,
                        "tipo_falta": tipo_falta_val
                    }
                    
                    st.session_state.persisted_q_loc = list(st.session_state.current_q_loc)
                    st.session_state.persisted_q_vis = list(st.session_state.current_q_vis)
                    
                    if st.session_state.modo_edicion:
                        st.session_state.datos_guardados[indice] = nuevo_dato
                        st.session_state.indice_jugada = st.session_state.indice_retorno
                        st.session_state.modo_edicion = False
                        st.session_state.indice_retorno = None
                    else:
                        st.session_state.datos_guardados.append(nuevo_dato)
                        st.session_state.indice_jugada += 1
                        
                    st.rerun()