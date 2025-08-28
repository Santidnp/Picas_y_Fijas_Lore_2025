
import random
import streamlit as st
import pandas as pd

st.markdown("""
<style>
/* Reduce márgenes y mejora legibilidad en móviles */
@media (max-width: 640px) {
  .block-container { padding: 0.75rem 0.8rem; }
  label, .stTextInput label { font-size: 1rem !important; }
  input[type="text"], input[type="number"] { font-size: 1.05rem !important; }
  .stButton>button { width: 100% !important; padding: 0.8rem 1rem; font-size: 1rem; }
  .stDataFrame { height: 340px !important; }  /* evita scroll excesivo */
}

/* Opcional: “cards” más compactas */
div.stAlert { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)


st.set_page_config(page_title="Picas y Fijas", page_icon="🎯", layout="centered")

# -------------------------
# Helpers
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
    """A valid guess is exactly 4 digits (0-9). We accept repeated digits like the original R app did."""
    return len(s) == 4 and s.isdigit()

# -------------------------
# Session state
# -------------------------
if "target" not in st.session_state:
    st.session_state.target = secret_number()

if "history" not in st.session_state:
    st.session_state.history = []  # list of dicts: {"Jugada": "0123", "Picas": 1, "Fijas": 2}

if "status" not in st.session_state:
    st.session_state.status = "ready"  # "ready", "playing", "won"

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
""")


col_left, col_right = st.columns([3, 1])
with col_left:
    guess = st.text_input("Tu jugada (4 dígitos):", value="0000", max_chars=4, help="Ejemplo: 0123")
with col_right:
    play = st.button("¡A jugar!")

c1, c2, c3 = st.columns(3)
with c1:
    st.info("**Picas**\n\n0")
with c2:
    st.info("**Fijas**\n\n0")
with c3:
    if len(st.session_state.history) == 0:
        st.success("**Listo para jugar**")
    else:
        st.warning("**Sigue intentando**")

# Process play
if play:
    if not valid_guess(guess):
        st.error("La jugada debe tener exactamente 4 dígitos (0–9).")
    else:
        g_digits = to_digits(guess)
        t_digits = st.session_state.target
        p = count_picas(g_digits, t_digits)
        f = count_fijas(g_digits, t_digits)
        st.session_state.history.append({"Jugada": guess, "Picas": p, "Fijas": f})

        # Update headline boxes after play
        c1.info(f"**Picas**\n\n{p}")
        c2.info(f"**Fijas**\n\n{f}")

        if guess == "".join(str(d) for d in t_digits):
            st.session_state.status = "won"
            c3.success(f"**¡GANASTE!** El número era: {''.join(map(str, t_digits))}")
            st.balloons()
        elif guess == "0000" and len(st.session_state.history) == 1:
            c3.success("**Listo para jugar**")
        else:
            c3.warning("**Sigue intentando**")

# History table
if st.session_state.history:
    st.subheader("Historial de jugadas")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df, use_container_width=True, hide_index=True)

# Sidebar with controls
with st.sidebar:
    st.header("Opciones")
    if st.toggle("Mostrar pista (revelar número)"):
        st.code("Número secreto: " + "".join(map(str, st.session_state.target)))

    if st.button("🔁 Reiniciar juego"):
        st.session_state.target = secret_number()
        st.session_state.history = []
        st.session_state.status = "ready"
        st.rerun()

st.caption("Reglas: **Fijas** = dígitos correctos en la posición correcta. **Picas** = dígitos correctos en posición incorrecta.")
