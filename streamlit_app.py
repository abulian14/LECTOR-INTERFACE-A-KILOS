import streamlit as st
import pandas as pd
from io import BytesIO
import re
import requests

st.set_page_config(page_title="Procesador de Remitos FRUTAPAC", page_icon="🍺", layout="wide")

st.title("🍺 Procesador de Remitos FRUTAPAC")
st.markdown("Subí el archivo TXT con los datos de los remitos y obtené el peso total por remito")

# ============================================================
# URL DEL EXCEL EN GITHUB
# ============================================================
URL_EXCEL_GITHUB = "https://raw.githubusercontent.com/abulian14/lector-interface-excel/main/PESO%20X%20ARTICULOO.xlsx"

# ============================================================
# BASE DE DATOS DE PESOS POR DEFECTO
# ============================================================
PESOS_POR_DEFECTO = {
    1130001: 13.3, 1130015: 12.7, 1130016: 12.7, 1130017: 12.7, 1130018: 12.7,
    1133015: 12.7, 8880113: 3.6, 8880518: 1.9, 1140001: 13.3, 1140002: 13.3,
    1140003: 13.3, 1140015: 12.7, 1150006: 14.4, 1150008: 14.4, 1150010: 14.4,
    1150016: 12.7, 1150017: 12.7, 1150018: 13.1, 1150019: 13.1, 8880115: 2.7,
    8880117: 3.6, 8880502: 3.1, 8880512: 2.3, 8880513: 1.9, 1150100: 31.5,
    1230041: 13.4, 1230042: 13.4, 1230043: 13.4, 1230044: 13.4, 1230141: 12.2,
    1230142: 12.2, 1230144: 12.2, 1230143: 12.2, 1230026: 12.6, 1230027: 12.6,
    1230016: 11.2, 1230017: 11.2, 1230018: 11.2, 8880105: 1.5, 8880106: 1.5,
}

# ============================================================
# FUNCIÓN PARA CARGAR EXCEL DESDE GITHUB
# ============================================================
@st.cache_data(ttl=3600)
def cargar_pesos_desde_github():
    try:
        response = requests.get(URL_EXCEL_GITHUB)
        response.raise_for_status()
        
        with open("temp_pesos.xlsx", "wb") as f:
            f.write(response.content)
        
        df = pd.read_excel("temp_pesos.xlsx", sheet_name='Hoja2')
        df = df.dropna(how='all')
        
        encabezado_fila = None
        for i, row in df.iterrows():
            if row.astype(str).str.contains('CODIGO', case=False, na=False).any():
                encabezado_fila = i
                break
        
        if encabezado_fila is not None:
            df = pd.read_excel("temp_pesos.xlsx", sheet_name='Hoja2', header=encabezado_fila)
        
        col_codigo = None
        col_peso = None
        
        for col in df.columns:
            col_str = str(col).upper().strip()
            if 'CODIGO' in col_str or 'COD' in col_str:
                col_codigo = col
            if 'PESO' in col_str or 'KG' in col_str:
                col_peso = col
        
        if col_codigo is None or col_peso is None:
            return PESOS_POR_DEFECTO, f"⚠️ Columnas no encontradas: {df.columns.tolist()}"
        
        df[col_codigo] = pd.to_numeric(df[col_codigo], errors='coerce')
        df[col_peso] = pd.to_numeric(df[col_peso], errors='coerce')
        df = df.dropna(subset=[col_codigo, col_peso])
        
        pesos = dict(zip(df[col_codigo].astype(int), df[col_peso]))
        return pesos, f"✅ Cargados {len(pesos)} productos desde GitHub"
        
    except Exception as e:
        return PESOS_POR_DEFECTO, f"⚠️ Usando pesos por defecto. Error: {str(e)}"

# ============================================================
# FUNCIÓN PARA DECODIFICAR ARCHIVO
# ============================================================
def decodificar_archivo(bytes_archivo):
    codificaciones = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    for encoding in codificaciones:
        try:
            texto = bytes_archivo.decode(encoding)
            return texto, encoding
        except UnicodeDecodeError:
            continue
    return bytes_archivo.decode('latin-1', errors='replace'), 'latin-1'

