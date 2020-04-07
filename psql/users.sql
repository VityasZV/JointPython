begin;
drop table if exists users;
create table users(
  login varchar(60) primary key,
  name varchar,
  password varchar(60)
);


commit;