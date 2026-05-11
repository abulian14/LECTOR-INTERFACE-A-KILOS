import streamlit as st
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="Procesador de Remitos FRUTAPAC", page_icon="🍺", layout="wide")

st.title("🍺 Procesador de Remitos FRUTAPAC")
st.markdown("Subí el archivo TXT con los datos de los remitos y obtené el peso total por remito")

# ============================================================
# BASE DE DATOS DE PESOS (COMPLETA)
# ============================================================
pesos_dict = {
    1130001: 13.3, 1130015: 12.7, 1130016: 12.7, 1130017: 12.7, 1130018: 12.7,
    1133015: 12.7, 8880113: 3.6, 8880518: 1.9, 1140001: 13.3, 1140002: 13.3,
    1140003: 13.3, 1140015: 12.7, 1150006: 14.4, 1150008: 14.4, 1150010: 14.4,
    1150016: 12.7, 1150017: 12.7, 1150018: 13.1, 1150019: 13.1, 8880115: 2.7,
    8880117: 3.6, 8880502: 3.1, 8880512: 2.3, 8880513: 1.9, 1150100: 31.5,
    1230041: 13.4, 1230042: 13.4, 1230043: 13.4, 1230044: 13.4, 1230141: 12.2,
    1230142: 12.2, 1230144: 12.2, 1230143: 12.2, 1230026: 12.6, 1230027: 12.6,
    1230016: 11.2, 1230017: 11.2, 1230018: 11.2, 8880105: 1.5, 8880106: 1.5,
}

st.sidebar.success(f"✅ Base cargada: {len(pesos_dict)} productos")

# ============================================================
# FUNCIÓN PARA DECODIFICAR (sin librerías externas)
# ============================================================
def decodificar_archivo(bytes_archivo):
    """Intenta decodificar el archivo con diferentes codificaciones"""
    codificaciones = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in codificaciones:
        try:
            texto = bytes_archivo.decode(encoding)
            return texto, encoding
        except UnicodeDecodeError:
            continue
    
    # Si todas fallan, usar latin-1 que siempre funciona
    return bytes_archivo.decode('latin-1', errors='replace'), 'latin-1'

# ============================================================
# PROCESAR TXT REAL
# ============================================================
def procesar_txt(contenido):
    lineas = contenido.strip().split('\n')
    
    datos = []
    
    for linea in lineas:
        if not linea.strip() or 'ORIGEN' in linea:
            continue
        
        campos = linea.split(';')
        
        if len(campos) < 30:
            continue
        
        nro_remito = campos[1].strip() if len(campos) > 1 else ""
        fecha_raw = campos[2].strip() if len(campos) > 2 else ""
        cliente = campos[7].strip() if len(campos) > 7 else ""
        
        codigo_str = ""
        for campo in campos:
            if campo.strip().isdigit() and len(campo.strip()) == 7:
                codigo_str = campo.strip()
                break
        
        cantidad_str = ""
        for campo in campos:
            # Busca patrón como "0000009.00"
            if re.match(r'0{6}\d+\.\d{2}', campo.strip()):
                cantidad_str = campo.strip()
                break
        
        if not codigo_str or not cantidad_str:
            continue
        
        codigo = int(codigo_str)
        # Convierte "0000009.00" a 9.0
        cantidad = float(cantidad_str)
        
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
    
    # Agregar pesos
    df['peso_unitario'] = df['codigo'].map(pesos_dict).fillna(0)
    df['peso_total_item'] = df['cantidad'] * df['peso_unitario']
    
    # Detectar códigos sin peso
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
# INTERFAZ
# ============================================================
archivo_subido = st.file_uploader("📂 Seleccioná el archivo TXT", type=['txt'])

if archivo_subido is not None:
    archivo_bytes = archivo_subido.getvalue()
    contenido, encoding_usado = decodificar_archivo(archivo_bytes)
    
    st.info(f"📄 Codificación detectada: {encoding_usado}")
    
    with st.spinner("Procesando..."):
        resultado, sin_peso = procesar_txt(contenido)
    
    if resultado is not None and not resultado.empty:
        st.success(f"✅ Procesado! {len(resultado)} remitos encontrados")
        
        st.dataframe(resultado, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Remitos", len(resultado))
        col2.metric("Total Bultos", int(resultado['Total Bultos'].sum()))
        col3.metric("Peso Total", f"{resultado['Peso Total (kg)'].sum():.2f} kg")
        
        if sin_peso:
            st.warning(f"⚠️ Códigos sin peso en la base de datos: {sin_peso}")
        
        # Generar Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            resultado.to_excel(writer, sheet_name='Resumen por Remito', index=False)
        
        st.download_button(
            label="📥 Descargar Reporte Excel",
            data=output.getvalue(),
            file_name="reporte_remitos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error(f"❌ {sin_peso if sin_peso else 'No se encontraron datos válidos en el archivo'}")
