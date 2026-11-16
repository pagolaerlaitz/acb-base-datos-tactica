import os
import requests

# Cabeceras que usa la web live.acb.com. La clave se lee de la variable de entorno ACB_API_KEY.
headers = {
    'accept': '*/*',
    'accept-language': 'es,es-ES;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,de;q=0.5,ar;q=0.4,de-LU;q=0.3,ar-JO;q=0.2',
    'cache-control': 'no-cache',
    'origin': 'https://live.acb.com',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://live.acb.com/',
    'sec-ch-ua': '"Microsoft Edge";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0',
    'x-apikey': os.environ.get('ACB_API_KEY', ''),
}

params = {
    'matchId': '105683',
}

respuesta = requests.get('https://api2.acb.com/api/matchdata/PlayByPlay/play-by-play', params=params, headers=headers)

# La URL que también te ha generado la web
url = 'https://api2.acb.com/api/matchdata/PlayByPlay/play-by-play?matchId=105683'

print("Conectando con la API de la ACB...")
respuesta = requests.get(url, headers=headers)

if respuesta.status_code == 200:
    datos_partido = respuesta.json()
    jugadas = datos_partido.get("plays", [])
    print(f"¡Conexión exitosa! Se han descargado {len(jugadas)} jugadas.")
else:
    print(f"Error al conectar. Código: {respuesta.status_code}")