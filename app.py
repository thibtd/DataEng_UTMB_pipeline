import streamlit as st
import pandas as pd
import duckdb
from plugins.recommender import Recommender
from datetime import datetime, timedelta
import folium
from plugins.utils import get_offered_X


def plot_to_map(df:pd.DataFrame,clustered:bool, kmeans,colors:list=['red','green','blue'])->folium.Map:

    s = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=2)
    for i in range(df.shape[0]):
        cluster = 0 
        color = 'red'
        if clustered:
            print(kmeans.labels_[i])
            cluster = kmeans.labels_[i]
            color = colors[cluster]
        print(color)
        offered_distances = get_offered_X(row = df.iloc[i],prefix= 'distance')
        offered_styles = get_offered_X(row= df.iloc[i],prefix= 'style')
        name = df['name'][i]
        image = df['image'][i]
        country = df['country'][i]
        city = df['city'][i]
        if df['start_day'][i] != 0:
            start_date = datetime(df['year'][i], df['month'][i], df['start_day'][i]).strftime('%Y-%m-%d')
        else:
            start_date = datetime(df['year'][i], df['month'][i],1).strftime('%Y-%m')
            start_date+=' day to be defined'
        if df['multidays'][i]:
            duration = df['duration'][i]
            if df['end_day'][i] != 0:
                end_date= datetime(df['year'][i], df['month'][i], df['end_day'][i]).strftime('%Y-%m-%d')
            else:
                pass
            dates_str=f'<p style="margin: 0; font-size: 14px; color: #555;"><strong>Dates:</strong> From {start_date} to {end_date} ({int(duration)} days)</p'
        else:
            dates_str=f'<p style="margin: 0; font-size: 14px; color: #555;"><strong>Date:</strong> {start_date}</p>'

        html = f"""
        <div style="font-family: Arial, sans-serif; width: 400px;">
            <h3 style="margin: 0; padding: 0; font-size: 18px; color: #333;">{name}</h3>
            <hr style="margin: 5px 0; border: 0; border-top: 1px solid #ccc;">
            <img src="{image}" alt="image" style="width: 60%; height: auto; border-radius: 5px; margin-bottom: 10px;">
            <p style="margin: 0; font-size: 14px; color: #555;"><strong>Distances:</strong> {offered_distances} km</p>
            <p style="margin: 0; font-size: 14px; color: #555;"><strong>Type of race:</strong> {offered_styles}</p> 
            <p style="margin: 0; font-size: 14px; color: #555;"><strong>Location:</strong> {city} ({country})</p> 
            {dates_str}
        </div>
        """ 
        folium.Marker([df['latitude'][i], df['longitude'][i]], popup=html,icon=folium.Icon(color=color)).add_to(s)
    return s


def main(): 
    table  = pd.read_csv('data/utmb_data_clean.csv')
    preferences = {
        'distance':[20,80],
        'style':["Mountain","Forest",'Stages'],
        'month':6,
        "year":2025,
        'country':"Austria",
        'multidays':True,
        'disipline':['Trail']
    }
    recommender = Recommender(table)
    recommendations = recommender.recommend(preferences)

    plot_map = plot_to_map(recommender.data,clustered=True, kmeans=recommender.kmeans)
    plot_map.show_in_browser()

if __name__ == '__main__':
    main()
