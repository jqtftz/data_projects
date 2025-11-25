-- drop repo
drop table if exists
repo;

-- create repo
create table if not exists repo(
  repo_id int primary key,
  repo_name text
);

-- drop owner
drop table if exists
owner;

-- create owner
create table if not exists owner(
  owner_id int primary key,
  owner_login text
);

-- drop repo_owner
drop table if exists
repo_owner;

-- create repo_owner
create table if not exists repo_owner(
  repo_id int references repo(repo_id) on delete cascade,
  owner_id int references owner(owner_id) on delete restrict
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
  dt_time timestamp
);