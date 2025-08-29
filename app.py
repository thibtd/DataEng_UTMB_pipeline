import streamlit as st
import pandas as pd
import duckdb
from plugins.recommender import Recommender
from datetime import datetime
import folium
from plugins.utils import get_offered_X
import plotly.express as px
from streamlit_folium import st_folium



def plot_to_map(df:pd.DataFrame,clustered:bool, kmeans,colors:list=['red','green','blue'],zoom = 2)->folium.Map:

    s = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=zoom)
    for i in range(df.shape[0]):
        cluster = 0 
        color = 'red'
        if clustered:
            cluster = kmeans.labels_[i]
            color = colors[cluster]
        offered_distances = get_offered_X(row = df.iloc[i],prefix= 'distance')
        offered_styles = get_offered_X(row= df.iloc[i],prefix= 'style')
        name = df['name'][i]
        image = df['image'][i]
        country = df['country'][i]
        city = df['city'][i]
        link = df['link'][i]
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
            <a href={link} target="_blank" >More information</a>
        </div>
        """ 
        folium.Marker([df['latitude'][i], df['longitude'][i]], popup=html,icon=folium.Icon(color=color)).add_to(s)
    return s


def main(): 
    table  = pd.read_csv('data/utmb_data_clean.csv')
    preferences = {
        'distance':[20,80],
        'style':[],
        'month':6,
        "year":2025,
        'country':"Austria",
        'disipline':['Trail']
    }
    recommender = Recommender(table)
    recommendations = recommender.recommend(preferences)

    plot_map = plot_to_map(recommender.data,clustered=True, kmeans=recommender.kmeans)
    plot_map.show_in_browser()


@st.cache_data
def load_data():
    conn = duckdb.connect('data/utmb_db.duckdb')
    data = conn.sql("select * from UTMB").df()
    return data

def overview(data:pd.DataFrame) -> str:
    number_of_events =data.shape[0]
    number_of_countries = data['country'].nunique()
    number_of_cities = data['city'].nunique()
    return f'Over the year, there are {number_of_events} events in {number_of_cities} cities from {number_of_countries} different countries.'




def streamlit_app():
    st.set_page_config(page_title='🏃‍♂️ UTMB Recommender', page_icon='🏃‍♂️', layout='wide', initial_sidebar_state='auto')
    st.title('Ultra Trail World Series Recommender')
    st.write('This app is a recommender system for ultra races that are part of the UTMB World Series.')
    #  load data and cash the data 
    data = load_data()
    print(data.head())
    print(data.columns)
    recommender = Recommender(data)
    # get all the different variables required to be displayed 
    list_of_styles = sorted([col.replace('style_', '') for col in recommender.data.columns if col.startswith('style_')])
    #list_of_styles.remove('') # remove the empty string
    list_of_distances = [int(col.replace('distance_', '')) for col in recommender.data.columns if col.startswith('distance_')]
    list_of_disciplines = [col.replace('discipline_', '') for col in recommender.data.columns if col.startswith('discipline_')]
    list_of_countries = sorted(data['country'].unique())
    list_of_cities = sorted(data['city'].unique())


    #st.dataframe(data)
    tab1, tab2 = st.tabs(["Overview of the Races", "Get recommendations"])

    with tab1:
        st.write(overview(data))
        #distribution of the events by country
        country_distribution = data['country'].value_counts()
        fig = px.bar(x = country_distribution.index, y= country_distribution.values, labels={'x':'Country','y':'Number of events'})
        fig.layout.update(title='Distribution of the events by country')
        st.plotly_chart(fig)

        #distribution of the events over the year (months)
        month_distribution = data['month'].value_counts()
        fig = px.bar(x = month_distribution.index, y= month_distribution.values, labels={'x':'Month','y':'Number of events'})
        fig.layout.update(title='Distribution of the events over the year (months)')
        st.plotly_chart(fig)

        #recommendations = recommender.recommend(preferences)
        plot_map = plot_to_map(recommender.data,clustered=True, kmeans=recommender.kmeans)
        map_st = st_folium(plot_map, width=1300, height=700, returned_objects=[])

    with tab2:
        st.header('Enter your preferences')
        st.write('Please fill the following information to get recommendations')
        preferences = {}
        col1,col2 = st.columns(2)
        with col1:

            preferences['distance'] = st.slider('How long do you want to run for?', min_value=min(list_of_distances), max_value=max(list_of_distances), value=(20,80))
            preferences['style'] = st.multiselect("Waht style are you interested in?",list_of_styles)
            preferences['discipline'] = st.multiselect("What discipline are you interested in?",list_of_disciplines)
            multidays= st.selectbox('Are you interested in multi-days events?',['yes','no','indifferent'],index=2)
        
        with col2: 
            pref_date = st.date_input('When are you planning to run?',format='DD-MM-YYYY',value=None)
            if pref_date:
                preferences['month'] = pref_date.month
                preferences['year'] = pref_date.year
            country_select= st.selectbox('Where would you like to run?', list_of_countries,index=0)
            city_select = st.selectbox('Where would you like to run?', list_of_cities,index=None)
            top_k = st.slider('How many recommendations do you want?', min_value=1, max_value=10, value=5)
    
        map_to_multidays = {'yes':True,'no':False,'indifferent':''}
        preferences['multidays'] = map_to_multidays[multidays]
        preferences['country'] = country_select if country_select else ''
        preferences['city'] = city_select if city_select else ''
        

        st.header("Based on your preferences, here are the recommendations:")

        recommendations = recommender.recommend(preferences, top_n=top_k).reset_index()
        months = {1:'January',2:'February',3:'March',4:'April',5:'May',6:'June',7:'July',8:'August',9:'September',10:'October',11:'November',12:'December'}

        data_recc = pd.DataFrame(data = recommendations, columns = ['image','name','city','country','month','year','link'])
        data_recc['month'] = data_recc['month'].map(months)
        st.data_editor(data_recc, column_config={
            "image": st.column_config.ImageColumn(
                "Preview Image", help="Race vignette"
            ),
            "link": st.column_config.LinkColumn("More information", help="Link to the event website",display_text="More information")
            },
            hide_index=True,
        )
        

        plot_map_rec = plot_to_map(recommendations.reset_index(),clustered=False, kmeans=None,zoom=4)
        map_rec = st_folium(plot_map_rec, width=1300, height=700, returned_objects=[])

        explanation = recommender.explain_recommendations()
        plot = recommender.plot_correlation(explanation)
        st.plotly_chart(plot)
        





if __name__ == '__main__':
    streamlit_app()
