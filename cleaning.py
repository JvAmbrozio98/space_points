import pandas as pd 

df = pd.read_csv("points.csv")

df = df[~(  df['Placemark Name'] == 'Unnamed Placemark' )]
df = df[['Placemark Name','Latitude','Longitude' ]]
df.to_csv("output.csv",index=False)