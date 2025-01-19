from geopy.geocoders import Nominatim

def round_to_nearest_5(x):
    x = float(x)
    return round(x/5)*5

def get_lat_long(city):
    geolocator = Nominatim(user_agent="utmb_pipeline")
    location = geolocator.geocode(city)
    return location.latitude, location.longitude