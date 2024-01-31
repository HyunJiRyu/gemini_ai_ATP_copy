import requests
import asyncio
import aiohttp
import time
import json
from sc_google_maps_api import ScrapeitCloudClient
import deploy_maps
import aiofiles
from deploy_maps import country

async def parse_data(response_data, type, good_place):
  local_vectors = []
  for local in response_data["scrapingResult"]["locals"]:
    local_vect = []
    
    title = local.get("title", "")
    if title: local_vect.append(title)
    
    website = local.get("website", "")
    if website: local_vect.append(website)
      
    working_hours = local.get("workingHours", {})
    if working_hours:
      timezone = working_hours.get("timezone", "")
      days = working_hours.get("days", [])
      local_vect.append(timezone)
      local_vect.append(days)        
      
    #other fields
    rating = local.get("rating", "")
    if rating: 
      rating_val = float(rating)
      if rating_val < 2.0: 
        continue   #평점이 이것보다 작은거 거르기
      else: 
        local_vect.append(rating)
  
  
    reviews = local.get("reviews", "")
    if reviews:
      reviews_val = int(reviews)
      if reviews_val < 100: 
        continue    #리뷰수가 이것보다 작으면 거르기
      else: 
        local_vect.append(reviews)
      
    gps_coordinates = local.get("gpsCoordinates", {})
    latitude = gps_coordinates.get("latitude")
    longitude = gps_coordinates.get("longitude")
    if latitude is not None and longitude is not None:
      local_vect.append(latitude)
      local_vect.append(longitude)
      if type == 1:
        food_info_coordinates.append([latitude, longitude])
      else:
        stay_info_coordinates.append([latitude, longitude])
      
    #check if any of the files is undefined or null
    if title and rating is not None and reviews is not None:
      local_vect.extend([
        title, rating, reviews
      ])
      
    local_vectors.append(local_vect)
    if type == 1:  
      food_info_lists.append(local_vectors)
    else:
      stay_info_lists.append(local_vectors)
  #정보 txt파일로 저장
  if type == 1:
    output_filename = f"{good_place}_food_info.txt"
  else :
    output_filename = f"{good_place}_stay_info.txt"
    
  #각 장소의 상권 리스트 및 정보들을 파일 전달
  async with aiofiles.open(output_filename, 'w', encoding="utf-8") as output_file:
    for idx, local_vect in enumerate(local_vectors, start = 1):
      for item in local_vect:
        await output_file.write(f"  {item}\n")
      await output_file.write(f"\n")
  print(f"Parsed information saved to {output_filename}")
  
  #각 장소의 상권 좌표들 파일 전달
  if type == 1:
    async with aiofiles.open(f"{good_place}_food_coords.txt", 'w') as file:
      print(f"전달 전 식당 좌표수:", len(food_info_coordinates))
      print(f"전달 전 식당 정보수:", len(food_info_lists))    
      for coord in food_info_coordinates:
        await file.write(f"{coord[0]}, {coord[1]}\n")
      food_info_coordinates.clear()
      food_info_lists.clear()
  else:
    async with aiofiles.open(f"{good_place}_stay_coords.txt", 'w') as file:
      print(f"전달 전 숙소 좌표수:", len(stay_info_coordinates))
      print(f"전달 전 숙소 정보수:", len(stay_info_lists))    
      for coord in stay_info_coordinates:
        await file.write(f"{coord[0]}, {coord[1]}\n")
      stay_info_coordinates.clear()
      stay_info_lists.clear()
  
async def scrape(api_key, keyword, country, domain):
  start = time.time()
  client = ScrapeitCloudClient(api_key=api_key)
  response = client.scrape(
    params = {
      "country": country,
      "domain": domain,
      "keyword": keyword,
    }
  )
  print(response.status_code)
  end = time.time()
  print(f"소요시간: ", end - start)
  return json.loads(response.text)

async def main():
  api_key=''

  
  with open("place_list.txt", 'r') as file:
    place_list = [line.strip() for line in file]
  country = place_list[len(place_list)-1]
  place_list = place_list[:len(place_list)-1]
  print("craw")
  print(place_list)

  print(f"nation code:", country)

  for good_place in place_list:
    print(good_place,f"!!")

    
    
    #식당 정보
    keyword_food = f"{good_place}, food"
    food_data = await scrape(api_key, keyword_food, country, "com")
    print("parsing start")
    await parse_data(food_data, 1, good_place)

    #숙박 정보
    keyword_stay = f"{good_place}, stay"
    accomodation_data = await scrape(api_key, keyword_stay, country, "com")
    await parse_data(accomodation_data, 2, good_place)

if __name__ == "__main__":
  stay_info_lists = []        #전달할 상권 정보들
  stay_info_coordinates = []    #전달할 상권 좌표들
  food_info_lists = []
  food_info_coordinates = []
  asyncio.run(main())
