
import pandas as pd
import duckdb
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from yellowbrick.cluster import KElbowVisualizer, SilhouetteVisualizer
from utils import get_lat_long, round_to_nearest_5

class Recommender():
    def __init__(self, data):
        self.scaler = StandardScaler()
        self.data = data
        self.cleaned_data = self.preprocess()
        self.kmeans = self.build_kmeans()
        self.visualizer_elbow = None
        self.k = None
        self.user_input = None
        self.recommended = None


    def clean(self):
        # month and year as int
        self.data['month'] = self.data['month'].astype(int)
        self.data['year'] = self.data['year'].astype(int)

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
        self.visualizer_elbow.show()
        # silhouette plot
        visualizer = SilhouetteVisualizer(self.kmeans, colors='yellowbrick')
        visualizer.fit(self.cleaned_data)
        visualizer.show()
        # pca plot
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(self.cleaned_data)

        cluster_names = ['cluster 1','cluster 2','cluster 3']
        # Plot
        plt.scatter(X_pca[:, 0], X_pca[:, 1], c=kmeans.labels_, cmap='viridis', s=50)
        # Create custom legend handles
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', label=cluster_names[i], 
                markerfacecolor=plt.cm.viridis(i / (len(cluster_names) - 1)), markersize=10)
            for i in range(len(cluster_names))
        ]
        # Add legend
        plt.legend(handles=legend_elements, title='Clusters', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.title('K-means Clustering with PCA')
        plt.xlabel('Principal Component 1')
        plt.ylabel('Principal Component 2')
        plt.show()

        # Explained variance ratio
        explained_variance_ratio = pca.explained_variance_ratio_
        print("Explained Variance Ratio per Component:", explained_variance_ratio)

        # Cumulative explained variance
        cumulative_explained_variance = explained_variance_ratio.cumsum()
        print("Cumulative Explained Variance:", cumulative_explained_variance)

        #loading 
        components = pca.components_
        # Rank features by importance for each component
        for i, component in enumerate(abs(components)):
            ranked_features = pd.Series(component, index=self.cleaned_data.columns).sort_values(ascending=False)
            print(f"Top Features for PC{i+1}:\n", ranked_features.head(5))


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
        recommendations = clusters_recc.sort_values(by='similarity', ascending=False)
        self.recommendations = self.data.loc[recommendations.index]
        return self.recommendations.head(top_n)
        

    def inspet_recommendations(self):

        # Calculate the correlation between each feature and the similarity score
        correlation_with_similarity = self.recommendations.corr()['similarity'].sort_values(ascending=False)
        correlation_with_similarity.drop('similarity', inplace=True)
        correlation_with_similarity.dropna(inplace=True)
        # Plot the correlation
        fig = px.bar(
            x=correlation_with_similarity.index,
            y=correlation_with_similarity.values,
            labels={'x': 'Features', 'y': 'Correlation with Similarity'},
            title='Correlation of Features with Cosine Similarity Score'
        )

        # Show the plot
        fig.show()


def main():
    
    table  = pd.read_csv('../data/utmb_data_clean.csv')
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
    print(recommendations)



if __name__ == '__main__':
    main()
