begin;
drop table if exists chats;



create table chats(
  name varchar primary key, --название чата - является уникальным.
  admin varchar       -- администратор данного чата.
);


commit;