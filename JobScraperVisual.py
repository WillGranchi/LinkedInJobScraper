import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import time


def get_job_postings(company_urls):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    all_jobs = []
    one_month_ago = datetime.now() - timedelta(days=30)
    
    for url in company_urls:
        with st.spinner(f'Scraping jobs from {url}...'):
            try:
                response = requests.get(url, headers=headers)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                job_listings = soup.find_all('div', {'class': 'job-search-card'})
                
                for job in job_listings:
                    try:
                        title = job.find('h3', {'class': 'base-search-card__title'}).text.strip()
                        company = job.find('h4', {'class': 'base-search-card__subtitle'}).text.strip()
                        date_posted = job.find('time')['datetime']
                        job_link = job.find('a', {'class': 'base-card__full-link'})['href']
                        
                        post_date = datetime.strptime(date_posted[:10], '%Y-%m-%d')
                        
                        if post_date >= one_month_ago:
                            job_data = {
                                'Title': title,
                                'Company': company,
                                'Date Posted': date_posted[:10],
                                'Job Link': job_link
                            }
                            all_jobs.append(job_data)
                    
                    except (AttributeError, KeyError) as e:
                        st.error(f"Error parsing job listing: {str(e)}")
                        continue
                
                time.sleep(3)
                
            except Exception as e:
                st.error(f"Error scraping {url}: {str(e)}")
                continue
    
    return pd.DataFrame(all_jobs) if all_jobs else pd.DataFrame()

def main():
    st.title('LinkedIn Job Scraper Dashboard')
    
    # Session state for URLs
    if 'urls' not in st.session_state:
        st.session_state.urls = []

    # Input field for new URL
    new_url = st.text_input('Enter LinkedIn Jobs Search URL:')
    if st.button('Add URL'):
        if new_url and new_url not in st.session_state.urls:
            st.session_state.urls.append(new_url)

    # Display and manage URLs
    st.subheader('Current URLs:')
    for i, url in enumerate(st.session_state.urls):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text(url)
        with col2:
            if st.button('Remove', key=f'remove_{i}'):
                st.session_state.urls.pop(i)
                st.rerun()

    # Scrape jobs button
    if st.button('Scrape Jobs') and st.session_state.urls:
        df = get_job_postings(st.session_state.urls)
        
        if not df.empty:
            # Display results
            st.subheader('Job Listings')
            st.dataframe(df)
            
            # Download button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download CSV",
                csv,
                "linkedin_jobs.csv",
                "text/csv",
                key='download-csv'
            )
        else:
            st.warning('No jobs found for the given URLs.')

if __name__ == "__main__":
    main()
