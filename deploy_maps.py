import requests
import time
import folium
import webbrowser
import googlemaps
import os
from itertools import permutations
from geopy.distance import geodesic
import subprocess

#받아서 고쳐야하는거 : place_list, country

place_list = []
country = ""

def get_place_coordinates(api_key, place):
    base_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        'input': place,
        'inputtype': 'textquery',
        'fields': 'geometry',
        'key': api_key
    }

    print(place)

    response = requests.get(base_url, params=params)
    data = response.json()

    if response.status_code == 200 and data.get('candidates'):
        location = data['candidates'][0]['geometry']['location']
        print(location)
        return location['lat'], location['lng']
    else:
        print(f"Failed to retrieve coordinates for {place}")
        return None, None

def get_directions(api_key, origin, destination, country):
    gmaps = googlemaps.Client(key = api_key)
    
    if country == "JP":
        mode = "walking"
        print("Sorry, Japan does not provide transit informations. Instead, walking routes is drawn on the board.")
    elif country == "KR":
        print("Sorry, unable to show direction for South Korea.")
    else:
        print("processing...")
        mode = "transit"
    directions_result = gmaps.directions(origin, destination, mode = mode)
    return directions_result

def read_info(file_path):
    info_list = []
    current_info = []
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if line:
                current_info.append(line)
            else:
                if current_info:
                    info_list.append(current_info)
                    current_info = []
    if current_info:
        info_list.append(current_info)
    return info_list

def deploy_maps_function():
    
    start_location = place_list[0]       #예시
    reference_points = []       #각 장소의 좌표
    
    start_time = time.time()
    # GPT에서 받아온 명소 리스트들을 구글맵에 띄운다
    googlemap_api_key = ''

    marker_group = folium.FeatureGroup(name="Places")
    location_for_route = {}
    
    delete_will_list = []
    #장소 위에 핀 찍기
    for location_name in place_list:
        latitude, longitude = get_place_coordinates(googlemap_api_key, location_name)
        if latitude is not None and longitude is not None:
            target_location = (latitude, longitude)
            reference_points.append(target_location)
            location_for_route[location_name] = target_location
            popup_html = f"""
            <h2>{location_name}</h2>
            <a href="https://www.google.com/maps?q={location_name.replace(' ', '+')}" target="_blank">Open in Google Maps</a>
            """
            iframe = folium.IFrame(popup_html, width=300, height=150)
            marker = folium.Marker(location=target_location, popup=folium.Popup(iframe, max_width=500), 
                                   icon = folium.Icon(color="lightgreen"))
            marker_group.add_child(marker)
        else:
            print("Failed to find the location. Passing this part...")
            print(f"location name : {location_name}")
            delete_will_list.append(location_name)
            continue          

    for i in delete_will_list:
        place_list.remove(i)  
        
    print(place_list)
    with open("place_list.txt", 'w') as file:
        for place in place_list:
            file.write(f"{place}\n")
        file.write(f"{country}\n")
    google_map = folium.Map(location=location_for_route[start_location], zoom_start=15)
    google_map.add_child(marker_group)  # 구한 마커들을 지도에 추가

    # 두 지점 사이 최적 경로 찾아내기
    if len(place_list) > 1:
        for i in range(len(place_list) - 1):
            loc1 = place_list[i]
            loc2 = place_list[i+1]
            print(loc1)
            print(loc2)
            origin = location_for_route[loc1]
            destination = location_for_route[loc2]
            
            #구한 최적 경로들을 지도위에 그리기
            directions_result = get_directions(googlemap_api_key, origin, destination, country)
            if directions_result:
                steps = directions_result[0]['legs'][0]['steps']
                for step in steps:
                    try:
                        start_location = (step['start_location']['lat'], step['start_location']['lng'])
                        end_location = (step['end_location']['lat'], step['end_location']['lng'])
                        
                        polyline = folium.PolyLine(locations=[start_location, end_location], weight = 5, color='green')
                        google_map.add_child(polyline)
                    except Exception as e:
                        print(f"Error processing step: {e}")
    
    # 핀 꽃은 장소 주변 상권 표시하기
    subprocess.run(["python", "crawling_map.py"]) 
    current_dic = os.path.dirname(os.path.abspath(__file__))
    food_icon_path = os.path.join(current_dic, "food_icon.png")
    stay_icon_path = os.path.join(current_dic, "stay_icon.png")
    
    cnt = 0
    for i in place_list:
        #음식점
        food_list = read_info(f"{i}_food_info.txt")
        food_coordinates = [] 
        with open(f"{i}_food_coords.txt", 'r') as file:
            for line in file:
                lat, lng = map(float, line.strip().split(', '))
                food_coordinates.append([lat, lng])
            
        count = 0
        #받은 주변 음식점 좌표들 핀 찍기
        for c, s in zip(food_coordinates, food_list):
            distance = geodesic((c[0], c[1]), reference_points[cnt]).kilometers
            gmap_search_url = f"https://www.google.com/maps/search/?q={s[0].replace(' ', '+')}"
            popup_url = f"""
                <h3>{s[0]}</h3>
                <a href="{s[1]}" target="_blank">Visit Website!</a>
                <br>
                <a href="{gmap_search_url}" target="_blank">Open in Google Maps</a>
            """
            iframe = folium.IFrame(popup_url, width=300, height=150)
            if distance <= 1500:     #거리가 1km 이허인 것만
                count += 1
                folium.Marker(
                    location=[c[0], c[1]],
                    popup=folium.Popup(iframe, max_width=500),
                    icon=folium.CustomIcon(icon_image=food_icon_path, icon_size = (20, 20))
                ).add_to(google_map)
        print("Num of Marked Food places:", count)
        #숙박
        stay_list = read_info(f"{i}_stay_info.txt")
        stay_coordinates = []
        with open(f"{i}_stay_coords.txt", 'r') as file:
            for line in file:
                lat, lng = map(float, line.strip().split(', '))
                stay_coordinates.append([lat, lng])
                
        count = 0
        for c, s in zip(stay_coordinates, stay_list):
            distance = geodesic((c[0], c[1]), reference_points[cnt]).meters
            gmap_search_url = f"https://www.google.com/maps/search/?q={s[0].replace(' ', '+')}"
            popup_url = f"""
                <h3>{s[0]}</h3>
                <a href="{s[1]}" target="_blank">Visit Website!</a>
                <br>
                <a href="{gmap_search_url}" target="_blank">Open in Google Maps</a>
            """
            iframe = folium.IFrame(popup_url, width=300, height=150)
            if distance <= 1500:
                count += 1
                folium.Marker(
                    location=[c[0], c[1]],
                    popup=folium.Popup(iframe, max_width=500),
                    icon=folium.CustomIcon(icon_image=stay_icon_path, icon_size = (20, 20))
                ).add_to(google_map)
        cnt += 1
        print(f"Num of Marked stay places:", count)
    
    #지도 plot 
    html_file = "google_map.html"
    google_map.save(html_file)
    print("Custom Popup with Redirect Google Map HTML is created.")
    webbrowser.open(html_file, new=2)

    end_time = time.time()  
    print(f"time cost:", end_time - start_time, f"secs")  
