import os
import requests
import bs4
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
from random import choice, randint
import streamlit as st


headers = { 'User-Agent' :"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"}

wp = pd.read_csv(r'./Working_Proxies.csv')
proxy_list = list(wp['http'])

#creating result folder if not available
# if not os.path.exists("./results"):
#     os.mkdir("./results")

@st.experimental_memo
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')


class BankDetailsAndReviewExtract:

    def __init__(self,BaseURL,headers,proxies):
        self.BaseURL = BaseURL
        self.headers = headers
        self.proxies = proxies
    
    def get_soup(self, URL):

        proxy= {'http': choice(self.proxies)}
        r = requests.get(URL ,{'headers':self.headers, 'proxies': proxy})
        if r.status_code ==200:
            soup = bs4.BeautifulSoup(r.text,'html.parser')
            return soup
        return None
    
    def get_total_page_count(self):

        soup = self.get_soup(self.BaseURL)
        if soup:
            pages = soup.find('a',attrs={"name":"pagination-button-last"}).text
            return int(pages)
        else:
            return None
    
    def get_ind_page_reviews(self,URL,page_no):

        soup = self.get_soup(URL=URL + f"?page={page_no}")
        ind_page_reviews = soup.find_all('div',class_ ="styles_cardWrapper__LcCPA styles_show__HUXRb styles_reviewCard__9HxJJ")
        
        all_review = []
        if len(ind_page_reviews) != 0:

            for rev in ind_page_reviews :
                try:
                    user_name = rev.find("span",class_="typography_heading-xxs__QKBS8 typography_appearance-default__AAY17").text
                except:
                    user_name = None
                try:
                    rating =  rev.find("div",class_="styles_reviewHeader__iU9Px")["data-service-review-rating"]
                except:
                    rating = None
                
                try:
                    location =  rev.find("div",class_="typography_body-m__xgxZ_ typography_appearance-subtle__8_H2l styles_detailsIcon__Fo_ua").text
                except:
                    location = None
                    
                try:
                    review_title =  rev.find("h2",class_="typography_heading-s__f7029 typography_appearance-default__AAY17").text
                except:
                    review_title = None
                
                try:
                    review =  rev.find("p",class_="typography_body-l__KUYFJ typography_appearance-default__AAY17 typography_color-black__5LYEn").text
                except:
                    review = None
                    
                try:
                    date =  rev.find("p",class_="typography_body-m__xgxZ_ typography_appearance-default__AAY17 typography_color-black__5LYEn").text
                except:
                    date = None
                    
                all_review.append([URL,user_name,rating,location,review_title,review,date])
        return all_review


    def get_all_review(self):
        total_pages = self.get_total_page_count()
        all_reviews = []
        try:
            if total_pages:
                
                for page_no in tqdm(range(1,total_pages)):
                    ind_pages_all_reviews = self.get_ind_page_reviews(self.BaseURL,page_no)
                    all_reviews += ind_pages_all_reviews
                    # break

            df_review = pd.DataFrame(all_reviews, columns= ['BankURL','UserName','ReviewRating','UserLocation','ReviewTitle','ReviewComment','ReviewDate'])
            return df_review

        except:
            df_review = pd.DataFrame(all_reviews, columns= ['BankURL','UserName','ReviewRating','UserLocation','ReviewTitle','ReviewComment','ReviewDate'])
            return df_review
            
                

    def get_ind_bank_page(self,page_no):

        soup = self.get_soup(URL=self.BaseURL + f"?page={page_no}")
        banks = soup.find_all('div',class_ ="paper_paper__1PY90 paper_outline__lwsUX card_card__lQWDv card_noPadding__D8PcU styles_wrapper__2JOo2")
        
        all_bank_info = []
        if len(banks)!=0:
            for lt in banks:
                try:
                    bank_title = lt.find('p',class_ = "typography_heading-xs__jSwUz typography_appearance-default__AAY17 styles_displayName__GOhL2").text
                except:
                    bank_title = None
                try:
                    trust_score, review = lt.find('p', class_ = "typography_body-m__xgxZ_ typography_appearance-subtle__8_H2l styles_ratingText__yQ5S7").text.split("|")
                except:
                    trust_score, review = None,None
                try:   
                    location = lt.find('span', class_ = "typography_body-m__xgxZ_ typography_appearance-subtle__8_H2l styles_metadataItem__Qn_Q2 styles_location__ILZb0").text
                except:
                    location = None
                
                try:
                    bank_page_ref = lt.find('a', class_="link_internal__7XN06 link_wrapper__5ZJEx styles_linkWrapper__UWs5j",href=True)['href']
                except:
                    bank_page_ref=None
                    
                all_bank_info.append([bank_title,trust_score,review,location,bank_page_ref])
        
        return all_bank_info


    def get_all_bank_page(self):
        total_pages = self.get_total_page_count()
        all_bank_detail = []
        try:
            if total_pages:
                
                for page_no in tqdm(range(1,total_pages)):
                    ind_bank_page = self.get_ind_bank_page(page_no)
                    all_bank_detail += ind_bank_page
            
            df = pd.DataFrame(all_bank_detail, columns = ['BankName', 'TrustScore','ReviewCount','Location',"Reflink"])
            return df

        except:
            df = pd.DataFrame(all_bank_detail, columns = ['BankName', 'TrustScore','ReviewCount','Location',"Reflink"])
            return df


bank_detail_csv_path = "./all_bank_detail.csv"

if os.path.exists(bank_detail_csv_path):
    bank_detail_df = pd.read_csv(bank_detail_csv_path)

else:
    bank_detail = BankDetailsAndReviewExtract("https://www.trustpilot.com/categories/bank",headers,proxy_list)
    bank_detail_df = bank_detail.get_all_bank_page()
    bank_detail_df.to_csv(bank_detail_csv_path,index=False)


input_bank_name = st.text_input('Enter bank name:')

selected_bank = bank_detail_df[bank_detail_df['BankName']==input_bank_name]['Reflink'].tolist()
if len(selected_bank)>0:
    ref_link_for_given_bank = selected_bank[0]

    bank_URL = f"https://www.trustpilot.com{ref_link_for_given_bank}"

    review_extractor = BankDetailsAndReviewExtract(bank_URL,headers,proxy_list)
    df_review = review_extractor.get_all_review()

    # df_review.to_csv(f"./results/{input_bank_name}_reviews.csv",index=False)

    # st.write("Given bank result is ready")

    df_review = convert_df(df_review)
    st.download_button(
        "Given bank result is ready, Press to Download",
        df_review,
        f"{input_bank_name}_reviews.csv",
        "text/csv",
        key='download-csv'
        )


else:
    print("Given bank detail not found")
    st.write("Given bank detail not found")







        