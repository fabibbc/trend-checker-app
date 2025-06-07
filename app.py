import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import io

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

region_nombre = st.selectbox("🌍 Elegí una región", list(regiones.keys()))
region = regiones[region_nombre]

# Ingreso de productos
productos_input = st.text_area("🛒 Ingresá los productos separados por coma", "aire acondicionado, estufa, ventilador")

# Botón principal
if st.button("📊 Analizar Tendencias"):
    productos = [p.strip() for p in productos_input.split(",") if p.strip()]

    if not productos:
        st.warning("⚠️ Ingresá al menos un producto válido.")
    else:
        pytrends = TrendReq(hl='es-CL', tz=360)
        pytrends.build_payload(kw_list=productos, geo=region)
        df = pytrends.interest_over_time()

        if df.empty or df.drop(columns=['isPartial']).sum().sum() == 0:
            st.error("❌ No se encontraron datos para esos productos en esta región.")
        else:
            df = df.drop(columns=['isPartial'])
            fecha = datetime.now().strftime("%Y-%m-%d")

            # Gráfico
            st.subheader(f"📈 Tendencias de búsqueda en {region_nombre}")
            fig, ax = plt.subplots(figsize=(12, 6))
            df.plot(ax=ax)
            ax.set_title(f"Tendencias - {region_nombre} - {fecha}")
            ax.set_xlabel("Fecha")
            ax.set_ylabel("Interés de búsqueda")
            ax.grid(True)
            ax.legend(title="Producto")
            st.pyplot(fig)

            # Botón de descarga CSV
            nombre_csv = f"tendencias_{region}_{fecha}.csv"
            csv_bytes = df.to_csv().encode('utf-8')
            st.download_button("⬇️ Descargar CSV", data=csv_bytes, file_name=nombre_csv, mime="text/csv")

            # Botón de descarga de imagen PNG
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png')
            buffer.seek(0)
            st.download_button("🖼️ Descargar Gráfico PNG", data=buffer, file_name=f"grafico_{region}_{fecha}.png", mime="image/png")

            # Análisis
            cambios = df.iloc[-1] - df.iloc[0]
            subida = cambios.idxmax()
            bajada = cambios.idxmin()
            st.subheader("📊 Análisis de Tendencias")
            st.markdown(f"🔺 Producto que **más subió**: `{subida}` (+{cambios[subida]})")
            st.markdown(f"🔻 Producto que **más bajó**: `{bajada}` ({cambios[bajada]})")

            # Ranking
            picos = df.max().sort_values(ascending=False)
            st.markdown("🏆 **Ranking por pico de interés máximo:**")
            for i, (producto, valor) in enumerate(picos.items(), start=1):
                st.markdown(f"{i}. **{producto}**: {valor}")
