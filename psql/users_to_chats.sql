begin;
drop table if exists users_to_chats;
create table users_to_chats(
  login varchar(60),
  chat varchar,
  primary key(login, chat)
);


commit;