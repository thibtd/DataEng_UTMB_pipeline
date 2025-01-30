
import pandas as pd
import duckdb
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from yellowbrick.cluster import KElbowVisualizer, SilhouetteVisualizer
from plugins.utils import get_lat_long, round_to_nearest_5
from sklearn.decomposition import PCA
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import plotly.express as px

class Recommender():
    def __init__(self, data):
        self.scaler = StandardScaler()
        self.data = data
        self.cleaned_data = self.preprocess()
        self.visualizer_elbow = None
        self.k = None
        self.kmeans = self.build_kmeans()
        self.user_input = None
        self.recommended = None
        self.explained_variance_ratio = None
        self.cumulative_explained_variance = None
        self.loadings = None


    def clean(self):
        # month, year as int
        self.data['month'] = self.data['month'].astype(int)
        self.data['year'] = self.data['year'].astype(int)
        
        # replace nan with 0 and convert to int 
        self.data['start_day'] = self.data['start_day'].replace(np.nan, 0)
        self.data['start_day'] = self.data['start_day'].astype(int)
        self.data['end_day'] = self.data['end_day'].replace(np.nan, 0)
        self.data['end_day'] = self.data['end_day'].astype(int)

        # replace nan with 0
        self.data['duration'] = self.data['duration'].fillna(0)
        self.data['multidays'] = self.data['multidays'].fillna(False)
        
    
    def preprocess(self):
        #clean the data 
        self.clean()
        data = self.data.copy()
        data  = data.drop(['start_day','end_day'],axis=1)
        numeric_columns = data.select_dtypes('number').columns
        numeric_columns = numeric_columns.drop(['latitude','longitude'])
        X_scaled = self.scaler.fit_transform(data[numeric_columns])
        data = data.drop(numeric_columns, axis=1)
        cleaned_data = pd.concat([data, pd.DataFrame(X_scaled, columns=numeric_columns)], axis=1)
        # remove variables 
        cleaned_data = cleaned_data.drop(['name','country','city','image','link','date_confirmed','style_UTMBWorldSeries'],axis=1)
        print(cleaned_data.columns)
        return cleaned_data
    
    def build_kmeans(self):
        # determine the number of clusters
        model = KMeans()
        self.visualizer_elbow = KElbowVisualizer(model, k=(1,12))
        self.visualizer_elbow.fit(self.cleaned_data)   
        self.k = self.visualizer_elbow.elbow_value_
        
        # run the model 
        kmeans = KMeans(n_clusters=self.k)
        kmeans = kmeans.fit(self.cleaned_data)
        kmeans.predict(self.cleaned_data)
        return kmeans
    
    def inspect_kmeans(self):
        # elbow plot
        fig, (ax1, ax2, ax3,ax4) = plt.subplots(1, 4, figsize=(20, 6))
        self.visualizer_elbow.finalize()
        self.visualizer_elbow.ax = ax1
        ax1.set_title("Elbow Plot")
       

        # silhouette plot
        silhouette_visualizer = SilhouetteVisualizer(self.kmeans, colors='yellowbrick', ax=ax2)
        print('silhouette',silhouette_visualizer.ax)
        silhouette_visualizer.fit(self.cleaned_data)
        silhouette_visualizer.finalize()
        ax2.set_title("Silhouette Plot")

        # PCA plot 
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(self.cleaned_data)
        scatter = ax3.scatter(
            X_pca[:, 0], X_pca[:, 1], c=self.kmeans.labels_, cmap="viridis", s=50
        )
        
        ax3.set_title("PCA Plot")
        ax3.set_xlabel("PC1")
        ax3.set_ylabel("PC2")
        
        # Add legend for PCA plot
        legend_labels = [f"Cluster {i}" for i in np.unique(self.kmeans.labels_)]
        ax3.legend(
            handles=scatter.legend_elements()[0],
            labels=legend_labels,
            title="Clusters",
            bbox_to_anchor=(1.05, 1),
            loc="upper left",
        )

        cluster_names = ['cluster 1','cluster 2','cluster 3']
        ax4.scatter(self.cleaned_data['longitude'],self.cleaned_data['latitude'], c=self.kmeans.labels_, cmap='viridis', s=50)
        ax4.scatter(self.kmeans.cluster_centers_[:, -4], self.kmeans.cluster_centers_[:, -5], c='red', s=200, alpha=0.7)
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', label=cluster_names[i], 
                markerfacecolor=plt.cm.viridis(i / (len(cluster_names) - 1)), markersize=10)
            for i in range(len(cluster_names))
        ]
        # Add legend
        ax4.legend(handles=legend_elements, title='Clusters', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax4.set_title('K-means clusters with their centroids')
        ax4.set_xlabel('longitude')
        ax4.set_ylabel('latitude')

        

        # Explained variance ratio
        self.explained_variance_ratio = pca.explained_variance_ratio_
        print("Explained Variance Ratio per Component:",  self.explained_variance_ratio)

        # Cumulative explained variance
        self.cumulative_explained_variance = self.explained_variance_ratio.cumsum()
        print("Cumulative Explained Variance:", self.cumulative_explained_variance)

        #loading 
        self.loadings = pca.components_
        # Rank features by importance for each component
        for i, component in enumerate(abs(self.loadings)):
            ranked_features = pd.Series(component, index=self.cleaned_data.columns).sort_values(ascending=False)
            print(f"Top Features for PC{i+1}:\n", ranked_features.head(5))
        
        return fig


    def process_input(self, preferences):

        min_dist, max_dist = preferences['distance']
        distance_list = [round_to_nearest_5(i) for i in range(min_dist, max_dist+1,5)]
        if 0 in distance_list:
            distance_list.remove(0)
            
        preferences['distance'] = distance_list
        # Convert list-type values into a flat dictionary
        flattened_prefs = {
            f"{key}_{value}": True for key, values in preferences.items() if isinstance(values, list) for value in values
        }

        # Include non-list values as they are except country
        flattened_prefs.update({key: value for key, value in preferences.items() if key !='country' and  not isinstance(value, list)})
        print(flattened_prefs)

        # Replace 'country' with latitude and longitude
        lat, lon = get_lat_long(preferences['country'])
        flattened_prefs["latitude"] = lat
        flattened_prefs["longitude"] = lon

        user_pref = pd.DataFrame(data = flattened_prefs, columns=self.cleaned_data.columns,index=[0])
        user_pref['year'] = user_pref['year'].astype(int)
        cat_columns = self.cleaned_data.select_dtypes(include=['bool']).columns
        numeric_columns = self.cleaned_data.select_dtypes(include=['number']).columns
        user_pref[cat_columns] = user_pref[cat_columns].fillna(False).astype(bool)
        user_pref[numeric_columns] = user_pref[numeric_columns].fillna(0).astype(int)
        numeric_columns = numeric_columns.drop(['latitude','longitude'])
        X_scaled = self.scaler.transform(user_pref[numeric_columns])
        user_pref = user_pref.drop(numeric_columns, axis=1)
        user_pref = pd.concat([user_pref, pd.DataFrame(X_scaled, columns=numeric_columns)], axis=1)
        
        return user_pref

    def recommend(self,user_input,top_n=5):
        
        self.user_input = self.process_input(user_input)
        distances = self.kmeans.transform(self.user_input)
        # Find the closest cluster
        closest_cluster = np.argmin(distances)
        data_recc = self.cleaned_data.copy()
        data_recc['cluster'] = self.kmeans.labels_ 
        clusters_recc = data_recc[data_recc['cluster'] == closest_cluster]
        clusters_recc = clusters_recc.drop('cluster', axis=1)

        # use cosine similarity to find the most similar event wihtin the cluster
        cosine_sim = cosine_similarity(self.user_input,clusters_recc)
        # Rank races by similarity
        clusters_recc['similarity'] = cosine_sim[0]
        self.recommended = clusters_recc.sort_values(by='similarity', ascending=False)
        recommendations= self.data.loc[self.recommended.index]
        return recommendations.head(top_n)
        

    def explain_recommendations(self):
        #data_recc = self.recommended.copy()
        #data_recc = data_recc.drop(['name','country','city','image','link'],axis=1)
        # Calculate the correlation between each feature and the similarity score
        correlation_with_similarity = self.recommended.corr()['similarity'].sort_values(ascending=False)
        correlation_with_similarity.drop('similarity', inplace=True)
        correlation_with_similarity.dropna(inplace=True)
        return correlation_with_similarity
    
    def plot_correlation(self,correlation_with_similarity):
        # Plot the correlation
        fig = px.bar(
            x=correlation_with_similarity.index,
            y=correlation_with_similarity.values,
            labels={'x': 'Features', 'y': 'Correlation with Similarity'},
            title='Correlation of Features with Cosine Similarity Score'
        )
        return fig 

        


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
    
    explanation = recommender.explain_recommendations()
    plot = recommender.plot_correlation(explanation)
    k_means_fig = recommender.inspect_kmeans()
    print(recommender.explained_variance_ratio)
    plt.show()
    plot.show()
    


if __name__ == '__main__':
    main()
