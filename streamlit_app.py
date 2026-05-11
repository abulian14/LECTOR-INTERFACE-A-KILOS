import streamlit as st
import pandas as pd
from io import StringIO, BytesIO

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================
st.set_page_config(page_title="Procesador de Remitos FRUTAPAC", page_icon="🍺", layout="wide")

st.title("🍺 Procesador de Remitos FRUTAPAC")
st.markdown("Subí el archivo TXT con los datos de los remitos y obtené el peso total por remito")

# ============================================================
# CARGA DE LA BASE DE DATOS DE PESOS (incluida en la app)
# ============================================================
# NOTA: Tenés que copiar los pesos directamente acá para que la app funcione sola
# Esto es porque la app no puede leer archivos de tu computadora cuando está online

pesos_dict = {
    1130001: 13.3,    # 24 Botellas x 0,33 ml DAB
    1130015: 12.7,    # 24 Latas x 0,50 ml DAB
    1130016: 12.7,    # CERVEZA DAB DARK LATA 24 X 500CC
    1130017: 12.7,    # CERVEZA DAB MAIBOCK LATA 24 X 500CC
    1130018: 12.7,    # CERVEZA DAB RADLER LATA 24 X 500CC
    1133015: 12.7,    # JEVER PILSENER Lata 500cc x 24
    8880113: 3.6,     # ESTUCHE DAB 4 LATAS + CHOP
    8880518: 1.9,     # REEMPLAZO PARA DAB JARRA SEIDEL "DONAU"400cc x 6
    1140001: 13.3,    # 24 Botellas x 0,33 ml CLAUSTHALER
    1140002: 13.3,    # CLAUSTHALER LEMON botella 330 cm3
    1140003: 13.3,    # CLAUSTHALER UNFILTERED botella 330 cm3
    1140015: 12.7,    # CHAUSTHALER Original Lata Verde 24x500
    1150006: 14.4,    # 18 Botellas x 0,50 ml SCHOFFERHOFER
    1150008: 14.4,    # Cerveza Shofferhofer DUNKEL BT 3x6x500
    1150010: 14.4,    # 18 Botellas x 0.50 ml Cerv. Shoffer Kristal
    1150016: 12.7,    # 24 Latas x 0.50 ml SCHOFFERHOFER
    1150017: 12.7,    # SHOFFERHOFER POMELO LATA 500 cm3
    1150018: 13.1,    # SCHÖFFERHOFER PINEAPPLE Lata 500cc x 24
    1150019: 13.1,    # SH WATERMELON MINT LATA 500cc x 24
    8880115: 2.7,     # CAJA GIFT PACK x 3 SCOFFERHOFER
    8880117: 3.6,     # EST. SCHOFFER 4 LATAS LATAS + VASO 330
    8880502: 3.1,     # VASOS SCHOFFER x 500cc 6 unid.
    8880512: 2.3,     # VASOS SCHOFFER X 2 LTS
    8880513: 1.9,     # VASOS SCHOFFER 330 x 6
    1150100: 31.5,    # SCHOFFERHOFER BARRIL 30 LTROS NO RETORNABLE
    1230041: 13.4,    # KAISERDOM PILSENER LATA 1L x 12
    1230042: 13.4,    # KAISERDOM KELLERBIER 1L x 12
    1230043: 13.4,    # KAISERDOM DARK LAGER 1L x 12
    1230044: 13.4,    # KAISERDOM HEFE WEISSBIER 1L x 12
    1230141: 12.2,    # KAISERDOM Pilsener Lata 1 L + Jarra x 5
    1230142: 12.2,    # KAISERDOM Kellerbier Lata 1 L + Jarra x 5
    1230144: 12.2,    # KAISERDOM Weißbier Lata 1 L + Jarra x 5
    1230143: 12.2,    # KAISERDOM Dark Lager Lata 1 L + Jarra x 5
    1230026: 12.6,    # KAISERDOM Lemon mix 0,0% Lata 500 x 24
    1230027: 12.6,    # KAISERDOM Grapefruit mix 0,0% Lata 500cc x 24
    1230016: 11.2,    # KAISERDOM Strong Beer Lata 440cc x 24
    1230017: 11.2,    # KAISERDOM Smoked Beer Lata 440cc x 24
    1230018: 11.2,    # KAISERDOM IPA Lata 440cc x 24
    8880105: 1.5,     # POASAVASOS SH BULTO X 8 ROLLOS
    8880106: 1.5,     # POSAVASOS DAB BULTO X 8 ROLLOS
}

st.sidebar.success(f"✅ Base de datos cargada: {len(pesos_dict)} productos")

