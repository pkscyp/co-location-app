import streamlit as st
import pandas as pd
import numpy as np
import folium 
import folium
from folium.plugins import MarkerCluster
import random
from sklearn.cluster import DBSCAN
import h3


kms_per_radian = 6371.0088

epsilon = 1.0*75/ (kms_per_radian*1000)


def handleFile(c1,fileName):
    df = pd.read_csv('./docdir/'+fileName,sep=',',names = ['asset_id','ts','lat','lon'],header=1)
    df = df.assign(lat=df.lat/10**7,lon = pd.to_numeric(df.lon)/10**7)
    #st.table(df.groupby('asset_id')['asset_id'].count())
    df = df.astype({'asset_id':str})
    df['radians'] = df[['lat','lon']].apply(lambda r : np.radians([r['lat'],r['lon']]),axis=1)
    
    db = DBSCAN(eps=epsilon, min_samples=2, metric='haversine').fit(df.radians.values.tolist())
    labels = db.labels_
    df['cluster_labels']= labels
    df = df[df.cluster_labels != -1]
    dfg = df.groupby('cluster_labels')['asset_id'].agg(['unique'])
    dfg['cosize'] =  dfg.unique.apply(lambda x : len(x))
    dfg = dfg[dfg.cosize > 1 ]
    c1.write(f'Number of Record :{df.size} No of colocation Found {dfg.size}')
    df = df[df.cluster_labels.isin(dfg.index)].sort_values('cluster_labels')

    dfr = df[['lat','lon','cluster_labels']].groupby('cluster_labels').agg(latitude=('lat','mean'),longitude=('lon','mean'))
    dfr.reset_index(drop=True,inplace=True)
    map_center = (df.lat.mean(),df.lon.mean())

    uqassets = set(df.asset_id.values.tolist())
    no_of_colors = len(uqassets)
    colors = ["#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
                for i in range(no_of_colors)]

    cluster_color = dict(zip(set(uqassets),colors))

    m = folium.Map(location=map_center, zoom_start=5)

    marker_cluster = MarkerCluster().add_to(m)

    for i,r in dfr.iterrows():
        folium.Circle(location=(r.latitude,r.longitude),radius=75).add_to(m)
        
    for idx,row in df[['asset_id','lat','lon','cluster_labels']].iterrows() :
        color = cluster_color.get(row.asset_id, 'gray')
        folium.CircleMarker(
                location=[row.lat, row.lon],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=f'Cluster {row.asset_id}' 
            ).add_to(marker_cluster)

    st.header("Offender Colocation", divider=True)
    st.components.v1.html(folium.Figure().add_child(m).render(), height=500)
    df = df.sort_values(['cluster_labels','asset_id','ts'])
    df = df.assign(cg=(df.asset_id != df.asset_id.shift()).ne(0).cumsum() )
    df['cellid'] = df[['lat','lon']].apply(lambda r: h3.latlng_to_cell(r.lat,r.lon,11),axis=1)
    df = df.groupby(['cluster_labels','asset_id','cg']).agg(
            asset_id=('asset_id','last'),
            start_time = ('ts','min'), 
            end_time=('ts','max'),
            latitude=('lat','mean'),
            longitude=('lon','mean'),
            no_of_point=('asset_id','count'),
            cellid=('cellid',lambda r: set(r.values)),
            cluster_labels=('cluster_labels','last')
            
    )
    df.reset_index(drop=True,inplace=True)
    df['coloc_id'] = None
    def setcoloc(r,df):
        df.loc[df.cluster_labels ==  r.name,['coloc_id']] =  [ set(r.values) for i in r.index]
        
    df.groupby('cluster_labels')['asset_id'].apply(lambda r:setcoloc(r,df))
    st.table(df)