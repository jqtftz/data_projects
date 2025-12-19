import os
import time
import requests
import numpy as np
import pandas as pd
from supabase import create_client, Client

# запрос данных от github

# авторизация
git_token = os.getenv('GIT_TOKEN')
git_username = 'jqtftz'
supabaseUrl = os.getenv('SUPABASEURL')
supabaseKey = os.getenv('SUPABASEKEY')

# определение методов для обращения к github
repo_search = 'https://api.github.com/search/repositories'
repo_get = 'https://api.github.com/repositories/{repo_id}'
user_get = 'https://api.github.com//user/{user_id}'

# поиск по репозиториев по топику 'data-science', сортировка по убыванию по количеству 'stars'
query = {'q' : 'topic:data-science',
         'sort': 'stars',
         'order': 'desc',
         'per_page': 100}

# запрос данных на поиск репозиториев
raw_response = requests.get(repo_search, params = query, auth = (git_username, git_token))
response = raw_response.json()

# преобразование ответа в датафрейм, отбор необходимых полей
df = pd.json_normalize(response, record_path = 'items')
repo = df[['id']].copy().rename(columns = {'id': 'repo_id'}).drop_duplicates('repo_id')

# загрузка данных в supabase

# активация клиента
supabase: Client = create_client(supabaseUrl, supabaseKey)

# выгрузка актуальных таблиц
repo_supabase = pd.json_normalize(supabase.table('repo').select('*').execute().model_dump()['data'])

# определяем, появились ли новые репозитории и пользователи в ТОП 100
repo_id_supabase = set(repo_supabase['repo_id'])
repo_id_git_api = set(repo['repo_id'])
new_repo_id = repo_id_git_api.difference(repo_id_supabase)

# если новые репозитории появились, то заливаем их в базу
if len(new_repo_id) > 0:
    new_repo = repo[repo['repo_id'].isin(new_repo_id)]
    repo_dict = new_repo.to_dict(orient = 'records')
    repo_supabase = pd.concat([repo_supabase, new_repo])
    for record in repo_dict:
        supabase.table('repo').insert(record).execute()

# выгрузка данных по репозиториям и пользователям

# репозитории
repo_data = []

for repo_id in repo_supabase['repo_id'].drop_duplicates():
    raw_response = requests.get(repo_get.format(repo_id = repo_id), auth = (git_username, git_token))
    if str(raw_response) == '<Response [200]>':
        supabase.table('repo_topics').delete().eq('repo_id', repo_id).execute()
        supabase.table('repo_info').delete().eq('repo_id', repo_id).execute()
        repo_data.append(raw_response.json())
        time.sleep(1)

if len(repo_data) > 0:
    repo_data = pd.json_normalize(repo_data)
    repo_data = repo_data.rename(columns = {'id': 'repo_id', 'owner.id': 'owner_id', 'license.name': 'license_name'})
    repo_data = repo_data.replace(np.nan, None)
    
    # информация по репозиторию
    repo_info = repo_data[['repo_id', 'owner_id', 'name', 'description',
                           'html_url', 'homepage', 'language', 'visibility',
                           'archived', 'license_name']].drop_duplicates(['repo_id']).copy()
    
    # топики в репозитории
    repo_topics = repo_data[['repo_id', 'topics']].explode('topics').reset_index()[['repo_id', 'topics']].drop_duplicates().copy()
    
    # статистика по репозиторию
    repo_stats = repo_data[['repo_id', 'stargazers_count', 'forks_count', 'open_issues_count', 'subscribers_count']].copy()
    repo_stats['dt_time'] = raw_response.headers['Date']
    repo_stats['dt_time'] = pd.to_datetime(repo_stats['dt_time'], utc = True)
    repo_stats['dt_time'] = repo_stats['dt_time'].astype(str)
    repo_stats = repo_stats.drop_duplicates()
    
    # пользователи
    owner_data = []
    
    for owner_id in repo_data['owner_id'].drop_duplicates():
        raw_response = requests.get(user_get.format(user_id = owner_id), auth = (git_username, git_token))
        if str(raw_response) == '<Response [200]>':
            supabase.table('owner').delete().eq('owner_id', owner_id).execute()
            owner_data.append(raw_response.json())
            time.sleep(1)
    if len(owner_data) > 0:
        owner_data = pd.json_normalize(owner_data)
        
        # информация по пользователю
        owner = owner_data[['id', 'login', 'name', 'html_url', 
                            'blog', 'type', 'user_view_type', 
                            'location', 'bio', 'public_repos']].drop_duplicates(['id']).copy()
        owner = owner.replace(np.nan, None)
        owner = owner.rename(columns = {'id': 'owner_id', 'login': 'owner_login'})

# импорт данных в supabase

# пользователь
if len(owner_data) > 0:
    if len(owner) > 0:
        owner_dict = owner.to_dict(orient = 'records')
        for record in owner_dict:
            supabase.table('owner').insert(record).execute()

# информация по репозиториям
if len(repo_data) > 0:
    if len(repo_info) > 0:
        repo_info_dict = repo_info.to_dict(orient = 'records')
        for record in repo_info_dict:
            supabase.table('repo_info').insert(record).execute()
    
    # топики репозитория
    if len(repo_topics) > 0:
        repo_topics_dict = repo_topics.to_dict(orient = 'records')
        for record in repo_topics_dict:
            supabase.table('repo_topics').insert(record).execute()
    
    # статистика по репозиториям
    if len(repo_stats):
        repo_stats_dict = repo_stats.to_dict(orient = 'records')
        for record in repo_stats_dict:
            supabase.table('repo_stats').insert(record).execute()