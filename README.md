# Filtro Avanzado ForoCoches (PC y Móvil + ML)

Este proyecto es un sistema de moderación y filtrado inteligente y automatizado para el foro ForoCoches. Combina un **UserScript de Tampermonkey** en el lado del navegador (cliente) con un **script de Python automatizado en la nube** para detectar no solo a trolls de una lista negra, sino también a sus "cómplices" o cuentas satélite basándose en interacciones relacionales direccionales.

---

## Arquitectura del Sistema

El sistema funciona de forma **Serverless** utilizando la infraestructura de GitHub:

```
┌────────────────────────────────────────────────────────┐
│                    NUBE (GitHub)                       │
│  ┌─────────────────┐       ┌────────────────────────┐  │
│  │ GitHub Actions  │ ──.   │ mapa_interacciones.json│  │
│  │ (Ejecución 10m) │    \  │   (Almacén en nube)    │  │
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

## Código de Colores y Acciones Visuales

El script aplica diferentes niveles de alerta visual en la lista de hilos y comentarios según el usuario:

*   🟢 **Favoritos (Lista Verde):** Hilos resaltados con borde verde en el listado y recuadro completo en sus comentarios para facilitar su lectura.
*   🔴 **Trolls (Lista Negra):** Sus hilos en el listado general se marcan en rojo translúcido (`opacity: 0.85`) etiquetados como **peligrosos**, y sus comentarios dentro de los hilos se **ocultan por completo** (`display: none`).
*   🟡 **Sospechosos / Cómplices (Lista Amarilla):** Usuarios que han interactuado con los trolls de tu lista negra. Sus hilos y comentarios se marcan en **amarillo/ámbar** para advertirte antes de interactuar.

---

## Seguridad e Interacción Direccional (Antisabotaje)

Para evitar que los trolls puedan sabotear a usuarios legítimos (por ejemplo, citando masivamente a gente sana para que el sistema los marque en amarillo), **las interacciones se mapean de forma estrictamente direccional (Usuario $\rightarrow$ Troll)**:

*   **Acción del Usuario al Troll (SÍ marca):** Si un usuario cita a un troll, o escribe en un hilo creado por un troll. El troll se almacena en la lista de interacciones del usuario, y el script lo marcará como sospechoso (amarillo).
*   **Acción del Troll al Usuario (NO marca):** Si el troll cita a un usuario sano, o el troll comenta en el hilo de un usuario sano. Esto se almacena en la lista de interacciones del troll (no del usuario), por lo que el usuario legítimo permanece a salvo.

---

## Período de Gracia (Evitar marcas retroactivas)

Para evitar marcar a usuarios que comentaron en hilos de trolls en el pasado de manera inocente, `script_ml.py` dispone de la variable:
```python
CUTOFF_THREAD_ID = 10703000
```
Cualquier hilo creado con un ID inferior a este será omitido por el scraper. De este modo, puedes avisar en el foro de que no se comente en hilos de trolls y empezar a trackear únicamente a partir del ID de hilo que desees.

---

## Cómo Usarlo (Guía Rápida)

Solo necesitas el navegador con Tampermonkey instalado. No hace falta clonar ni tocar nada del repositorio.

1. **Abre el archivo `fc.txt` en GitHub:**
   https://github.com/esdutiii/forocoches_ML/blob/main/fc.txt

2. **Copia todo el contenido** (Ctrl+A → Ctrl+C).

3. **Crea un nuevo script en Tampermonkey** y pega el contenido (Ctrl+V).

4. **Configura tus listas privadas** (busca dentro del script la sección "1. CONFIGURACIÓN DE USUARIOS"):
   - `listaNegra`: usuarios que quieres ocultar (trolls).
   - `listaFavoritos`: usuarios que quieres resaltar en verde.
   - `muletillasUsuarios`: (opcional) frases a eliminar automáticamente de los mensajes de ciertos usuarios.

5. **Guarda el script** (Ctrl+S).

El `@resource` ya apunta directamente al `mapa_interacciones.json` de este repositorio, no necesitas tocar nada más. El script se actualizará automáticamente con los datos más recientes cada vez que entres a ForoCoches.
