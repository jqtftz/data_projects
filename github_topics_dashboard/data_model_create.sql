-- drop repo
drop table if exists
repo;

-- create repo
create table if not exists repo(
  repo_id int primary key
);

-- drop owner
drop table if exists
owner;

-- create owner
create table if not exists owner(
  owner_id int primary key,
  owner_login text,
  name text,
  html_url text,
  blog text,
  type text,
  user_view_type text,
  location text,
  bio text,
  public_repos int
);

-- drop repo_info
drop table if exists
repo_info;

-- create repo_info
create table if not exists repo_info(
  repo_id int primary key references repo(repo_id) on delete cascade,
  owner_id int references owner(owner_id) on delete cascade,
  name text,
  description text,
  html_url text,
  homepage text,
  language text,
  visibility text,
  archived boolean,
  license_name text
);

-- drop repo_topics
drop table if exists
repo_topics;

-- create repo_topics
create table if not exists repo_topics(
  repo_id int references repo(repo_id) on delete cascade,
  topics text
);

-- drop repo_stats
drop table if exists
repo_stats;

-- create repo_stats
create table if not exists repo_stats(
  repo_id int references repo(repo_id) on delete cascade,
  forks_count int,
  open_issues_count int,
  stargazers_count int,
  subscribers_count int,
  dt_time timestamp
);
