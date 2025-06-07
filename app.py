import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from io import BytesIO

# Configuración inicial
st.set_page_config(page_title="Tendencias Google", layout="wide")
st.title("🔍 Analizador de Tendencias con Google Trends")

# Opciones de país
regiones = {
    "Chile": "CL",
    "Argentina": "AR",
    "Estados Unidos": "US",
    "España": "ES",
    "México": "MX"
}

# FECHA Y REGIÓN LADO A LADO ARRIBA
col_region, col_fecha = st.columns(2)
with col_region:
    region_nombre = st.selectbox("🌍 Elegí una región", list(regiones.keys()))
region = regiones[region_nombre]

with col_fecha:
    st.markdown("### 📅 Elegí el período de análisis")
    tipo_rango = st.radio("¿Querés un período predefinido o personalizado?", ["Predefinido", "Personalizado"])
    if tipo_rango == "Predefinido":
        opcion_periodo = st.selectbox("Seleccioná el período", ["Última semana", "Últimos 30 días", "Últimos 12 meses"])
        if opcion_periodo == "Última semana":
            fecha_inicio = datetime.today() - timedelta(days=7)
        elif opcion_periodo == "Últimos 30 días":
            fecha_inicio = datetime.today() - timedelta(days=30)
        else:
            fecha_inicio = datetime.today() - timedelta(days=365)
        fecha_fin = datetime.today()
    else:
        fecha_inicio = st.date_input("Desde", pd.to_datetime("2023-01-01"))
        fecha_fin = st.date_input("Hasta", pd.to_datetime("today"))
        if fecha_inicio >= fecha_fin:
            st.error("La fecha de inicio debe ser anterior a la de fin.")
            st.stop()

# INPUT PRODUCTOS (ABAJO DE FECHA Y REGIÓN)
productos_input = st.text_area("🛒 Ingresá los productos separados por coma", "aire acondicionado, estufa, ventilador")

# BOTÓN ANALIZAR (DESPUÉS DEL INPUT PRODUCTOS)
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

# Inicializamos sesión para guardar datos
if 'df' not in st.session_state:
    st.session_state.df = None

# FUNCIONES para recargar y analizar (por si querés modularizar)
def recargar():
    st.session_state.df = None
    st.rerun()


# SI HAY DATOS, MOSTRAR ANÁLISIS ARRIBA Y GRÁFICO AL FINAL
if st.session_state.df is not None:
    df = st.session_state.df
    fecha = datetime.now().strftime("%Y-%m-%d")

    # Análisis de tendencias organizado, arriba
    cambios = df.iloc[-1] - df.iloc[0]
    subida = cambios.idxmax()
    bajada = cambios.idxmin()
    picos = df.max().sort_values(ascending=False)

    st.subheader(f"📊 Análisis de Tendencias en {region_nombre}")

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

    # Explicación oculta
    with st.expander("❓ Cómo interpretar el gráfico"):
        st.write("""
        - Cada línea representa la evolución del interés de búsqueda relativo de un producto.
        - Los valores van de 0 a 100, donde 100 es el pico máximo de popularidad durante el período.
        - Cambios positivos significan que el interés subió, negativos que bajó.
        - Usá esta info para detectar tendencias y oportunidades.
        """)

    # GRÁFICO MÁS PEQUEÑO Y AL FINAL
    st.subheader(f"📈 Tendencias de búsqueda en {region_nombre}")
    fig, ax = plt.subplots(figsize=(10, 4))
    df.plot(ax=ax)
    ax.set_title(f"Tendencias - {region_nombre} - {fecha}")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Interés de búsqueda")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(title="Producto", loc='upper left')
    st.pyplot(fig)

    # BOTONES DESCARGA JUNTOS ABAJO
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        df_excel = df.rename(columns={col: f"Interés de búsqueda: {col}" for col in df.columns})
        df_excel = df_excel.reset_index()
        df_excel['date'] = df_excel['date'].dt.strftime('%Y-%m-%d')
        df_excel = df_excel.rename(columns={'date': 'Fecha'})
        fila_explicativa = {
            col: "Cada número representa el interés relativo (0-100)" if col != "Fecha" else "Fecha de la semana"
            for col in df_excel.columns
        }
        df_excel = pd.concat([pd.DataFrame([fila_explicativa]), df_excel], ignore_index=True)

        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_excel.to_excel(writer, index=False, sheet_name='Tendencias')
        excel_buffer.seek(0)

        st.download_button(
            "📄 Descargar Excel",
            data=excel_buffer,
            file_name=f"tendencias_{region}_{fecha}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with col_btn2:
        buffer = BytesIO()
        fig.savefig(buffer, format='png')
        buffer.seek(0)
        st.download_button("🖼️ Descargar Gráfico PNG", data=buffer, file_name=f"grafico_{region}_{fecha}.png", mime="image/png")

    # Botón recargar al lado de los botones de descarga
    if st.button("🔄 Recargar Datos"):
        recargar()
