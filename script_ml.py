import requests
from bs4 import BeautifulSoup
import re
import json
import os
import time

# ==========================================
# CONFIGURACIÓN DEL SCRAPER
# ==========================================
SUBFORUMS = [43]  # Subforo principal: 43 = Videojuegos
NUM_PAGES = 2    # Número de páginas a escanear del listado (aprox. 60 hilos)
MAP_FILE = "mapa_interacciones.json"

# Período de gracia: ID del hilo a partir del cual se empezará a analizar.
# Hilos con un ID inferior a este serán omitidos (evita marcar a usuarios retroactivamente).
# Puedes buscar el ID en la URL de cualquier hilo nuevo (ej: showthread.php?t=10703000)
CUTOFF_THREAD_ID = 10703000

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def cargar_mapa_existente():
    """Carga el archivo de interacciones si ya existe en el repositorio."""
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Advertencia: No se pudo cargar el mapa existente ({e}). Se creará uno nuevo.")
    return {}

def guardar_mapa(data):
    """Guarda el mapa relacional en formato JSON."""
    try:
        with open(MAP_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Éxito: Mapa guardado. Total creadores en base de datos: {len(data)}")
    except Exception as e:
        print(f"Error al guardar el mapa: {e}")

def escanear_forumdisplay(forum_id):
    """Escanea el listado de hilos de un subforo para obtener IDs de hilos y sus creadores."""
    hilos = []
    for page in range(1, NUM_PAGES + 1):
        url = f"https://www.forocoches.com/foro/forumdisplay.php?f={forum_id}&page={page}"
        print(f"Escaneando listado de hilos: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=12)
            if response.status_code != 200:
                print(f"Error de acceso (status {response.status_code})")
                continue
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # --- Método A: Layout clásico de PC ---
            filas = soup.find_all("tr", id=lambda x: x and x.startswith("thread_"))
            for fila in filas:
                thread_id_match = re.search(r"thread_(\d+)", fila.get("id", ""))
                if not thread_id_match:
                    continue
                thread_id = thread_id_match.group(1)
                
                # Ubicar la celda del título
                celda_titulo = fila.find("td", id=f"td_threadtitle_{thread_id}") or fila.find("td", class_="alt1")
                if celda_titulo:
                    autor_nodo = celda_titulo.find(lambda tag: tag.name in ["span", "a"] and (
                        (tag.get("onclick") and "member.php" in tag.get("onclick")) or 
                        (tag.get("href") and "member.php" in tag.get("href"))
                    ))
                    if autor_nodo:
                        autor = autor_nodo.get_text(strip=True)
                        if int(thread_id) >= CUTOFF_THREAD_ID:
                            hilos.append({"id": thread_id, "creador": autor})
            
            # --- Método B: Layout moderno / responsive de ForoCoches ---
            if not hilos:
                links = soup.find_all("a", id=lambda x: x and x.startswith("thread_title_"))
                for l in links:
                    thread_id_match = re.search(r"thread_title_(\d+)", l.get("id", ""))
                    if not thread_id_match:
                        continue
                    thread_id = thread_id_match.group(1)
                    
                    # El contenedor del hilo tiene la información del autor
                    p = l.parent.parent
                    span_autor = p.find(lambda tag: tag.name == "span" and "@" in tag.get_text())
                    if span_autor:
                        texto = span_autor.get_text(strip=True)
                        m = re.search(r"@([^\s\-]+)", texto)
                        if m:
                            autor = m.group(1)
                            if int(thread_id) >= CUTOFF_THREAD_ID:
                                hilos.append({"id": thread_id, "creador": autor})
                                    
            time.sleep(1.5)  # Delay prudencial entre peticiones
        except Exception as e:
            print(f"Error procesando listado en página {page}: {e}")
            
    return hilos

def escanear_interacciones_hilo(thread_id, creador):
    """Escanea el interior de un hilo y recopila las interacciones de cada usuario (citas y respuestas)."""
    interacciones = {}  # { usuario_que_interactua: [usuarios_con_quien_interactua] }
    url = f"https://www.forocoches.com/foro/showthread.php?t={thread_id}"
    print(f"Escaneando interacciones del hilo {thread_id}...")
    try:
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code != 200:
            return {}
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # --- Método A: Layout clásico PC ---
        posts = soup.find_all("table", id=lambda x: x and re.match(r"^post\d+$", x))
        for p in posts:
            author_tag = p.find(class_="bigusername")
            if not author_tag:
                continue
            author = author_tag.get_text(strip=True)
            if not author:
                continue
            
            if author not in interacciones:
                interacciones[author] = set()
            
            # Interacción 1: Comentar en un hilo creado por otro usuario
            if creador and author != creador:
                interacciones[author].add(creador)
            
            # Buscar el mensaje y las citas (Interacción 2)
            msg = p.find("div", id=lambda x: x and x.startswith("post_message_"))
            if msg:
                quotes = msg.find_all(lambda t: t.name in ["div", "span"] and t.get_text() and ("Iniciado por" in t.get_text() or "Cita de" in t.get_text()))
                for q in quotes:
                    user_tag = q.find(["b", "strong"])
                    if user_tag:
                        quoted_user = user_tag.get_text(strip=True)
                        if quoted_user and quoted_user != author:
                            interacciones[author].add(quoted_user)
                    
        # --- Método B: Layout moderno / móvil ---
        if not posts:
            posts_modernos = soup.find_all("div", id=lambda x: x and x.startswith("postmenu_") and not x.endswith("_menu"))
            for p in posts_modernos:
                enlace = p.find("a")
                if not enlace:
                    continue
                author = enlace.get_text(strip=True)
                if not author:
                    continue
                
                if author not in interacciones:
                    interacciones[author] = set()
                
                # Interacción 1: Comentar en un hilo creado por otro usuario
                if creador and author != creador:
                    interacciones[author].add(creador)
                
                # El contenedor del post
                container = p.find_parent("div", id=lambda x: x and x.startswith("edit"))
                if container:
                    msg = container.find("div", id=lambda x: x and x.startswith("post_message_"))
                    if msg:
                        quotes = msg.find_all(lambda t: t.name in ["div", "span"] and t.get_text() and ("Iniciado por" in t.get_text() or "Cita de" in t.get_text()))
                        for q in quotes:
                            user_tag = q.find(["b", "strong"])
                            if user_tag:
                                quoted_user = user_tag.get_text(strip=True)
                                if quoted_user and quoted_user != author:
                                    interacciones[author].add(quoted_user)
                            
    except Exception as e:
        print(f"Error escaneando interacciones del hilo {thread_id}: {e}")
        
    return {u: list(citados) for u, citados in interacciones.items()}

def main():
    print("Iniciando scraper de mapeo relacional de ForoCoches (interacciones direccionales)...")
    mapa = cargar_mapa_existente()
    
    hilos_encontrados = []
    for f_id in SUBFORUMS:
        hilos = escanear_forumdisplay(f_id)
        hilos_encontrados.extend(hilos)
        
    print(f"Hilos totales encontrados en listados: {len(hilos_encontrados)}")
    
    # Procesamos individualmente cada hilo para mapear interacciones
    for hilo in hilos_encontrados:
        t_id = hilo["id"]
        creador = hilo["creador"]
        
        interacciones_hilo = escanear_interacciones_hilo(t_id, creador)
        
        for usuario, citados in interacciones_hilo.items():
            if not usuario:
                continue
            
            if usuario not in mapa:
                mapa[usuario] = []
            
            # Fusionar con registros previos eliminando duplicados
            existentes = set(mapa[usuario])
            for c in citados:
                if c != usuario:  # Evitar que se relacione consigo mismo
                    existentes.add(c)
            mapa[usuario] = list(existentes)
            
        # Espera de 2 segundos para evitar rate-limits y baneos de IP de la Action
        time.sleep(2.0)
        
    guardar_mapa(mapa)

if __name__ == "__main__":
    main()