# ============================================================
# PROCESAR TXT - VERSIÓN CORREGIDA
# ============================================================
def procesar_txt(contenido, pesos_dict):
    lineas = contenido.strip().split('\n')
    datos = []
    
    for linea in lineas:
        if not linea.strip() or 'ORIGEN' in linea:
            continue
        
        campos = linea.split(';')
        
        if len(campos) < 10:
            continue
        
        nro_remito = campos[1].strip() if len(campos) > 1 else ""
        fecha_raw = campos[2].strip() if len(campos) > 2 else ""
        cliente = campos[7].strip() if len(campos) > 7 else ""
        
        # Buscar código de 7 dígitos en TODA la línea (no solo en campos)
        codigo_match = re.search(r'\b(\d{7})\b', linea)
        if not codigo_match:
            continue
        codigo = int(codigo_match.group(1))
        
        # Buscar cantidad: patrón como 0000010.00 o 0000005.00
        cantidad_match = re.search(r'0{6}(\d+)\.(\d{2})', linea)
        if not cantidad_match:
            continue
        
        cantidad = float(f"{cantidad_match.group(1)}.{cantidad_match.group(2)}")
        
        # Convertir fecha YYYYMMDD a DD/MM/YYYY
        if len(fecha_raw) == 8 and fecha_raw.isdigit():
            fecha = f"{fecha_raw[6:8]}/{fecha_raw[4:6]}/{fecha_raw[0:4]}"
        else:
            fecha = fecha_raw
        
        datos.append({
            'remito': nro_remito,
            'fecha': fecha,
            'cliente': cliente,
            'codigo': codigo,
            'cantidad': cantidad
        })
    
    if not datos:
        return None, "No se encontraron datos válidos en el archivo"
    
    df = pd.DataFrame(datos)
    
    df['peso_unitario'] = df['codigo'].map(pesos_dict).fillna(0)
    df['peso_total_item'] = df['cantidad'] * df['peso_unitario']
    
    sin_peso = df[df['peso_unitario'] == 0]['codigo'].unique().tolist()
    
    # Agrupar por remito
    resumen = df.groupby('remito').agg({
        'cantidad': 'sum',
        'peso_total_item': 'sum',
        'fecha': 'first',
        'cliente': 'first'
    }).reset_index()
    
    resumen.columns = ['N° Remito', 'Total Bultos', 'Peso Total (kg)', 'Fecha', 'Cliente']
    resumen['Peso Total (kg)'] = resumen['Peso Total (kg)'].round(2)
    resumen = resumen[['Fecha', 'N° Remito', 'Cliente', 'Total Bultos', 'Peso Total (kg)']]
    
    return resumen, sin_peso

# ============================================================
# MAIN
# ============================================================
st.sidebar.header("📊 Base de Datos de Pesos")

with st.spinner("Cargando base de datos desde GitHub..."):
    pesos_dict, mensaje = cargar_pesos_desde_github()

st.sidebar.success(mensaje)
st.sidebar.info(f"📌 {len(pesos_dict)} productos disponibles")

# Mostrar últimos códigos cargados
with st.sidebar.expander("Ver códigos disponibles"):
    codigos_lista = sorted(list(pesos_dict.keys()))[:20]
    st.write(codigos_lista)

st.header("📄 Procesar Remitos")
archivo_subido = st.file_uploader("Seleccioná el archivo TXT con los remitos", type=['txt'])

if archivo_subido is not None:
    archivo_bytes = archivo_subido.getvalue()
    contenido, encoding_usado = decodificar_archivo(archivo_bytes)
    
    st.info(f"📄 Codificación detectada: {encoding_usado}")
    
    with st.spinner("Procesando..."):
        resultado, sin_peso = procesar_txt(contenido, pesos_dict)
    
    if resultado is not None and not resultado.empty:
        st.success(f"✅ Procesado! {len(resultado)} remitos encontrados")
        st.dataframe(resultado, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Remitos", len(resultado))
        col2.metric("Total Bultos", int(resultado['Total Bultos'].sum()))
        col3.metric("Peso Total", f"{resultado['Peso Total (kg)'].sum():.2f} kg")
        
        if sin_peso:
            st.warning(f"⚠️ Códigos sin peso en la base de datos: {sin_peso}")
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            resultado.to_excel(writer, sheet_name='Resumen por Remito', index=False)
        
        st.download_button(
            label="📥 Descargar Reporte Excel",
            data=output.getvalue(),
            file_name="reporte_remitos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Mostrar detalle de productos por remito (para depuración)
        with st.expander("📋 Ver detalle de productos procesados"):
            st.write("Productos encontrados en el archivo:")
            detalle_df = pd.DataFrame(datos)
            st.dataframe(detalle_df)
    else:
        st.error(f"❌ {sin_peso if sin_peso else 'No se encontraron datos válidos en el archivo'}")
