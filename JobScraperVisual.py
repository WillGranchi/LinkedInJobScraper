import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import time
import json
import os
import openai

# Add OpenAI configuration
def configure_openai():
    api_key = st.sidebar.text_input("Enter OpenAI API Key:", type="password")
    if api_key:
        openai.api_key = api_key
        return True
    return False

def chat_with_recruiter_agent(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful recruiting assistant for a team of recruiters in the digital health space."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def recruiter_agent_tab():
    st.title("Recruiter Agent")
    
    if not configure_openai():
        st.warning("Please enter your OpenAI API key in the sidebar to continue.")
        return

    # Chat interface
    st.subheader("Chat with Recruiter Agent")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask your recruiting question..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and display assistant response
        with st.chat_message("assistant"):
            response = chat_with_recruiter_agent(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

def get_job_postings(company_urls, days_back=14):  # Modified function signature
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    all_jobs = []
    cutoff_date = datetime.now() - timedelta(days=days_back)  # Modified to use parameter
    
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
                        
                        if post_date >= cutoff_date:
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

def load_saved_lists():
    if os.path.exists('saved_url_lists.json'):
        with open('saved_url_lists.json', 'r') as f:
            return json.load(f)
    return {}

def save_url_lists(lists):
    with open('saved_url_lists.json', 'w') as f:
        json.dump(lists, f)

def delete_saved_list(list_name):
    if os.path.exists('saved_url_lists.json'):
        with open('saved_url_lists.json', 'r') as f:
            saved_lists = json.load(f)
        if list_name in saved_lists:
            del saved_lists[list_name]
            with open('saved_url_lists.json', 'w') as f:
                json.dump(saved_lists, f)
            return True
    return False

def main():
    st.sidebar.title("Navigation")
    
    # Create tabs
    tab1, tab2 = st.tabs(["LinkedIn Job Scraper", "Recruiter Agent"])
    
    with tab1:
        # Original LinkedIn Job Scraper code
        st.title('LinkedIn Job Scraper')
        # ...existing LinkedIn scraper code...
        if 'urls' not in st.session_state:
            st.session_state.urls = []
        if 'saved_lists' not in st.session_state:
            st.session_state.saved_lists = load_saved_lists()
            
        # Create columns for URL list management
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Existing date range selector
            days_back = st.number_input(
                'Number of days to look back:',
                min_value=1,
                max_value=365,
                value=14,
                help='Select how many days back to search for jobs'
            )

        with col2:
            # Add saved list selector and management
            saved_list_names = list(st.session_state.saved_lists.keys())
            if saved_list_names:
                selected_list = st.selectbox('Load saved URL list:', [''] + saved_list_names)
                col2a, col2b = st.columns([1, 1])
                
                with col2a:
                    if selected_list and st.button('Load List'):
                        st.session_state.urls = st.session_state.saved_lists[selected_list].copy()
                        st.rerun()
                
                with col2b:
                    if selected_list and st.button('Delete List'):
                        if delete_saved_list(selected_list):
                            st.session_state.saved_lists = load_saved_lists()
                            if selected_list in st.session_state.saved_lists:
                                del st.session_state.saved_lists[selected_list]
                            st.success(f'List "{selected_list}" deleted successfully!')
                            st.rerun()

        # URL input and save functionality
        new_url = st.text_input('Enter LinkedIn Jobs Search URL:')
        col3, col4 = st.columns([2, 1])
        
        with col3:
            if st.button('Add URL'):
                if new_url and new_url not in st.session_state.urls:
                    st.session_state.urls.append(new_url)

        with col4:
            # Enhanced save/update list functionality
            list_name = st.text_input('List name:')
            if st.button('Save/Update List'):
                if list_name and st.session_state.urls:
                    # Update existing list or create new one
                    st.session_state.saved_lists[list_name] = st.session_state.urls.copy()
                    save_url_lists(st.session_state.saved_lists)
                    st.success(f'List "{list_name}" saved successfully!')

        # Display and manage URLs with list context
        st.subheader('Current URLs:')
        for i, url in enumerate(st.session_state.urls):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text(url)
            with col2:
                if st.button('Remove', key=f'remove_{i}'):
                    st.session_state.urls.pop(i)
                    # If we're working with a saved list, update it
                    if 'current_list' in st.session_state and st.session_state.current_list:
                        st.session_state.saved_lists[st.session_state.current_list] = st.session_state.urls.copy()
                        save_url_lists(st.session_state.saved_lists)
                    st.rerun()

        # Modify the Scrape Jobs button section
        if st.button('Scrape Jobs') and st.session_state.urls:
            df = get_job_postings(st.session_state.urls, days_back)  # Pass days_back parameter
            
            if not df.empty:
                # Display results
                st.subheader(f'Job Listings (Past {days_back} days)')
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

    with tab2:
        recruiter_agent_tab()

if __name__ == "__main__":
    main()
