import pandas as pd 
from datetime import datetime, timedelta
import ee

ee.Initialize(project='ee-jvambrozio98')


def get_indices(longitude, latitude, raio, cidade, periodo_inicial, periodo_final):
    point = ee.Geometry.Point(longitude, latitude).buffer(raio)

    # Coleções
    MOD13Q1 = (
        ee.ImageCollection('MODIS/061/MOD13Q1')
        .filterDate(periodo_inicial, periodo_final)
        .filterBounds(point)
    )
    SPL4SMGP = (
        ee.ImageCollection('NASA/SMAP/SPL4SMGP/008')
        .filterDate(periodo_inicial, periodo_final)
        .filterBounds(point)
    )
    MOD11A1 = (
        ee.ImageCollection("MODIS/061/MOD11A1")
        .filterDate(periodo_inicial, periodo_final)
        .filterBounds(point)
    )

    # Seleção de bandas
    MOD13Q1_indices = MOD13Q1.select(['NDVI', 'EVI'])
    SPL4SMGP_indices = SPL4SMGP.select(['leaf_area_index', 'sm_rootzone_pctl', 'sm_profile_pctl'])
    MOD11A1_indices = MOD11A1.select('LST_Day_1km')

    # Estatísticas regionais
    MOD13Q1_mean = MOD13Q1_indices.mean().reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=250
    ).getInfo()

    SPL4SMGP_mean = SPL4SMGP_indices.mean().reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=10000
    ).getInfo()

    MOD11A1_mean = MOD11A1_indices.mean().reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=1000
    ).getInfo()

    # Recupera valores
    ndvi_mean = MOD13Q1_mean.get('NDVI')
    evi_mean = MOD13Q1_mean.get('EVI')
    lai_mean = SPL4SMGP_mean.get('leaf_area_index')
    sm_rootzone_mean = SPL4SMGP_mean.get('sm_rootzone_pctl')
    sm_profile_mean = SPL4SMGP_mean.get('sm_profile_pctl')
    lst_mean = MOD11A1_mean.get('LST_Day_1km')

    # Ajustes de escala
    if ndvi_mean is not None:
        ndvi_mean *= 0.0001
    if evi_mean is not None:
        evi_mean *= 0.0001
    if lst_mean is not None:
        lst_mean = lst_mean * 0.02 - 273.15

    # Retorno estruturado
    return {
        "cidade": cidade,
        "longitude": longitude,
        "latitude": latitude,
        "periodo_inicial": periodo_inicial,
        "periodo_final": periodo_final,
        "ndvi_medio": round(ndvi_mean, 4) if ndvi_mean is not None else None,
        "evi_medio": round(evi_mean, 4) if evi_mean is not None else None,
        "leaf_area_index_medio": lai_mean,
        "sm_rootzone_pctl_medio": sm_rootzone_mean,
        "sm_profile_pctl_medio": sm_profile_mean,
        "lst_day_1km_c": lst_mean
    }


def get_satelite_data(latitude,longitude,cidade):
    initial_start_date = datetime(2020,1,1)
    interval = timedelta(days=20)
    final_data = datetime(2024,12,30)
    fulldata = []
    raio = 2000

    while initial_start_date < final_data:
        end_data = initial_start_date + interval
        str_initial_start_date = initial_start_date.strftime('%Y-%m-%d')
        str_end_data = end_data.strftime('%Y-%m-%d')
        resultado = get_indices(latitude=latitude,longitude=longitude,cidade=cidade,raio=raio,periodo_inicial=str_initial_start_date,periodo_final=str_end_data)
        initial_start_date = end_data 
        fulldata.append(resultado)
        print(resultado)

    df = pd.DataFrame(fulldata)
    df.to_csv(f'{cidade}-lat:{latitude}long:{longitude}')



def formatar_coordenada_correto(coord_str):
    """
    Converte uma string como '-227999905' ou '-227.999.905'
    para o float -22.7999905.
    """
    s = str(coord_str)
    
    # 1. Remove todos os pontos e espaços da string
    numeros = s.replace('.', '').replace(' ', '')
    
    # Se não houver nada, retorna 0.0 para evitar erros
    if not numeros or numeros == '-':
        return 0.0
        
    # 2. Verifica se o número é negativo
    if numeros.startswith('-'):
        # Insere o ponto decimal após o terceiro caractere (depois do sinal e dos 2 dígitos)
        # Ex: '-227999905' -> '-22.7999905'
        string_correta = numeros[:3] + '.' + numeros[3:]
    else:
        # Insere o ponto decimal após o segundo caractere
        # Ex: '227999905' -> '22.7999905'
        string_correta = numeros[:2] + '.' + numeros[2:]
        
    return float(string_correta)




lista = pd.read_csv("output.csv")
lista = lista.rename(columns={"Placemark Name":"Cidade"})
lista['Latitude'] = lista['Latitude'].str.replace(r'[^\d-]', '', regex=True)
lista['Longitude'] = lista['Longitude'].str.replace(r'[^\d-]', '', regex=True)
lista['Latitude'] = lista['Latitude'].apply(formatar_coordenada_correto)
lista['Longitude'] = lista['Longitude'].apply(formatar_coordenada_correto)
print(lista)
for row in lista.itertuples():
    get_satelite_data(row.Latitude,row.Longitude,row.Cidade)


