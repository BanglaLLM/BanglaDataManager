import os
import jsonlines
from bs4 import BeautifulSoup
import requests
import time
from datasets import Dataset, load_dataset
from tqdm import tqdm, trange
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import concurrent.futures
from fake_useragent import UserAgent

BASE_URL = "https://sattacademy.com/"
Q_ID = 1
MAX_Q = 531000
SATT_URL = f"{BASE_URL}academy/single-question?"
HF_DATASET_ID = "BanglaLLM/SattSamprotikAll"
HF_TOKEN = os.getenv("HF_TOKEN")
OUT_FILE = "all.jsonl"
ERROR_FILE = f"error_{time.strftime('%Y-%m-%d_%H-%M-%S')}"

import pickle
with open('errors.pkl', 'rb') as f:
    errors = pickle.load(f)

# Configure session with retry strategy
def create_session(proxy=None):
    session = requests.Session()
    retries = Retry(
        total=1, # 1, 2, 4, 8, 16
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    if proxy:
        session.proxies = {
            "http": proxy,
            "https": proxy
        }

    # Rotate User-Agents
    ua = UserAgent()
    session.headers = {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

    return session

def get_done_ids():
    ids = set()
    if os.path.exists(OUT_FILE):
        with jsonlines.open(OUT_FILE) as reader:
            for obj in reader:
                ids.add(obj['id'])

    for id in errors['404']:
        ids.add(id)
    
    for id in errors['qna_not_found']:
        ids.add(id)

    ds = load_dataset(HF_DATASET_ID)
    for row in ds['train']:
        ids.add(row['id'])
    return ids

def extract_data(html_content, q_id):
    soup = BeautifulSoup(html_content, 'html.parser')
    choices = None

    isit404 = soup.select_one('.image-404')
    if isit404:
        raise ValueError("404 Not Found")
    
    title = soup.select_one('h1')
    question = title.text.strip() if title else None
    
    first_card_body = soup.select_one(".card-body")
    choices_div = first_card_body.select('.row .col-md-6') if first_card_body else []
    
    if len(choices_div) > 1:
        choices = [choice.text.strip() for choice in choices_div]
        choices = [choice for choice in choices if choice]
    
    answer_element = soup.select_one('.sa-success')
    answer = answer_element.text.strip() if answer_element else None
    
    category_container = soup.select_one(".card.card-bordered .card-body")
    categories = [span.text.strip() for span in category_container.select("a .badge")] if category_container else []
    
    try:
        description = soup.select_one('.all-description').select_one('.px-3.text-dark')
        description = description.text.strip()
    except:
        description = None
    
    ret = {
        'id': q_id,
        'question': question,
        'answer': answer,
        'description': description,
        'categories': categories,
        'choices': choices
    }

    def clean_string(x):
        if isinstance(x, int) or isinstance(x, float): return x
        if not x: return ""
        return x.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip()

    for k, v in ret.items():
        if k == 'id': continue
        if isinstance(v, str):
            ret[k] = clean_string(v)
        elif isinstance(v, list):
            ret[k] = [clean_string(x) for x in v]

    return ret
 
def fetch_and_process(q_id):
    try:
        proxy = None
        session = create_session(proxy)

        time.sleep(random.uniform(0.5, 2))
        
        response = session.get(SATT_URL + f"ques_id={q_id}")
        retry = 0
        while response.status_code == 429 and retry < 5:
            retry += 1
            wait_time = int(response.headers['Retry-After'])
            for i in trange(wait_time, desc=f"Waiting {q_id}.{retry}", leave=False):
                time.sleep(1)
            time.sleep(wait_time)
            response = session.get(SATT_URL + f"ques_id={q_id}")
        response.raise_for_status()
        
        data = extract_data(html_content=response.text, q_id=q_id)
        if data['question'] is None or data['answer'] is None:
            raise ValueError("Question or answer not found")
        
        return data
    except Exception as e:
        with open(f'{ERROR_FILE}.log', 'a') as f:
            f.write(f"Error at ID: {q_id} - {e}\n")
        with open(f'{ERROR_FILE}.txt', 'a') as f:
            f.write(f"{q_id}\n")
        return None

def create_dataset():
    done_ids = get_done_ids()
    
    # Process in batches to manage memory
    BATCH_SIZE = 256
    NUM_WORKERS = 16
    remaining_ids = [i for i in range(Q_ID, MAX_Q + 1) if i not in done_ids]
    print(f"Total Ids: {MAX_Q - Q_ID + 1}")
    print(f"Done Ids: {len(done_ids)}")
    print(f"Remaining Ids: {len(remaining_ids)}")
    
    for i in trange(0, len(remaining_ids), BATCH_SIZE):
        batch_ids = remaining_ids[i:i + BATCH_SIZE]
        
        # Process batch with thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
            futures = {executor.submit(fetch_and_process, q_id): q_id 
                      for q_id in batch_ids}
            
            for future in tqdm(concurrent.futures.as_completed(futures), 
                             total=len(batch_ids), 
                             desc=f"Batch {i//BATCH_SIZE + 1}",
                             leave=False):
                data = future.result()
                if data:
                    with jsonlines.open(OUT_FILE, 'a') as writer:
                        writer.write(data)

    # Create final dataset
    all_data = []
    with jsonlines.open(OUT_FILE) as reader:
        for obj in reader:
            all_data.append(obj)
    all_data.sort(key=lambda x: x['id'])
    
    return Dataset.from_list(all_data)

if __name__ == "__main__":
    dataset = create_dataset()
    dataset.push_to_hub(
        HF_DATASET_ID,
        token=HF_TOKEN,
    )