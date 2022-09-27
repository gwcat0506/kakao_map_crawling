import os
import re
import csv
import pandas as pd
from time import sleep
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import StaleElementReferenceException
from bs4 import BeautifulSoup


options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('lang=ko_KR')
chromedriver_path = "./chromedriver"
driver = webdriver.Chrome(os.path.join(os.getcwd(), chromedriver_path), options=options)  # chromedriver 열기



def main():
    
    global driver, load_wb, review_num

    driver.implicitly_wait(4)  # 렌더링 될때까지 기다린다 4초
    driver.get('https://map.kakao.com/')  # 주소 가져오기

    # 검색할 목록
    # place_infos = ['연남동 애견동반']
    place_name = '연남동'
    search(place_name)
    
    driver.quit()
    print("finish")


def search(place):
    global driver

    search_area = driver.find_element(By.XPATH, r'//*[@id="search.keyword.query"]') # 검색창
    search_area.send_keys(place)  # 검색어 입력
    
    driver.find_element(By.XPATH, r'//*[@id="search.keyword.submit"]').send_keys(Keys.ENTER)
    sleep(1)
    
    # 검색된 정보가 있는 경우에만 탐색
    # 1번 페이지 place list 읽기
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    place_lists = soup.select('.placelist > .PlaceItem') # 검색된 장소 목록
    print(place_lists)
    
    # 검색된 첫 페이지 장소 목록 크롤링하기
    crawling(place, place_lists)
    search_area.clear()
    
    
    # 우선 더보기 클릭해서 2페이지
    try:
        driver.find_element(By.XPATH, r'//*[@id="info.search.place.more"]').send_keys(Keys.ENTER)
        sleep(1)

        # 2~ 페이지 읽기
        for i in range(6, 16):
            if i%5==1:
                driver.find_element(By.XPATH, r'//*[@id="info.search.page.next"]').send_keys(Keys.ENTER)
                # 검색된 첫 페이지 장소 목록 크롤링하기
                sleep(2)
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                place_lists = soup.select('.placelist > .PlaceItem') # 장소 목록 list
                
                crawling(place, place_lists)
                search_area.clear()
                sleep(2)
            else:
                
                # 페이지 넘기기
                if i%5==0:
                    xPath = '//*[@id="info.search.page.no' + str(5) + '"]'
                else:
                    xPath = '//*[@id="info.search.page.no' + str(i%5) + '"]'
                
                driver.find_element(By.XPATH, xPath).send_keys(Keys.ENTER)

                sleep(2)

                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                place_lists = soup.select('.placelist > .PlaceItem') # 장소 목록 list

                crawling(place, place_lists)

    except ElementNotInteractableException:
        print('not found')
    finally:
        search_area.clear()
    
    
def crawling(place, place_lists):
    
    for i, place in enumerate(place_lists):
        
        k=0
        print(i,"번째 가게 탐색")
        place_name = place.select('.head_item > .tit_name > .link_name')[0].text  # place name
        place_address = place.select('.info_item > .addr > p')[0].text  # place address
        
        print(place_name,place_address)
        if i==3:
            print('-------------광고 넘김---------------')      
            k=1

        detail_page_xpath = '//*[@id="info.search.place.list"]/li[' + str(k+i + 1) + ']/div[5]/div[4]/a[1]'
            
        driver.find_element(By.XPATH, detail_page_xpath).send_keys(Keys.ENTER)
        driver.switch_to.window(driver.window_handles[-1])  # 상세정보 탭으로 변환
        sleep(2)
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        try:
            all_review_num_text = soup.find(attrs = {'class':'total_evaluation'}).text
            all_review_num = int(re.sub(r'[^0-9]', '', all_review_num_text))
            print(all_review_num)
        except:
            # 매장주 요청으로 후기가 제공되지 않는 장소입니다 
            driver.close()
            driver.switch_to.window(driver.window_handles[0]) 
            continue
        
        # 리뷰 전체 다 볼 수 있도록 리뷰 더보기 버튼 클릭 
        if int(all_review_num) > 3:
            for j in range((int(all_review_num)-3)//5+1):
                sleep(0.5)
                driver.execute_script('document.querySelector("#mArticle > div.cont_evaluation > div.evaluation_review > a").click();')
                print('리뷰 더보기')
        
        sleep(2)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        list_star = []
        list_review = []
        list_place_name = []
        list_place_address = []
        
        # 리뷰 목록 찾기
        review_lists = soup.select('.list_evaluation > li')
        print(len(review_lists))
        # 리뷰가 있는 경우 들고오기
        
        
        
        if len(review_lists) != 0:
            for i, review in enumerate(review_lists):

                # 별점과 리뷰 구하기
                star_text = review.find(attrs = {'class':'ico_star inner_star'}) 
                star_text = str(star_text)
                star = int(re.sub(r'[^0-9]', '', star_text))/20
                # print(star)
                rating = review.select('.grade_star size_s') # 별점
                comment = review.select('.txt_comment > span')[0].text # 리뷰
                
                # print(i+1,star)
                # print(i+1,comment)

                list_place_name.append(place_name)
                list_place_address.append(place_address)
                list_star.append(star)
                list_review.append(comment)
                
                
                f = open('서울_애견동반.csv','a', newline='')
                wr = csv.writer(f)
                wr.writerow([place_name,place_address,star,comment])
                
                
                
        print(len(list_star),list_star)
        print(len(list_review),list_review)
        print('======================완료=========================')
        
        driver.close()
        driver.switch_to.window(driver.window_handles[0]) 
        
        f.close()
    


if __name__ == "__main__":
    main()
