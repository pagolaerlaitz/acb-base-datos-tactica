import sqlite3
import os
import unicodedata

def limpiar_nombre(nombre):
    if not nombre: return ""
    s = ''.join(c for c in unicodedata.normalize('NFD', nombre) if unicodedata.category(c) != 'Mn')
    s = s.lower().replace(",", "").replace(".", "").replace("-", " ")
    s = s.replace("'", "").replace("’", "").replace("`", "")
    s = " ".join(s.split())
    return s

def crear_base_datos(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Equipos (
            ID_Equipo INTEGER PRIMARY KEY AUTOINCREMENT, 
            Nombre TEXT UNIQUE, 
            Escudo TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Jugadores (
            ID_Jugador INTEGER PRIMARY KEY AUTOINCREMENT, 
            Nombre TEXT, 
            Apellido TEXT, 
            Nombre_Completo TEXT,
            Dorsal TEXT, 
            Posicion TEXT, 
            Altura TEXT, 
            Edad TEXT, 
            Condicion TEXT, 
            Foto TEXT,
            ID_Equipo INTEGER, 
            ID_ACB INTEGER,
            FOREIGN KEY(ID_Equipo) REFERENCES Equipos(ID_Equipo)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Partidos (
            ID_Partido INTEGER PRIMARY KEY AUTOINCREMENT,
            Local INTEGER,
            Visitante INTEGER,
            Jornada TEXT,
            Fecha TEXT,
            Hora TEXT,
            Puntos_Local INTEGER DEFAULT 0,
            Puntos_Visitante INTEGER DEFAULT 0,
            Estado TEXT DEFAULT 'Pendiente',
            Progreso_JSON TEXT,
            FOREIGN KEY(Local) REFERENCES Equipos(ID_Equipo),
            FOREIGN KEY(Visitante) REFERENCES Equipos(ID_Equipo)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Convocatorias (
            ID_Convocatoria INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_Partido INTEGER,
            ID_Equipo INTEGER,
            ID_Jugador INTEGER,
            FOREIGN KEY(ID_Partido) REFERENCES Partidos(ID_Partido),
            FOREIGN KEY(ID_Equipo) REFERENCES Equipos(ID_Equipo),
            FOREIGN KEY(ID_Jugador) REFERENCES Jugadores(ID_Jugador),
            UNIQUE(ID_Partido, ID_Jugador)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Play_By_Play (
            ID_Evento INTEGER PRIMARY KEY AUTOINCREMENT,
            Num_Viaje INTEGER,
            ID_Partido INTEGER,
            Cuarto TEXT,
            Minuto TEXT,
            Equipo_Atacante INTEGER,
            Equipo_Defensor INTEGER,
            Marcador_Local INTEGER,
            Marcador_Visitante INTEGER,
            Atacante_J1 INTEGER, Atacante_J2 INTEGER, Atacante_J3 INTEGER, Atacante_J4 INTEGER, Atacante_J5 INTEGER,
            Defensor_J1 INTEGER, Defensor_J2 INTEGER, Defensor_J3 INTEGER, Defensor_J4 INTEGER, Defensor_J5 INTEGER,
            Evento TEXT,
            Jugador INTEGER,
            Equipo INTEGER,
            Puntos INTEGER,
            Defense_Type TEXT,
            DPlayer INTEGER,
            SPlayer INTEGER,
            Playtype TEXT,
            Secondary_Playtype TEXT,
            PNR_Handler_Offense INTEGER,
            PNR_Roller_Offense INTEGER,
            PNR_Handler_Defense INTEGER,
            PNR_Roller_Defense INTEGER,
            PNR_Coverage TEXT,
            Coordenada_X REAL,
            Coordenada_Y REAL,
            FOREIGN KEY(ID_Partido) REFERENCES Partidos(ID_Partido),
            FOREIGN KEY(Equipo_Atacante) REFERENCES Equipos(ID_Equipo),
            FOREIGN KEY(Equipo_Defensor) REFERENCES Equipos(ID_Equipo),
            FOREIGN KEY(Atacante_J1) REFERENCES Jugadores(ID_Jugador),
            FOREIGN KEY(Atacante_J2) REFERENCES Jugadores(ID_Jugador),
            FOREIGN KEY(Atacante_J3) REFERENCES Jugadores(ID_Jugador),
            FOREIGN KEY(Atacante_J4) REFERENCES Jugadores(ID_Jugador),
            FOREIGN KEY(Atacante_J5) REFERENCES Jugadores(ID_Jugador),
            FOREIGN KEY(Defensor_J1) REFERENCES Jugadores(ID_Jugador),
            FOREIGN KEY(Defensor_J2) REFERENCES Jugadores(ID_Jugador),
            FOREIGN KEY(Defensor_J3) REFERENCES Jugadores(ID_Jugador),
            FOREIGN KEY(Defensor_J4) REFERENCES Jugadores(ID_Jugador),
            FOREIGN KEY(Defensor_J5) REFERENCES Jugadores(ID_Jugador),
            FOREIGN KEY(Jugador) REFERENCES Jugadores(ID_Jugador),
            FOREIGN KEY(Equipo) REFERENCES Equipos(ID_Equipo),
            FOREIGN KEY(DPlayer) REFERENCES Jugadores(ID_Jugador),
            FOREIGN KEY(SPlayer) REFERENCES Jugadores(ID_Jugador),
            FOREIGN KEY(PNR_Handler_Offense) REFERENCES Jugadores(ID_Jugador),
            FOREIGN KEY(PNR_Roller_Offense) REFERENCES Jugadores(ID_Jugador),
            FOREIGN KEY(PNR_Handler_Defense) REFERENCES Jugadores(ID_Jugador),
            FOREIGN KEY(PNR_Roller_Defense) REFERENCES Jugadores(ID_Jugador)
        )
    ''')
    
    try: cursor.execute("ALTER TABLE Jugadores ADD COLUMN ID_ACB INTEGER;")
    except sqlite3.OperationalError: pass 
    try: cursor.execute("ALTER TABLE Partidos ADD COLUMN Estado TEXT DEFAULT 'Pendiente';")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE Partidos ADD COLUMN Progreso_JSON TEXT;")
    except sqlite3.OperationalError: pass

    conn.commit()
    conn.close()

def obtener_equipos(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT Nombre, ID_Equipo FROM Equipos ORDER BY Nombre")
    equipos = cursor.fetchall()
    conn.close()
    return {nombre: id_equipo for nombre, id_equipo in equipos}

def registrar_partido(db_path, id_partido, id_local, id_visitante, jornada, fecha, hora):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO Partidos (ID_Partido) VALUES (?)', (id_partido,))
    cursor.execute('''
        UPDATE Partidos 
        SET Local=?, Visitante=?, Jornada=?, Fecha=?, Hora=?, Estado='En curso'
        WHERE ID_Partido=?
    ''', (id_local, id_visitante, jornada, fecha, hora, id_partido))
    conn.commit()
    conn.close()

def guardar_progreso_json(db_path, id_partido, json_data):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE Partidos SET Progreso_JSON = ?, Estado = 'En curso' WHERE ID_Partido = ?", (json_data, id_partido))
    conn.commit()
    conn.close()

def obtener_partidos_en_curso(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT P.ID_Partido, P.Local, P.Visitante, E1.Nombre, E2.Nombre, P.Jornada, P.Fecha, P.Progreso_JSON
        FROM Partidos P
        JOIN Equipos E1 ON P.Local = E1.ID_Equipo
        JOIN Equipos E2 ON P.Visitante = E2.ID_Equipo
        WHERE P.Estado = 'En curso'
    ''')
    res = cursor.fetchall()
    conn.close()
    return res

def obtener_ids_propios(db_path, mapeo_acb):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    traductor = {}
    
    cursor.execute("SELECT ID_Jugador, Nombre_Completo, Nombre FROM Jugadores WHERE ID_ACB IS NULL")
    jugadores_pendientes = cursor.fetchall()
    
    bd_nombres = {}
    for id_j, nom_comp, nom in jugadores_pendientes:
        texto_base = nom_comp if nom_comp else nom
        if texto_base:
            bd_nombres[limpiar_nombre(texto_base)] = id_j
            if "," in texto_base:
                partes = texto_base.split(",")
                if len(partes) == 2:
                    invertido = f"{partes[1].strip()} {partes[0].strip()}"
                    bd_nombres[limpiar_nombre(invertido)] = id_j

    for id_acb, nombre_acb in mapeo_acb.items():
        cursor.execute("SELECT ID_Jugador FROM Jugadores WHERE ID_ACB = ?", (id_acb,))
        resultado = cursor.fetchone()
        
        if resultado:
            traductor[id_acb] = resultado[0] 
        else:
            nombre_acb_limpio = limpiar_nombre(nombre_acb)
            tu_id = bd_nombres.get(nombre_acb_limpio)
            
            if not tu_id:
                palabras_acb = set(nombre_acb_limpio.split())
                for nom_bd, id_bd in bd_nombres.items():
                    if palabras_acb == set(nom_bd.split()):
                        tu_id = id_bd
                        break

            if tu_id:
                cursor.execute("UPDATE Jugadores SET ID_ACB = ? WHERE ID_Jugador = ?", (id_acb, tu_id))
                traductor[id_acb] = tu_id
            else:
                cursor.execute("INSERT INTO Jugadores (Nombre_Completo, ID_ACB) VALUES (?, ?)", (nombre_acb, id_acb))
                tu_nuevo_id = cursor.lastrowid
                traductor[id_acb] = tu_nuevo_id
                
    conn.commit()
    conn.close()
    return traductor

def volcar_partido_completo(db_path, bd_final, id_partido_acb, mapeo_jugadores, id_local, id_visitante, pts_loc_final, pts_vis_final):
    traductor_ids = obtener_ids_propios(db_path, mapeo_jugadores)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM Play_By_Play WHERE ID_Partido = ?", (id_partido_acb,))
    
    for jugada in bd_final:
        locales = [(traductor_ids.get(jid) if jid else None) for jid in jugada.get("quinto_local_ids", [])] + [None]*5
        visitantes = [(traductor_ids.get(jid) if jid else None) for jid in jugada.get("quinto_visitante_ids", [])] + [None]*5
        
        id_jugador_accion = traductor_ids.get(jugada.get("jugador_id"))
        id_equipo_accion = id_local if jugada.get("es_local") else id_visitante
        
        equipo_atacante = id_local if jugada.get("es_local") else id_visitante
        equipo_defensor = id_visitante if jugada.get("es_local") else id_local
        
        puntos_accion = 0
        ev_cod = jugada.get("codigo_acb")
        if ev_cod == 92: puntos_accion = 1
        elif ev_cod in [93, 100]: puntos_accion = 2
        elif ev_cod == 94: puntos_accion = 3
        
        cursor.execute('''
            INSERT INTO Play_By_Play (
                ID_Partido, Num_Viaje, Cuarto, Minuto, 
                Marcador_Local, Marcador_Visitante,
                Equipo_Atacante, Equipo_Defensor,
                Atacante_J1, Atacante_J2, Atacante_J3, Atacante_J4, Atacante_J5,
                Defensor_J1, Defensor_J2, Defensor_J3, Defensor_J4, Defensor_J5,
                Jugador, Equipo, Evento, Puntos, Playtype, Secondary_Playtype, SPlayer, DPlayer,
                PNR_Handler_Offense, PNR_Roller_Offense, PNR_Handler_Defense, PNR_Roller_Defense, PNR_Coverage, Defense_Type,
                Coordenada_X, Coordenada_Y
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            id_partido_acb,
            jugada.get("num_viaje"),
            jugada["minuto"].split("-")[0].strip() if "-" in jugada["minuto"] else "", 
            jugada["minuto"].split("-")[1].strip() if "-" in jugada["minuto"] else jugada["minuto"],
            jugada.get("marcador_local", 0),
            jugada.get("marcador_visitante", 0),
            equipo_atacante,
            equipo_defensor,
            locales[0], locales[1], locales[2], locales[3], locales[4],
            visitantes[0], visitantes[1], visitantes[2], visitantes[3], visitantes[4],
            id_jugador_accion,
            id_equipo_accion,
            jugada.get("accion", ""),
            puntos_accion,
            jugada.get("play_type", "Misc"),
            jugada.get("secondary_play_type", "Misc"),
            traductor_ids.get(jugada.get("splayer")),
            traductor_ids.get(jugada.get("jugador_defensa")),
            traductor_ids.get(jugada.get("pnr_handler")),
            traductor_ids.get(jugada.get("pnr_roller")),
            traductor_ids.get(jugada.get("pnr_handler_defense")),
            traductor_ids.get(jugada.get("pnr_roller_defense")),
            jugada.get("pnr_coverage", ""),
            jugada.get("defense_type", ""),
            jugada.get("coordenada_x"),
            jugada.get("coordenada_y")
        ))
        
    cursor.execute("UPDATE Partidos SET Estado = 'Finalizado', Progreso_JSON = '', Puntos_Local = ?, Puntos_Visitante = ? WHERE ID_Partido = ?", (pts_loc_final, pts_vis_final, id_partido_acb))
    conn.commit()
    conn.close()
    return True

def obtener_metadatos_partido(db_path, id_local, id_visitante):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ID_Equipo, Escudo FROM Equipos WHERE ID_Equipo IN (?, ?)", (id_local, id_visitante))
    escudos = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.execute("SELECT ID_ACB, Posicion, Dorsal FROM Jugadores WHERE ID_ACB IS NOT NULL")
    datos_jugadores = {row[0]: {"posicion": row[1], "dorsal": row[2]} for row in cursor.fetchall()}
    conn.close()
    return escudos.get(id_local), escudos.get(id_visitante), datos_jugadores

def obtener_foto_jugador(db_path, id_acb):
    if not id_acb: return None
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT Foto FROM Jugadores WHERE ID_ACB = ?", (id_acb,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado and resultado[0] else None

def obtener_jugadores_desconocidos(db_path, mapeo_acb):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ID_Jugador, Nombre_Completo, Nombre FROM Jugadores WHERE ID_ACB IS NULL")
    jugadores_pendientes = cursor.fetchall()
    
    bd_nombres = {}
    for id_j, nom_comp, nom in jugadores_pendientes:
        texto_base = nom_comp if nom_comp else nom
        if texto_base:
            bd_nombres[limpiar_nombre(texto_base)] = id_j
            if "," in texto_base:
                partes = texto_base.split(",")
                if len(partes) == 2:
                    invertido = f"{partes[1].strip()} {partes[0].strip()}"
                    bd_nombres[limpiar_nombre(invertido)] = id_j

    desconocidos = []
    for id_acb, nombre_acb in mapeo_acb.items():
        cursor.execute("SELECT ID_Jugador FROM Jugadores WHERE ID_ACB = ?", (id_acb,))
        if cursor.fetchone(): continue
            
        nombre_acb_limpio = limpiar_nombre(nombre_acb)
        tu_id = bd_nombres.get(nombre_acb_limpio)
        if not tu_id:
            palabras_acb = set(nombre_acb_limpio.split())
            for nom_bd, id_bd in bd_nombres.items():
                if palabras_acb == set(nom_bd.split()):
                    tu_id = id_bd
                    break
        if not tu_id: desconocidos.append((id_acb, nombre_acb))
            
    conn.close()
    return desconocidos

def obtener_plantilla_equipos(db_path, id_local, id_visitante):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT J.ID_Jugador, J.Nombre_Completo, E.Nombre 
        FROM Jugadores J
        JOIN Equipos E ON J.ID_Equipo = E.ID_Equipo
        WHERE J.ID_Equipo IN (?, ?) AND J.ID_ACB IS NULL
    ''', (id_local, id_visitante))
    res = cursor.fetchall()
    conn.close()
    return res

def vincular_id_acb(db_path, id_jugador_db, id_acb):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE Jugadores SET ID_ACB = ? WHERE ID_Jugador = ?", (id_acb, id_jugador_db))
    conn.commit()
    conn.close()

def crear_nuevo_jugador(db_path, nombre, apellido, dorsal, posicion, condicion, altura, edad, foto, id_equipo, id_acb):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    nombre_completo = f"{nombre} {apellido}".strip()
    cursor.execute('''
        INSERT INTO Jugadores (Nombre, Apellido, Nombre_Completo, Dorsal, Posicion, Altura, Edad, Condicion, Foto, ID_Equipo, ID_ACB)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (nombre, apellido, nombre_completo, dorsal, posicion, altura, edad, condicion, foto, id_equipo, id_acb))
    conn.commit()
    conn.close()

def registrar_convocatorias(db_path, id_partido_acb, mapeo_jugadores):
    traductor_ids = obtener_ids_propios(db_path, mapeo_jugadores)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for id_acb, id_jugador in traductor_ids.items():
        if id_jugador:
            cursor.execute("SELECT ID_Equipo FROM Jugadores WHERE ID_Jugador = ?", (id_jugador,))
            res = cursor.fetchone()
            if res and res[0]:
                id_equipo = res[0]
                cursor.execute('''
                    INSERT OR IGNORE INTO Convocatorias (ID_Partido, ID_Equipo, ID_Jugador)
                    VALUES (?, ?, ?)
                ''', (id_partido_acb, id_equipo, id_jugador))
                
    conn.commit()
    conn.close()