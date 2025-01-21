from geopy.geocoders import Nominatim

def round_to_nearest_5(x:float)->float:
    x:float = float(x)
    return round(x/5)*5

def get_lat_long(city:str)->tuple:
    geolocator = Nominatim(user_agent="utmb_pipeline",timeout=40)
    location = geolocator.geocode(city)
    return location.latitude, location.longitude