# ============================================================
# FUNCIÓN PARA LEER EL TXT
# ============================================================
def procesar_txt(contenido_txt):
    """Procesa el contenido del TXT y devuelve los resultados"""
    lineas = contenido_txt.split('\n')
    
    # Definir columnas según el formato
    columnas = [
        'ORIGEN', 'NUMERO DE REMITO', 'FECHA', 'FECHA2', 'NºCTE', 'NºCTE2', 'CUIT', 'CLIENTE',
        'DIRECCION1', 'VACIO1', 'CP', 'LOCALIDAD', 'DIRECCION2', 'ENTRE CALLES1', 'ENTRE CALLES2',
        'VACIO2', 'BARRIO', 'PEDIDO', 'FECHA3', 'VACIO3', 'VALOR DECLARADO', 'VACIO4', 'VACIO5',
        'VACIO6', 'VACIO7', 'VACIO8', 'VACIO9', 'VACIO10', 'VACIO11', 'CODIGO', 'VACIO12', 'VACIO13',
        'ARTICULO', 'VACIO14', 'VACIO15', 'CANTIDAD BULTOS', 'VACIO16', 'VACIO17', 'VACIO18',
        'VACIO19', 'VACIO20', 'VACIO21', 'FECHA4', 'VACIO22'
    ]
    
    datos = []
    for linea in lineas:
        if linea.strip() and 'ORIGEN' not in linea:
            partes = linea.split(';')
            if len(partes) >= len(columnas):
                fila = dict(zip(columnas, partes))
                if fila.get('CODIGO') and fila.get('CODIGO').strip():
                    datos.append(fila)
    
    if not datos:
        return None, "No se encontraron datos válidos en el archivo"
    
    df = pd.DataFrame(datos)
    
    # Convertir columnas
    df['CODIGO'] = pd.to_numeric(df['CODIGO'], errors='coerce')
    df['CANTIDAD BULTOS'] = pd.to_numeric(df['CANTIDAD BULTOS'], errors='coerce')
    df = df.dropna(subset=['CODIGO', 'CANTIDAD BULTOS'])
    
    # Agregar pesos
    df['PESO_UNITARIO'] = df['CODIGO'].map(pesos_dict)
    df['PESO_TOTAL_ITEM'] = df['CANTIDAD BULTOS'] * df['PESO_UNITARIO']
    
    # Identificar códigos faltantes
    faltantes = df[df['PESO_UNITARIO'].isna()]['CODIGO'].unique().tolist()
    
    # Limpiar fecha
    df['FECHA'] = df['FECHA'].apply(lambda x: f"{str(x)[6:8]}/{str(x)[4:6]}/{str(x)[0:4]}" if len(str(x)) == 8 else x)
    
    # Agrupar por remito
    resumen = df.groupby('NUMERO DE REMITO').agg({
        'CANTIDAD BULTOS': 'sum',
        'PESO_TOTAL_ITEM': 'sum',
        'FECHA': 'first',
        'CLIENTE': 'first'
    }).reset_index()
    
    resumen.columns = ['N° Remito', 'Total Bultos', 'Peso Total (kg)', 'Fecha', 'Cliente']
    resumen = resumen[['Fecha', 'N° Remito', 'Cliente', 'Total Bultos', 'Peso Total (kg)']]
    resumen['Peso Total (kg)'] = resumen['Peso Total (kg)'].round(2)
    
    return resumen, faltantes

# ============================================================
# INTERFAZ DE USUARIO
# ============================================================
with st.expander("📋 Instrucciones", expanded=True):
    st.markdown("""
    1. Copiá los datos del remito desde el sistema
    2. Pegalos en un archivo de texto (.txt)
    3. Subí el archivo usando el botón de abajo
    4. La app calcula automáticamente el peso total por remito
    """)

# Uploader de archivo [citation:6][citation:7]
archivo_subido = st.file_uploader("📂 Seleccioná el archivo TXT con los datos", type=['txt'])

if archivo_subido is not None:
    # Leer el contenido
    contenido = archivo_subido.getvalue().decode('utf-8')
    
    with st.spinner('Procesando archivo...'):
        resultado, faltantes = procesar_txt(contenido)
    
    if resultado is not None and not resultado.empty:
        st.success(f"✅ Procesado correctamente! {len(resultado)} remitos encontrados.")
        
        # Mostrar resultados
        st.subheader("📊 Resultados")
        st.dataframe(resultado, use_container_width=True)
        
        # Mostrar estadísticas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Remitos", len(resultado))
        with col2:
            st.metric("Total Bultos", int(resultado['Total Bultos'].sum()))
        with col3:
            st.metric("Peso Total", f"{resultado['Peso Total (kg)'].sum():.2f} kg")
        
        # Mostrar códigos faltantes si hay
        if faltantes:
            with st.expander("⚠️ Códigos no encontrados en la base de datos"):
                st.write(f"Los siguientes códigos no tienen peso asignado: {faltantes}")
                st.info("Agregalos a la base de datos para que el cálculo sea completo.")
        
        # Botón para descargar Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            resultado.to_excel(writer, sheet_name='Resumen por Remito', index=False)
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Descargar Reporte Excel",
            data=excel_data,
            file_name="reporte_remitos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error(f"❌ Error: {faltantes if faltantes else 'No se pudo procesar el archivo'}")
else:
    st.info("👆 Subí un archivo TXT para comenzar")

# Footer
st.markdown("---")
st.caption("Procesador de Remitos FRUTAPAC - Los archivos no se guardan en el servidor")
