begin;
drop table if exists chats;
drop table if exists users_0;

-- пользователей чата храним в таблице
-- users_<идентификатор чата>
create table chats(
  chat_id BIGINT primary key, --уникальный идентификатор чата, равен 0 для all
  name varchar--название чата
);

create table users_0(
      login varchar(60) primary key--логин юзера чата
);
insert into users_0 select users.login
from users;


commit;