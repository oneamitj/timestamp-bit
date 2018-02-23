drop table if exists user;
create table user (
  user_id integer primary key autoincrement,
  uuid text not null,
  email text not null,
  pw_hash text not null,
  type int not null,
  verified boolean not null,
  verified_by text
);

drop table if exists item;
create table item (
  item_id integer primary key autoincrement,
  name text not null,
  data text not null,
  verified boolean not null,
  verified_by text,
  owner boolean not null,
  derived boolean not null,
  linked_items text,
  timestamped boolean not null,
  stamp_txn_id integer
);

drop table if exists txn;
create table txn (
  txn_id integer primary key autoincrement,
  type text not null,
  ts_start boolean not null,
  ts_complete boolean not null,
  bitcoin_tx text,
  bitcoin_block text,
  prev_tx integer not null,
  item_id integer not null,
  data_file_path text not null,
  ots_file_path text not null
);

insert into user (
              uuid, email, pw_hash, type, verified) values ("aj", "a@j.com", "pbkdf2:sha256:50000$gDuJMf6h$3440ee304f9fffeae51a5753058c55d6cacee8cfc4a69b4fcc0227ef5a1fc3c1", "admin", 0)