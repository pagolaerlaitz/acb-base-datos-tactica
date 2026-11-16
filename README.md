# Base de datos táctica de partidos de la Liga ACB

Aplicación en Streamlit que descarga el registro jugada a jugada (play-by-play) de un partido de la Liga ACB y permite completarlo, posesión a posesión, con información táctica que la estadística oficial no recoge. El resultado se guarda en una base de datos SQLite diseñada para el proyecto.

**Estado:** terminado (septiembre – octubre de 2026). La app genera la base de datos, pero todavía no calcula métricas ni gráficos a partir de ella. Ese análisis lo desarrollé después en otro proyecto: [analitica-baloncesto-segunda-nacional](https://github.com/pagolaerlaitz/analitica-baloncesto-segunda-nacional).

## Qué pregunta responde

La estadística oficial cuenta **qué** pasó: un tiro, un rebote, una pérdida. No cuenta **cómo**: con qué tipo de jugada se llegó al tiro, cómo se defendió el bloqueo directo o desde dónde se tiró. Este proyecto construye esa capa táctica sobre los datos oficiales, para poder responder después a preguntas como:

- ¿Qué tipos de jugada usa más un equipo y cuáles le dan más puntos?
- ¿Cómo defiende cada equipo el bloqueo directo y qué le funciona?
- ¿Desde qué zonas tira cada jugador?

## De dónde salen los datos

1. **Play-by-play oficial.** Se descarga de la API que usa la web de directos de la ACB (`live.acb.com`), indicando el identificador del partido. Son los mismos datos que la ACB muestra públicamente en su web. Se usan solo para análisis deportivo y no se redistribuyen. La clave de acceso no está en el código: se lee de la variable de entorno `ACB_API_KEY`.
2. **Etiquetado manual.** Viendo el vídeo del partido, cada jugada se completa en la app con:
   - tipo de defensa
   - tipo de jugada (playtype) principal y secundario
   - jugadores implicados
   - en el bloqueo directo: quién bloquea y quién maneja, quién defiende a cada uno y cómo se defiende
   - posición del tiro, marcada con un clic sobre la pista

**Este repositorio no incluye datos:** ni la base de datos, ni fotos de jugadores, ni escudos.

## Qué se hace con ellos

1. **Descarga:** la app pide el play-by-play de un partido a la API y lo convierte en una lista de jugadas.
2. **Cruce de jugadores:** los identificadores de la ACB se relacionan con los jugadores de la base de datos propia. Si un jugador no existe todavía, se puede vincular a mano o crear desde la propia app.
3. **Etiquetado:** la app recorre el partido jugada a jugada. Lleva el marcador y los quintetos en pista, y muestra solo los campos que tienen sentido en cada jugada (por ejemplo, los del bloqueo directo solo si la jugada es un pick and roll). Antes de guardar comprueba que no falta nada, como la posición de un tiro.
4. **Guardado:** el progreso se guarda por el camino, para poder seguir otro día. Al terminar, el partido completo se vuelca en la base de datos.

La base de datos tiene cinco tablas relacionadas: equipos, jugadores, partidos, convocatorias y play-by-play enriquecido. Se han etiquetado dos partidos completos, con unas 700 jugadas.

## Herramientas

- **Python:** requests, sqlite3, Pillow
- **Base de datos:** SQLite, con un modelo relacional propio
- **Interfaz:** Streamlit y streamlit-image-coordinates (clic sobre la pista)
- **Desarrollo:** VS Code y GitHub. Programado con ayuda de asistentes de IA (Claude y Gemini).

## Cómo ejecutarlo

Requiere Python 3.12 o superior.

```bash
pip install -r requirements.txt
export ACB_API_KEY="tu_clave"      # en Windows: set ACB_API_KEY=tu_clave
streamlit run scripts/app.py
```

La primera vez se crea `ACB.db` vacía en la raíz del repositorio. Para registrar un partido hay que cargar antes los equipos de la liga en la tabla `Equipos`. `scripts/prueba_scraping.py` es la primera prueba de conexión con la API.

---

Erlaitz Pagola · Máster en Ciencia de Datos e IA (EBIS) · Doble Grado en ADE y Economía (UPV/EHU)
