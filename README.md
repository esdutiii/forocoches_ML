# 🛡️ Filtro Avanzado ForoCoches (PC y Móvil + ML)

Este proyecto es un sistema de moderación y filtrado inteligente y automatizado para el foro ForoCoches. Combina un **UserScript de Tampermonkey** en el lado del navegador (cliente) con un **Scraper de Python automatizado en la nube** (vía GitHub Actions) para detectar no solo a trolls de una lista negra, sino también a sus "cómplices" o cuentas satélite basándose en interacciones relacionales direccionales.

---

## 💡 Arquitectura del Sistema

El sistema funciona de forma **Serverless** (sin servidores ni costes de mantenimiento) utilizando la infraestructura gratuita de GitHub:

```
┌────────────────────────────────────────────────────────┐
│                    NUBE (GitHub)                       │
│  ┌─────────────────┐       ┌────────────────────────┐  │
│  │ GitHub Actions  │ ──.   │ mapa_interacciones.json│  │
│  │ (Ejecución 6h)  │    \  │   (Almacén en nube)    │  │
│  └────────┬────────┘     \ └───────────▲────────────┘  │
│           │               \            │               │
│           ▼                `──► [Empuja el JSON]       │
│  ┌─────────────────┐                   │               │
│  │  script_ml.py   │ ──────────────────┘               │
│  │ (Scraper Python)│                                   │
│  └─────────────────┘                                   │
└────────────────────────────────────────┼───────────────┘
                                         │ (Lectura Raw)
┌────────────────────────────────────────▼───────────────┐
│                 CLIENTE (Navegador)                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │             Tampermonkey UserScript              │  │
│  │  1. Lee lista negra privada local.               │  │
│  │  2. Descarga "mapa_interacciones.json".          │  │
│  │  3. Cruza datos y genera "Lista Amarilla".       │  │
│  │  4. Inyecta estilos CSS (PC y Móvil).             │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

---

## 🎨 Código de Colores y Acciones Visuales

El script aplica diferentes niveles de alerta visual en la lista de hilos y comentarios según el usuario:

*   🟢 **Favoritos (Lista Verde):** Hilos resaltados con borde verde en el listado y recuadro completo en sus comentarios para facilitar su lectura.
*   🔴 **Trolls directos (Lista Negra):** Sus hilos en el listado general se marcan en rojo translúcido (`opacity: 0.85`) etiquetados como **peligrosos**, y sus comentarios dentro de los hilos se **ocultan por completo** (`display: none`).
*   🟡 **Sospechosos / Cómplices (Lista Amarilla):** Usuarios que han interactuado con los trolls de tu lista negra. Sus hilos y comentarios se marcan en **amarillo/ámbar** para advertirte antes de interactuar.

---

## 🔒 Seguridad e Interacción Direccional (Antisabotaje)

Para evitar que los trolls puedan sabotear a usuarios legítimos (por ejemplo, citando masivamente a gente sana para que el sistema los marque en amarillo), **las interacciones se mapean de forma estrictamente direccional (Usuario $\rightarrow$ Troll)**:

*   **Acción del Usuario al Troll (SÍ marca):** Si un usuario cita a un troll, o escribe en un hilo creado por un troll. El troll se almacena en la lista de interacciones del usuario, y el script lo marcará como sospechoso (amarillo).
*   **Acción del Troll al Usuario (NO marca):** Si el troll cita a un usuario sano, o el troll comenta en el hilo de un usuario sano. Esto se almacena en la lista de interacciones del troll (no del usuario), por lo que el usuario legítimo permanece a salvo.

---

## 📅 Período de Gracia (Evitar marcas retroactivas)

Para evitar marcar a usuarios que comentaron en hilos de trolls en el pasado de manera inocente, `script_ml.py` dispone de la variable:
```python
CUTOFF_THREAD_ID = 10703000
```
Cualquier hilo creado con un ID inferior a este será omitido por el scraper. De este modo, puedes avisar en el foro de que no se comente en hilos de trolls y empezar a trackear únicamente a partir del ID de hilo que desees.

---

## 🚀 Guía de Despliegue

### Paso 1: Configurar el repositorio en GitHub
1. Crea un repositorio en GitHub (puede ser **Público** o **Privado**).
2. Sube a la raíz del repositorio el archivo [`script_ml.py`](file:///c:/Users/ortas/OneDrive/Documentos/tampermonkey/script_ml.py) y la carpeta de workflows [`.github/workflows/actualizar_lista.yml`](file:///c:/Users/ortas/OneDrive/Documentos/tampermonkey/.github/workflows/actualizar_lista.yml).
3. Si el repositorio es privado, asegúrate de activar los permisos de lectura/escritura para los workflows en *Settings -> Actions -> General -> Workflow permissions -> Read and write permissions*.

### Paso 2: Ejecución y enlace al archivo JSON
1. Ve a la pestaña **Actions** de tu repositorio de GitHub, selecciona "Actualizar Lista de Sospechosos" y pulsa **Run workflow** para forzar la primera ejecución.
2. Tras finalizar, verás que ha aparecido el archivo `mapa_interacciones.json` en tu repositorio.
3. Haz clic sobre él, pulsa el botón **Raw** y copia esa dirección URL pública.

### Paso 3: Instalar en Tampermonkey
1. Crea un nuevo script en tu extensión de Tampermonkey.
2. Copia todo el contenido del archivo [`-Nuevo userscript-.txt`](file:///c:/Users/ortas/OneDrive/Documentos/tampermonkey/-Nuevo%20userscript-.txt) y pégalo.
3. En la línea 10 de la cabecera, reemplaza el enlace `@resource` de plantilla con tu dirección **Raw** obtenida en el Paso 2:
   ```javascript
   // @resource     jsonInteracciones https://raw.githubusercontent.com/TU_USUARIO/TU_REPOSITORIO/main/mapa_interacciones.json
   ```
4. Configura tu `listaNegra` y `listaFavoritos` privadas en el bloque de código 1 del script.
5. Guarda el UserScript en tu navegador. ¡Listo!
