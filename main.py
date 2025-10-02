import ee
import streamlit as st
import pandas as pd 
import tempfile
import os 
from google.oauth2.service_account import Credentials
#-48.6156, -23.1044
try:
    # Converte o dicionário de segredos em um objeto de credenciais
    creds_dict = st.secrets["gcp_service_account"]
    
    scopes = [
    'https://www.googleapis.com/auth/earthengine',
    'https://www.googleapis.com/auth/cloud-platform'
    ]
    credentials = Credentials.from_service_account_info(creds_dict,scopes=scopes)
    # Inicializa o Earth Engine com as credenciais da conta de serviço
    ee.Initialize(credentials=credentials)
    
except Exception as e:
    st.error(f"Falha ao autenticar com o Google Earth Engine: {e}")
    st.info("Verifique se as credenciais 'gcp_service_account' estão configuradas corretamente nos segredos do Streamlit.")
    st.stop()

def get_indices(longitude, latitude, raio, cidade, periodo_inicial, periodo_final):


    # Carregar coleção MODIS NDVI/EVI (MOD13Q1)
    MOD13Q1 = (
        ee.ImageCollection('MODIS/061/MOD13Q1')
        .filterDate(f'{periodo_inicial}', f'{periodo_final}')
        .filterBounds(ee.Geometry.Point(longitude, latitude))
    )

    SPL4SMGP =  (
        ee.ImageCollection('NASA/SMAP/SPL4SMGP/008')
        .filterDate(f'{periodo_inicial}', f'{periodo_final}')
        .filterBounds(ee.Geometry.Point(longitude, latitude))
    )

    MOD11A1 = ee.ImageCollection("MODIS/061/MOD11A1").filterDate(f'{periodo_inicial}', f'{periodo_final}') .filterBounds(ee.Geometry.Point(longitude, latitude))


    

    # Seleciona NDVI e EVI
    MOD13Q1_indices = MOD13Q1.select(['NDVI', 'EVI'])
    SPL4SMGP_indexes = SPL4SMGP.select(['leaf_area_index','sm_rootzone_pctl','sm_profile_pctl'])
    MOD11A1_indexes = MOD11A1.select('LST_Day_1km')
    # Estatísticas
    MOD13Q1_mean_indices = MOD13Q1_indices.mean().reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=ee.Geometry.Point(longitude, latitude).buffer(raio),
        scale=250
    )

    SPL4SMGP_mean_index = SPL4SMGP_indexes.mean().reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=ee.Geometry.Point(longitude, latitude).buffer(raio),
        scale=10000
    )

    MOD11A1_mean_index = MOD11A1_indexes.mean().reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=ee.Geometry.Point(longitude, latitude),
        scale=1000
    ).getInfo()


    
     

    # Recupera valores em Python
    MOD13Q1_results = MOD13Q1_mean_indices.getInfo()
    SPL4SMGP_results = SPL4SMGP_mean_index.getInfo()
  
    ndvi_mean = MOD13Q1_results.get('NDVI')
    evi_mean = MOD13Q1_results.get('EVI')
    leaf_area_index_mean = SPL4SMGP_results.get('leaf_area_index')
    sm_rootzone_pctl_mean = SPL4SMGP_results.get('sm_rootzone_pctl')
    sm_profile_pctl_mean = SPL4SMGP_results.get('sm_profile_pctl')
    LST_Day_1km_C = MOD11A1_mean_index.get('LST_Day_1km') * 0.02 - 273.15



    # Corrigir escala (valores MODIS vêm multiplicados por 10000)
    if ndvi_mean is not None:
        ndvi_mean = ndvi_mean * 0.0001
    if evi_mean is not None:
        evi_mean = evi_mean * 0.0001


    return {
        "cidade": cidade,
        "longitude":longitude,
        "latitude":latitude,
        "periodo_inicial": f"{periodo_inicial}",
        "periodo_final":f"{periodo_final}",
        "NDVI_medio": round(ndvi_mean, 4) if ndvi_mean else None,
        "EVI_medio": round(evi_mean, 4) if evi_mean else None,
        "LEAF_area_index_medio": leaf_area_index_mean if leaf_area_index_mean else None,
        "sm_rootzone_pctl_medio": sm_rootzone_pctl_mean if sm_rootzone_pctl_mean else None,
        "sm_profile_pctl_medio":sm_profile_pctl_mean,
        "LST_Day_1km":LST_Day_1km_C
    }





if 'consultas' not in st.session_state:
    st.session_state.consultas = []


st.set_page_config(layout='centered')
st.header('Geopoints Statistics')

with st.form("Entrada de coordenadas"):
    nome_do_tile = st.text_input(label='Digite o nome da regiao')
    longitude = st.number_input(label="Digite a longitude do ponto a ser analisado",step=0.0001,format="%.4f")
    latitude = st.number_input(label='Digite a latitude do ponto a ser analisado',step=0.0001,format="%.4f")
    raio = st.number_input(label="Digite o tamanho da circunferencia a ser criada ao redor do ponto")
    data_inicial = st.date_input(label="Digite a data inicial")
    data_final = st.date_input(label="Digite a  data final")
    info_user = {
        "name":nome_do_tile,
        "logitude":longitude,
        "latitude":latitude,
        "raio":raio,
        "data_inicial":data_inicial,
        "data_final":data_final
    }

    btn_send = st.form_submit_button('Verficar estatisticas')
    if btn_send:
        statistics = get_indices(longitude=info_user['logitude'],latitude=info_user['latitude'],raio=info_user['raio'],periodo_inicial=info_user['data_inicial'],periodo_final=info_user['data_final'],cidade=info_user['name'])
        st.session_state.consultas.append(statistics)


df = pd.DataFrame(st.session_state.consultas)



st.dataframe(df)
st.map(data=df,latitude='latitude',longitude='longitude')

col1,col2 = st.columns(2)

with col1:
    st.download_button(label="Baixar os arquvivos da pesquisa",data=df.to_csv(),file_name=f"Dados_teste.csv")
with col2:
    clear_btn = st.button(label="Limpar o dataset")
    if clear_btn:
        st.session_state.consultas = []