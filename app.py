import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from io import BytesIO

# ---------- CONFIG ----------
st.set_page_config(page_title="Tendencias Google", layout="wide")
st.markdown(
    """
    <style>

    /* Cambiar tamaño de fuente global */
    html, body, [class*="css"]  {
        font-size: 14px;
    }
    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 2rem;
        margin: auto;
    }
    textarea {
        max-height: 200px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🔍 Analizador de Tendencias con Google Trends")
st.markdown("Obtené una visualización rápida y clara de cómo evoluciona el interés por tus productos en distintas regiones del mundo. Ideal para detectar oportunidades de mercado. 🚀")

# ---------- REGIONES Y CATEGORÍAS ----------
regiones = {
    "Chile": "CL",
    "Argentina": "AR",
    "Estados Unidos": "US",
    "España": "ES",
    "México": "MX"
}

# ---------- REGIÓN ----------
st.markdown("### 🌍 Región")
region_nombre = st.selectbox("Seleccioná una región", list(regiones.keys()), index=0)
region = regiones[region_nombre]  # acá tomamos el código que necesita pytrends

# ---------- FILTRO DE FECHAS ----------
st.markdown("### 📅 Filtro de Fechas")
tipo_filtro = st.radio("Filtro de Fechas", ["Predefinido", "Personalizado"], horizontal=True)

if tipo_filtro == "Predefinido":
    col1, _ = st.columns([2, 1])  # para que no ocupe todo el ancho
    with col1:
        rango_predefinido = st.selectbox(
            "Rango de fechas",
            ["Última semana", "Últimas 4 semanas", "Últimos 3 meses", "Último año"],
            index=0
        )
    # Lógica para traducir selección a fechas
    hoy = pd.to_datetime("today")
    if rango_predefinido == "Última semana":
        fecha_inicio = hoy - pd.Timedelta(days=7)
    elif rango_predefinido == "Últimas 4 semanas":
        fecha_inicio = hoy - pd.Timedelta(weeks=4)
    elif rango_predefinido == "Últimos 3 meses":
        fecha_inicio = hoy - pd.DateOffset(months=3)
    else:  # Último año
        fecha_inicio = hoy - pd.DateOffset(years=1)
    fecha_fin = hoy

else:
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Desde", pd.to_datetime("2023-01-01"))
    with col2:
        fecha_fin = st.date_input("Hasta", pd.to_datetime("today"))

    if fecha_inicio >= fecha_fin:
        st.error("La fecha de inicio debe ser anterior a la de fin.")
        st.stop()

# ---------- RANGO MOSTRADO ----------
st.success(f"🔍 Rango seleccionado: {fecha_inicio.strftime('%d/%m/%Y')} hasta {fecha_fin.strftime('%d/%m/%Y')}")

# ---------- INPUT CENTRADO ----------
st.markdown("### 🛒 ¿Qué productos querés analizar?")
sugerencia = ", ".join(["iPhone 14", "Samsung Galaxy S23", "Xiaomi Redmi Note 11", "Motorola Moto G100", "Nokia 3310"])
with st.container():
    productos_input = st.text_area(
        "O Ingresá los productos separados por coma",
        value=sugerencia if sugerencia else "",
        height=120,
        key="productos_input"
    )


# ---------- BOTÓN DE ANÁLISIS ----------
if st.button("📊 Analizar Tendencias"):
    productos = [p.strip() for p in productos_input.split(",") if p.strip()]
    if not productos:
        st.warning("⚠️ Ingresá al menos un producto válido.")
    else:
        pytrends = TrendReq(hl='es-CL', tz=360)
        rango_fecha_str = f"{fecha_inicio.strftime('%Y-%m-%d')} {fecha_fin.strftime('%Y-%m-%d')}"
        pytrends.build_payload(kw_list=productos, geo=region, timeframe=rango_fecha_str)
        df = pytrends.interest_over_time()
        if df.empty or df.drop(columns=['isPartial']).sum().sum() == 0:
            st.error("❌ No se encontraron datos para esos productos en esta región.")
        else:
            df = df.drop(columns=['isPartial'])
            st.session_state.df = df

# ---------- ANÁLISIS ----------
def recargar():
    st.session_state.df = None
    st.experimental_rerun()

if 'df' not in st.session_state:
    st.session_state.df = None

if st.session_state.df is not None:
    df = st.session_state.df
    fecha = datetime.now().strftime("%Y-%m-%d")

    cambios = df.iloc[-1] - df.iloc[0]
    subida = cambios.idxmax()
    bajada = cambios.idxmin()
    picos = df.max().sort_values(ascending=False)

    st.subheader(f"📈 Análisis de Tendencias en {region_nombre}")

    col1, col2, col3 = st.columns([1, 2, 2])
    with col1:
        st.markdown(f"🔺 **Más subió:**")
        st.markdown(f"### {subida}")
        st.markdown(f"+{cambios[subida]:.0f}")
    with col2:
        st.markdown(f"🔻 **Más bajó:**")
        st.markdown(f"### {bajada}")
        st.markdown(f"{cambios[bajada]:.0f}")
    with col3:
        st.markdown("🏆 **Ranking por pico máximo**")
        for i, (producto, valor) in enumerate(picos.items(), start=1):
            st.markdown(f"{i}. **{producto}**: {valor}")

    with st.expander("❓ Cómo interpretar el gráfico"):
        st.write("""
        - Cada línea representa la evolución del interés de búsqueda relativo de un producto.
        - Los valores van de 0 a 100, donde 100 es el pico máximo de popularidad durante el período.
        - Cambios positivos significan que el interés subió, negativos que bajó.
        """)

    st.markdown("### 📊 Gráfico de Tendencias")
    fig, ax = plt.subplots(figsize=(10, 4))
    df.plot(ax=ax)
    ax.set_title(f"Tendencias - {region_nombre} - {fecha}")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Interés de búsqueda")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(title="Producto", loc='upper left')
    st.pyplot(fig)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        df_excel = df.rename(columns={col: f"Interés: {col}" for col in df.columns})
        df_excel = df_excel.reset_index()
        df_excel['date'] = df_excel['date'].dt.strftime('%Y-%m-%d')
        df_excel = df_excel.rename(columns={'date': 'Fecha'})
        fila_explicativa = {
            col: "Interés relativo (0-100)" if col != "Fecha" else "Fecha" for col in df_excel.columns
        }
        df_excel = pd.concat([pd.DataFrame([fila_explicativa]), df_excel], ignore_index=True)
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_excel.to_excel(writer, index=False, sheet_name='Tendencias')
        excel_buffer.seek(0)
        st.download_button("📄 Descargar Excel", data=excel_buffer, file_name=f"tendencias_{region}_{fecha}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with col_btn2:
        buffer = BytesIO()
        fig.savefig(buffer, format='png')
        buffer.seek(0)
        st.download_button("🖼️ Descargar Gráfico PNG", data=buffer, file_name=f"grafico_{region}_{fecha}.png", mime="image/png")

    if st.button("🔄 Recargar Datos"):
        recargar()
