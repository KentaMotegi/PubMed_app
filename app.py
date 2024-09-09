import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io

# PubMed APIを利用して論文の要約を取得する関数（ESummaryを使用）
def fetch_article_summaries(pmid_list):
    ids = ','.join(pmid_list)
    url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={ids}&retmode=xml'
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'xml')
        
        articles = []
        for docsum in soup.find_all('DocSum'):
            title = docsum.find('Item', {'Name': 'Title'}).text if docsum.find('Item', {'Name': 'Title'}) else 'No Title'
            pub_date = docsum.find('Item', {'Name': 'PubDate'}).text if docsum.find('Item', {'Name': 'PubDate'}) else 'No Date'
            authors = [author.text for author in docsum.find_all('Item', {'Name': 'Author'})]
            pmid = docsum.find('Id').text if docsum.find('Id') else 'No PMID'
            
            articles.append({
                'PMID': pmid,
                'Title': title,
                'Publication Date': pub_date,
                'Authors': ', '.join(authors)
            })
        return articles
    else:
        st.error(f"Error fetching article summaries: HTTP {response.status_code}")
        return None

# PubMed APIを利用して論文のアブストラクトを取得する関数（EFetchを使用）
def fetch_article_abstracts(pmid_list):
    ids = ','.join(pmid_list)
    url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={ids}&retmode=xml'
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'xml')
        
        abstracts = {}
        for article in soup.find_all('PubmedArticle'):
            pmid = article.find('PMID').text if article.find('PMID') else 'No PMID'
            abstract = article.find('AbstractText').text if article.find('AbstractText') else 'No Abstract'
            
            abstracts[pmid] = abstract
        return abstracts
    else:
        st.error(f"Error fetching article abstracts: HTTP {response.status_code}")
        return None

# Streamlitアプリのメイン部分
def main():
    st.title("PubMed Article Details Finder")
    
    # テキストフィールドでPubMed IDsの入力を受け付ける
    pmid_input = st.text_area("Enter PubMed IDs (one per line):", height=300)
    
    if st.button("Fetch Details"):
        if pmid_input:
            pmid_list = [pmid.strip() for pmid in pmid_input.strip().split('\n') if pmid.strip()]
            
            # PubMed APIで要約情報を取得
            summaries = fetch_article_summaries(pmid_list)
            if summaries:
                # PubMed APIでアブストラクト情報を取得
                abstracts = fetch_article_abstracts(pmid_list)
                
                # 要約情報にアブストラクトを追加
                for article in summaries:
                    pmid = article['PMID']
                    article['Abstract'] = abstracts.get(pmid, 'No Abstract')
                
                # データフレームに変換
                df = pd.DataFrame(summaries)
                
                # データフレームをCSVファイルとして保存
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                csv_buffer.seek(0)
                
                # 結果をテキスト形式で保存
                text_buffer = io.StringIO()
                for entry in summaries:
                    text_buffer.write(f"PMID: {entry['PMID']}\n")
                    text_buffer.write(f"Title: {entry['Title']}\n")
                    text_buffer.write(f"Publication Date: {entry['Publication Date']}\n")
                    text_buffer.write(f"Authors: {entry['Authors']}\n")
                    text_buffer.write(f"Abstract:\n{entry['Abstract']}\n")
                    text_buffer.write("-" * 40 + "\n")
                text_buffer.seek(0)
                
                st.write("**Results**:")
                st.dataframe(df)
                
                # CSVファイルとしてダウンロードリンクを提供
                st.download_button(
                    label="Download CSV",
                    data=csv_buffer.getvalue(),
                    file_name='pubmed_data.csv',
                    mime='text/csv'
                )
                
                # テキストファイルとしてダウンロードリンクを提供
                st.download_button(
                    label="Download Text",
                    data=text_buffer.getvalue(),
                    file_name='pubmed_data.txt',
                    mime='text/plain'
                )
            else:
                st.warning("No details found for the provided PubMed IDs.")
        else:
            st.warning("Please enter at least one PubMed ID.")
    
if __name__ == "__main__":
    main()
