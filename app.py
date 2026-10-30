import inspect
import re
from itertools import product

import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------
# Datos del grupo
# ----------------------------------------------------------------------
GRUPO = 3
INTEGRANTES = [
    "Víctor Gabriel Abad Aguilar",
    "Andrés Mauricio Rizo Alvarado",
    "Maxwell Gabriel Espinoza Valle",
]

st.set_page_config(
    page_title=f"Calculadora Tabla de la Verdad - Grupo {GRUPO}",
    page_icon="🧮",
    layout="centered",
)

# Compatibilidad: versiones nuevas de Streamlit usan width="stretch"
if "width" in inspect.signature(st.button).parameters:
    STRETCH = {"width": "stretch"}
else:
    STRETCH = {"use_container_width": True}

# ----------------------------------------------------------------------
# Estilos
# ----------------------------------------------------------------------
st.markdown(
    """
    <style>
    .banner {
        background: linear-gradient(135deg, #0A3D7C 0%, #0B6DB7 55%, #1FB5E0 100%);
        padding: 1.6rem 1.4rem; border-radius: 16px; color: #fff;
        box-shadow: 0 6px 18px rgba(10, 61, 124, .35); margin-bottom: 1.2rem;
    }
    .banner h1 { color: #fff; margin: 0; padding: 0; font-size: 2rem; line-height: 1.2; }
    .banner p  { margin: .35rem 0 0 0; opacity: .92; font-size: .98rem; }
    .pill {
        display: inline-block; background: rgba(255,255,255,.2);
        border: 1px solid rgba(255,255,255,.5); border-radius: 999px;
        padding: .15rem .8rem; font-weight: 700; margin-right: .4rem;
    }
    .stButton > button { border-radius: 10px; font-weight: 600; }
    button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #0A3D7C 0%, #1FB5E0 100%);
        border: none; color: #fff;
    }
    button[data-testid="stBaseButton-primary"]:hover { filter: brightness(1.1); color: #fff; }
    .footer {
        margin-top: 2rem; padding: 1rem; text-align: center; font-size: .85rem;
        border-top: 2px solid rgba(31, 181, 224, .6); opacity: .8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="banner">
        <h1>🧮 Calculadora de Tabla de la Verdad</h1>
        <p><span class="pill">Grupo {GRUPO}</span>Estructuras Discretas · Universidad de Guayaquil</p>
        <p>👥 {" · ".join(INTEGRANTES)}</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    "Construye tu expresión haciendo clic. El resultado se mostrará **exclusivamente en 0 y 1**."
)

# ----------------------------------------------------------------------
# Estado de la sesión (la expresión se guarda como lista de tokens)
# ----------------------------------------------------------------------
if "tokens" not in st.session_state:
    st.session_state.tokens = []

SIMBOLOS = {"AND": "∧", "OR": "∨", "NOT": "¬", "XOR": "⊕", "->": "→", "<->": "↔"}


def agregar(token):
    st.session_state.tokens.append(token)


def limpiar():
    st.session_state.tokens = []


def borrar_ultimo():
    if st.session_state.tokens:
        st.session_state.tokens.pop()


def cargar(tokens):
    st.session_state.tokens = list(tokens)


def expr_texto():
    return " ".join(st.session_state.tokens)


def expr_bonita():
    return " ".join(SIMBOLOS.get(t, t) for t in st.session_state.tokens)


# ----------------------------------------------------------------------
# Ejemplos rápidos (leyes del informe)
# ----------------------------------------------------------------------
EJEMPLOS = {
    "De Morgan (∧)": "NOT ( P AND Q ) <-> NOT P OR NOT Q",
    "De Morgan (∨)": "NOT ( P OR Q ) <-> NOT P AND NOT Q",
    "Absorción": "P OR ( P AND Q ) <-> P",
    "Distributiva": "P AND ( Q OR R ) <-> ( P AND Q ) OR ( P AND R )",
    "Tercero excluido": "P OR NOT P",
    "Contradicción": "P AND NOT P",
}

with st.expander("📚 Ejemplos rápidos (leyes lógicas)"):
    ecols = st.columns(3)
    for i, (nombre, expr) in enumerate(EJEMPLOS.items()):
        with ecols[i % 3]:
            st.button(nombre, key=f"ej_{i}", on_click=cargar, args=(expr.split(),), **STRETCH)

# ----------------------------------------------------------------------
# UI: Constructor de Expresión
# ----------------------------------------------------------------------
st.subheader("🛠️ Constructor de Expresión")

variables = ["P", "Q", "R", "S", "T", "U"]
cols = st.columns(6)
for i, v in enumerate(variables):
    with cols[i]:
        st.button(v, key=f"btn_{v}", on_click=agregar, args=(v,), **STRETCH)

st.markdown("---")
st.subheader("➕ Operadores")

operadores = [
    ("AND", "∧  AND"), ("OR", "∨  OR"), ("NOT", "¬  NOT"), ("XOR", "⊕  XOR"),
    ("->", "→  Implica"), ("<->", "↔  Si y solo si"), ("(", "("), (")", ")"),
]
for fila in range(2):
    cols = st.columns(4)
    for j in range(4):
        op, etiqueta = operadores[fila * 4 + j]
        with cols[j]:
            st.button(etiqueta, key=f"btn_{op}", on_click=agregar, args=(op,), **STRETCH)

c1, c2 = st.columns(2)
with c1:
    st.button("🗑️ Limpiar", key="btn_limpiar", type="secondary", on_click=limpiar, **STRETCH)
with c2:
    st.button("⌫ Borrar último", key="btn_borrar", type="secondary", on_click=borrar_ultimo, **STRETCH)

st.code(expr_bonita() or "(vacío)", language="text")
st.caption("Precedencia: ¬, ∧, ⊕, ∨, →, ↔. Usa paréntesis cuando tengas dudas.")


# ----------------------------------------------------------------------
# Lógica Central
# ----------------------------------------------------------------------
def tokenizar(expr: str) -> list:
    e = expr.strip().upper()
    tokens = re.findall(r"<->|->|\(|\)|[A-Z]+|\S", e)
    validos = {"AND", "OR", "NOT", "XOR", "->", "<->", "(", ")"}
    for t in tokens:
        if t not in validos and not re.fullmatch(r"[A-Z]", t):
            raise ValueError(f"Token no válido: {t}")
    return tokens


def normalizar_expresion(expr: str) -> str:
    """Devuelve la expresión limpia (mayúsculas y espacios simples)."""
    return " ".join(tokenizar(expr))


def extraer_variables(expr: str) -> list:
    return sorted(set(re.findall(r"\b[A-Z]\b", expr.upper())))


def parsear(tokens: list):
    """Analizador sintáctico: devuelve un árbol de la expresión."""
    pos = [0]

    def ver():
        return tokens[pos[0]] if pos[0] < len(tokens) else None

    def tomar():
        t = ver()
        pos[0] += 1
        return t

    def bicondicional():
        nodo = implicacion()
        while ver() == "<->":
            tomar()
            nodo = ("bic", nodo, implicacion())
        return nodo

    def implicacion():
        nodo = disyuncion()
        if ver() == "->":
            tomar()
            return ("imp", nodo, implicacion())
        return nodo

    def disyuncion():
        nodo = xor()
        while ver() == "OR":
            tomar()
            nodo = ("or", nodo, xor())
        return nodo

    def xor():
        nodo = conjuncion()
        while ver() == "XOR":
            tomar()
            nodo = ("xor", nodo, conjuncion())
        return nodo

    def conjuncion():
        nodo = negacion()
        while ver() == "AND":
            tomar()
            nodo = ("and", nodo, negacion())
        return nodo

    def negacion():
        if ver() == "NOT":
            tomar()
            return ("not", negacion())
        return atomo()

    def atomo():
        t = tomar()
        if t == "(":
            nodo = bicondicional()
            if tomar() != ")":
                raise ValueError("Falta cerrar paréntesis")
            return nodo
        if t is not None and re.fullmatch(r"[A-Z]", t):
            return ("var", t)
        raise ValueError("Expresión incompleta")

    arbol = bicondicional()
    if pos[0] != len(tokens):
        raise ValueError("Sobran símbolos")
    return arbol


def evaluar(nodo, entorno: dict) -> bool:
    op = nodo[0]
    if op == "var":
        return entorno[nodo[1]]
    if op == "not":
        return not evaluar(nodo[1], entorno)
    a, b = evaluar(nodo[1], entorno), evaluar(nodo[2], entorno)
    if op == "and":
        return a and b
    if op == "or":
        return a or b
    if op == "xor":
        return a != b
    if op == "imp":
        return (not a) or b
    if op == "bic":
        return a == b
    raise ValueError("Operador desconocido")


def generar_tabla(expr_raw: str):
    if not expr_raw.strip():
        return [], []
    try:
        arbol = parsear(tokenizar(expr_raw))
    except ValueError:
        return [], []

    variables = extraer_variables(expr_raw)
    if not variables:
        return [], []

    tabla = []
    for valores in product([0, 1], repeat=len(variables)):
        entorno = {v: bool(val) for v, val in zip(variables, valores)}
        fila = list(valores) + [int(evaluar(arbol, entorno))]
        tabla.append(fila)
    return variables, tabla


def color_resultado(valor):
    if valor == 1:
        return "background-color: #1b8f4a; color: white; font-weight: 700; text-align: center"
    return "background-color: #c0392b; color: white; font-weight: 700; text-align: center"


# ----------------------------------------------------------------------
# Ejecución
# ----------------------------------------------------------------------
if st.button("🚀 Generar Tabla", key="btn_generar", type="primary", **STRETCH):
    if not st.session_state.tokens:
        st.warning("⚠️ Ingresa o construye una expresión primero.")
    else:
        vars, tabla = generar_tabla(expr_texto())

        if not vars:
            st.error("❌ Expresión inválida o sin variables detectadas.")
        else:
            cols_df = vars + ["Resultado"]
            df = pd.DataFrame(tabla, columns=cols_df)
            unos = int(df["Resultado"].sum())
            filas = len(df)
            ceros = filas - unos

            st.success(f"✅ Tabla generada para {len(vars)} variable(s)")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Variables", len(vars))
            m2.metric("Filas", filas)
            m3.metric("Unos (1)", unos)
            m4.metric("Ceros (0)", ceros)

            if unos == filas:
                st.success("🏆 **Tautología**: el resultado es 1 en todas las filas.")
                st.balloons()
            elif ceros == filas:
                st.error("🚫 **Contradicción**: el resultado es 0 en todas las filas.")
            else:
                st.info("🔀 **Contingencia**: el resultado depende de los valores de las variables.")

            estilo = df.style.map(color_resultado, subset=["Resultado"]) if hasattr(df.style, "map") \
                else df.style.applymap(color_resultado, subset=["Resultado"])
            estilo = estilo.set_properties(subset=vars, **{"text-align": "center"})
            st.dataframe(estilo, hide_index=True, **STRETCH)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Descargar CSV", csv, "tabla_verdad.csv", "text/csv")

# ----------------------------------------------------------------------
# Pie de página
# ----------------------------------------------------------------------
st.markdown(
    f"""
    <div class="footer">
        <b>Grupo {GRUPO}</b> · Estructuras Discretas<br>
        Facultad de Ciencias Matemáticas y Físicas · Universidad de Guayaquil · 2026
    </div>
    """,
    unsafe_allow_html=True,
)
