create table if not exists users(
	id int primary key default (abs(random()) % 89999 + 10000),
	username text not null,
	password_hash text not null,
	priv_level tinyint not null default 5 check (priv_level >= 1 and priv_level <=5),
	unique(username)
	);

create table if not exists system_params(
	id smallint primary key default (abs(random()) % 8999 + 1000),
	param text not null,
	val_string text default null,
	val_num int default null,
	val_bool boolean default null,
	unique(param)
	);

create table if not exists system_temp(
	id smallint primary key default (abs(random()) % 8999 + 1000),
	"date" date not null,
	"time" time not null,
	temp text not null
	);

create table if not exists crops(
	id smallint primary key default (abs(random()) % 8999 + 1000),
	enabled boolean not null default 0,
	crop text not null,
	pin tinyint not null check (pin >= 0 and pin <=40),
	rain_inc tinyint not null default 1 check (rain_inc >= 1 and rain_inc <= 31),
	"date" date not null,
	"time" time not null,
	unique(crop, pin)
	);

create table if not exists forecast(
	id smallint primary key default (abs(random()) % 8999 + 1000),
	"date" date not null,
	"time" time not null,
	status text,
	pop tinyint not null default 0 check (pop >= 0 and pop <= 100),
	temp real
	);

create table if not exists water_log(
	id smallint primary key default (abs(random()) % 8999 + 1000),
	"date" date not null,
	"time" time not null,
	message text not null default "An error occured in script execution. This was logged from the database."
	);

create table if not exists water_log_60(
        id smallint primary key default (abs(random()) % 8999 + 1000),
        "date" date not null,
        "time" time not null,
        message text not null default "An error occured in script execution. This was logged from the database."
        );

insert into users (username, password_hash, priv_level)
values
	("groot", "$2b$12$cxHaWKvc9qpVNLbjjGD3zueLAHX2AlntXjaNQaqUGbRg/G6/lpr0a", 1);

insert into system_params(param, val_string, val_num, val_bool)
values
	("api_city", "Raleigh", null, null),
	("api_country", "US", null, null),
	("api_state", "NC", null, null),
	("delay_after", null, 1, null),
	("delay_before", null, 1, null),
	("last_rain", null, 28, null),
	("max_crops", null, 4, null),
	("pump_pin", null, 27, null),
	("valve_close_pin", null, 16, null),
	("valve_enable_pin", null, 13, null),
	("valve_open_pin", null, 19, null),
	("system_enable", null, null, 0),
	("use_api", null, null, 0),
	("water_time", null, 10, null);

create trigger if not exists enforce_max_crops after insert on crops
when (select count(*) from crops) > (select val_num from system_params where param = 'max_crops')
begin
	delete from crops
	where id in (select id from crops order by "date" desc, "time" desc, id asc limit 1);
end;

create trigger if not exists max_temp_entries after insert on system_temp
when (select count(*) from system_temp) > 10
begin
	delete from system_temp
	where id in (select id from system_temp order by "date" asc, "time" asc limit 1);
end;

create trigger if not exists max_log_entries after insert on water_log
when (select count(*) from water_log) > 30
begin
	delete from water_log
	where id in (select id from water_log order by "date" asc, "time" asc limit 1);
end;

create trigger if not exists max_log_entries_60 after insert on water_log_60
when (select count(*) from water_log_60) > 60
begin
        delete from water_log_60
        where id in (select id from water_log_60 order by "date" asc, "time" asc limit 1);
end;



