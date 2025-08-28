import random
import base64
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# -------------------------
# Config
# -------------------------
st.set_page_config(page_title="Picas y Fijas", page_icon="🎯", layout="centered")

# --- CSS responsive ---
st.markdown("""
<style>
@media (max-width: 640px) {
  .block-container { padding: 0.75rem 0.8rem; }
  label, .stTextInput label { font-size: 1rem !important; }
  input[type="text"], input[type="number"] { font-size: 1.05rem !important; }
  .stButton>button { width: 100% !important; padding: 0.8rem 1rem; font-size: 1rem; }
  .stDataFrame { height: 340px !important; }
}
div.stAlert { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Helpers del juego
# -------------------------
def secret_number():
    """Return a list of 4 unique digits, allowing leading zero (e.g., 0123)."""
    return random.sample(range(10), 4)

def to_digits(s: str):
    """Convert 4-char string to list of ints: '0123' -> [0,1,2,3]."""
    return [int(ch) for ch in s]

def count_fijas(guess_digits, target_digits):
    """Fijas (bulls): correct digit in the correct place."""
    return sum(1 for i in range(4) if guess_digits[i] == target_digits[i])

def count_picas(guess_digits, target_digits):
    """Picas (cows): correct digit in the wrong place."""
    picas = 0
    for i, d in enumerate(guess_digits):
        if d in target_digits and d != target_digits[i]:
            picas += 1
    return picas

def valid_guess(s: str):
    """A valid guess is exactly 4 digits (0-9)."""
    return len(s) == 4 and s.isdigit()

# -------------------------
# 🎵 Música: utilidades
# -------------------------
MUSIC_PATH = "assets/WE ARE THE CRYSTAL GEMS (Steven Universe Intro) - Piano Tutorial.mp3"

@st.cache_data
def load_mp3_b64(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode()

def render_bgm(mp3_path=MUSIC_PATH):
    """
    Crea (una sola vez) un <audio> persistente en window.parent (fuera del iframe),
    y en cada rerun solo ajusta play/pause y volumen sin resetear el src.
    Requiere st.session_state.bgm_enabled (bool) y st.session_state.bgm_volume (0.0–1.0).
    """
    try:
        mp3_b64 = load_mp3_b64(mp3_path)
    except FileNotFoundError:
        st.warning(f"⚠️ No encontré el archivo de música: {mp3_path}")
        return

    enabled = "true" if st.session_state.get("bgm_enabled", False) else "false"
    volume  = float(st.session_state.get("bgm_volume", 0.25))

    components.html(f"""
    <script>
    (function() {{
      const P = window.parent;
      if (!P) return;

      // Crea el audio global una sola vez
      if (!P.bgmAudio) {{
        const a = P.document.createElement('audio');
        a.id = 'global_bgm_audio';
        a.loop = true;
        a.autoplay = false;  // lo controlamos con play() tras el botón
        a.src = "data:audio/mp3;base64,{mp3_b64}";
        a.style.display = "none";  // sin controles visibles
        P.document.body.appendChild(a);
        P.bgmAudio = a;
      }}

      // Ajusta volumen en cada render (no cambiamos la src)
      try {{
        P.bgmAudio.volume = {volume:.2f};
      }} catch(e) {{}}

      // Play / Pause según el estado
      if ({enabled}) {{
        P.bgmAudio.play().catch(()=>{{ /* si requiere gesto, el botón ya lo da */ }});
      }} else {{
        try {{ P.bgmAudio.pause(); }} catch(e) {{}}
      }}
    }})();
    </script>
    """, height=0)

# -------------------------
# Session state
# -------------------------
if "target" not in st.session_state:
    st.session_state.target = secret_number()

if "history" not in st.session_state:
    st.session_state.history = []  # {"Jugada": "0123", "Picas": 1, "Fijas": 2}

if "status" not in st.session_state:
    st.session_state.status = "ready"  # "ready", "playing", "won"

if "coins" not in st.session_state:
    st.session_state.coins = 0  # acumulado de monedas

# 🎵 estado de música
if "bgm_enabled" not in st.session_state:
    st.session_state.bgm_enabled = False   # usuario activó música?
if "bgm_volume" not in st.session_state:
    st.session_state.bgm_volume = 0.25     # 0.0 a 1.0

# -------------------------
# UI
# -------------------------
st.title("🎯 Picas y Fijas")
st.caption("## Versión Lore 2025 🦗.")
st.markdown("""
## 🎯 Cómo se juega *Picas y Fijas*

1. **El reto**  
   La computadora piensa un número secreto de **4 dígitos diferentes** (por ejemplo: 5271).  
   Tu misión es adivinarlo.  

2. **Tu jugada**  
   Escribe un número de 4 dígitos y presiona **“¡A jugar!”**.  

3. **Resultados**  
   - 🔴 **Fijas** → dígitos correctos en la **posición exacta**.  
     > Ejemplo: si el secreto es 5271 y escribes 5279 → tienes 3 fijas.  
   - 🔵 **Picas** → dígitos correctos pero en la **posición equivocada**.  
     > Ejemplo: si el secreto es 5271 y escribes 1523 → el 1, 2 y 5 están, pero en otra posición → 3 picas.  

4. **Objetivo**  
   Sigue intentando hasta que logres **4 fijas** 🎉  
   ¡Ese día habrás descubierto el número secreto!  

5. **Historial**  
   Revisa tus jugadas para deducir el número secreto. se encuentra en la parte inferior.
6. **Monedas**  
   Cada vez que adivines el número secreto, ganas **1 moneda de mil Lore**
""")

col_left, col_right = st.columns([3, 1])
with col_left:
    guess = st.text_input("Tu jugada (4 dígitos):", value="0000", max_chars=4, help="Ejemplo: 0123")
with col_right:
    play = st.button("¡A jugar!")

# --- Métricas con placeholders (evita duplicados) ---
c1, c2, c3, c4 = st.columns(4)
picas_box  = c1.empty()
fijas_box  = c2.empty()
status_box = c3.empty()
coins_box  = c4.empty()

def render_header():
    """Dibuja una sola fila de cajas según el último estado."""
    if st.session_state.history:
        last = st.session_state.history[-1]
        picas_box.info(f"**Picas**\n\n{last['Picas']}")
        fijas_box.info(f"**Fijas**\n\n{last['Fijas']}")
        if st.session_state.status == "won":
            num = "".join(map(str, st.session_state.target))
            status_box.success(f"**¡GANASTE!** El número era: {num}")
        else:
            status_box.warning("**Sigue intentando**")
    else:
        picas_box.info("**Picas**\n\n0")
        fijas_box.info("**Fijas**\n\n0")
        status_box.success("**Listo para jugar**")

    # Monedas con simbolito
    coins_box.info(f"**Monedas** 🪙\n\n{st.session_state.coins}")

# Dibuja el encabezado al cargar
render_header()

# Process play (solo actualiza estado; NO pinta cajas aquí)
if play:
    if not valid_guess(guess):
        st.error("La jugada debe tener exactamente 4 dígitos (0–9).")
    else:
        g_digits = to_digits(guess)
        t_digits = st.session_state.target
        p = count_picas(g_digits, t_digits)
        f = count_fijas(g_digits, t_digits)

        st.session_state.history.append({"Jugada": guess, "Picas": p, "Fijas": f})

        # ¿Acertó?
        if guess == "".join(str(d) for d in t_digits):
            # Sumar moneda SOLO la primera vez que entra en estado 'won'
            if st.session_state.status != "won":
                st.session_state.coins += 1
            st.session_state.status = "won"
            st.success("¡Ganaste 1 🪙 moneda de oro!")
            st.balloons()
        else:
            st.session_state.status = "playing"

        # Re-dibuja con los nuevos valores
        render_header()

# Historial
if st.session_state.history:
    st.subheader("Historial de jugadas")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df, use_container_width=True, hide_index=True)

# Sidebar
with st.sidebar:
    st.header("Opciones")
    st.write(f"**Monedas acumuladas:** 🪙 {st.session_state.coins}")
    if st.toggle("Mostrar pista (revelar número)"):
        st.code("Número secreto: " + "".join(map(str, st.session_state.target)))

    # 🔊 Música de fondo
    st.subheader("🎵 Música de fondo")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("▶️ Reproducir música"):
            st.session_state.bgm_enabled = True   # gesto del usuario → habilita play
    with c2:
        if st.button("⏸️ Pausar"):
            st.session_state.bgm_enabled = False  # pausa

    vol_pct = st.slider("Volumen", 0, 100, int(st.session_state.bgm_volume*100))
    st.session_state.bgm_volume = vol_pct / 100.0

    if st.button("🔁 Reiniciar juego"):
        st.session_state.target = secret_number()
        st.session_state.history = []
        st.session_state.status = "ready"
        st.rerun()

    if st.button("🧹 Reiniciar monedas"):
        st.session_state.coins = 0
        st.info("Monedas reiniciadas a 0.")

# Activa/actualiza el audio si el usuario ya dio permiso (no se reinicia al interactuar)
render_bgm(MUSIC_PATH)

st.caption("Reglas: **Fijas** = dígitos correctos en la posición correcta. **Picas** = dígitos correctos en posición incorrecta.")
