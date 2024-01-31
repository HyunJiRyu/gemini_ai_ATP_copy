import streamlit as st
import pandas as pd
import datetime
from copy import deepcopy
import LLM_matzip
import subprocess
import deploy_maps
import streamlit.components.v1 as components
import time



def main() :

    # 이미지 삽입
    st.title(':blue[TRIPLAN] 🌐')
    st.write(":violet[당신의 여행 계획을 완벽하게 짜드립니다!]")


    travel_type_list = ['유명 관광지', '자연', '쇼핑', '먹부림']
    travel_type = st.multiselect('당신의 여행 스타일을 선택하세요. 복수 선택 가능합니다!', travel_type_list,placeholder="골라주세요~")
    llm_travel_type = deepcopy(travel_type)

    st.write('마이 타입:sunglasses: :')
    total_type = ""
    for i in range(len(travel_type)):
        if travel_type[i] == "유명 관광지":
            travel_type[i] = travel_type[i] + ":classical_building:"
        elif travel_type[i] == "자연":
            travel_type[i] = travel_type[i] + ":four_leaf_clover:"
        elif travel_type[i] == "쇼핑":
            travel_type[i] = travel_type[i] + ":shopping_bags:"
        elif travel_type[i] == "먹부림":
            travel_type[i] = travel_type[i] + ":meat_on_bone:"            
        total_type = total_type + "  " + travel_type[i]
    st.markdown(f'# {total_type}')

    f = open("country.txt","r")
    line = f.readline()
    f.close()

    line = line.replace(" ","")
    line = line.split(",")

    countries = line
    selected_country = st.selectbox("국가를 선택해 주세요!",countries,index=None,placeholder="국가를 선택해 주세요!")

    selected_country1 = ""

    if selected_country == "일본":
        selected_country1 = selected_country + ":flag-jp:"
    if selected_country == "미국":
        selected_country1 = selected_country + ":flag-us:"
    if selected_country == "영국":
        selected_country1 = selected_country + ":uk:"
    if selected_country == "캐나다":
        selected_country1 = selected_country + ":flag-ca:"
    

    st.write('마이 픽:sunglasses: :')
    st.markdown(f"# {selected_country1}")

    city = st.text_input('가고 싶은 도시를 입력하세요! 똑바로 입력 해주시지 않으면 ai 생성이 불가능해요!')

    st.write('마이 픽:sunglasses: :')
    st.markdown(f"# {city}")

    today = datetime.datetime.now()
    today = str(today).split(" ")
    today = today[0]

    today = str(today).split("-")
    today1 = int(today[1])
    today2 = int(today[2])
    today = datetime.datetime.now()
    next_year = today.year + 1

    jan_1 = datetime.date(today.year, today1,today2)
    dec_31 = datetime.date(next_year, 12, 31)

    date = st.date_input(
        "여행 날짜를 선택해주세요! :airplane_departure:",
        (jan_1, datetime.date(next_year, 1,1)),
        jan_1,
        dec_31,
        format="MM.DD.YYYY",   
    )

    if st.button('입력'):
        date_Departure = str(date[0])
        date_Arrival = str(date[1])
        date_day = date[1] - date[0]
        date_day = str(date_day).split(" ")

        with st.spinner('잠시만 기다려주세요! 지도 생성까지 최대 2분가량 소요됩니다!'):
            response,url_list,url = LLM_matzip.make_travel_plan(llm_travel_type,city,date_Arrival,date_Departure,int(date_day[0]))
            st.markdown("# :blue[일정을 보여드리겠습니다!]")
            st.write(response)
            st.markdown("# :blue[항공권 예약을 도와드릴 링크입니다!]")
            st.write(url)
            st.markdown("# :violet[참고 링크 입니다!]")
            st.write(url_list)
            selected_country_list = """
US 미국 
DE 독일 
IE 아일랜드
GB 영국
FR 프랑스
IT 이탈리아
SE 스웨덴
BR 브라질
CA 캐나다
JP 일본
SG 싱가폴
"""

            selected_country_list = selected_country_list.split("\n")
    
            country_codes = [word for word in selected_country_list if f"{selected_country}" in word]
    
            #print(country_codes)
    
            country_codes = str(country_codes[0]).split(" ")
    
            result = response.rsplit('\n')
    
            print(result)
    
            result = result[len(result)-1]
    
            if result == []:
                result = result[len(result)- 2]
    
            result = result.split("→")
    
            for i in result:
                i = i.replace(" ","")
                i = i.replace("*","")
                temp = city + " " + str(i)
                deploy_maps.place_list.append(temp)
    
            deploy_maps.country = country_codes[0]
    
            deploy_maps.deploy_maps_function()
    
            # embed streamlit docs in a streamlit app
    
            html = ""
    
            f = open("google_map.html","r")
            lines = f.readlines()
            for line in lines:
                html = html + line    
    
            components.html(html, width=640, height=640, scrolling=True)


if __name__ == "__main__" :
    main()
