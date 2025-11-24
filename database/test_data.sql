insert into system_temp("date", "time", temp)
values
	("11/11/2025", "03:00:01", "94.2 F"),
	("11/11/2025", "04:00:02", "92.5 F"),
	("11/11/2025", "05:00:01", "90.7 F");

insert into crops (crop, pin, rain_inc, "date", "time")
values
        ("Peppers", 17, 3, date('now'), time('now')),
        ("Zuccini", 18, 1, date('now'), time('now')),
        ("Cactus", 22, 10, date('now'), time('now')),
        ("Tomato", 23, 1, date('now'), time('now'));

insert int forecast ("date", "time", status, pop, temp)
values
        ("2024-06-29", "00:00:00", "overcast clouds", 0, 88.6),
        ("2024-06-29", "03:00:00", "scattered clouds", 0, 82.7),
        ("2024-06-29", "06:00:00", "few clouds", 0, 73.9),
        ("2024-06-29", "09:00:00", "clear sky", 0, 72.1);

insert into water_log ("date", "time", message)
values
	("06/17/2024", "11:00:02", "Did not perform water operation. Water system not enabled."),
	("06/19/2024", "11:00:02", "Did not perform water operation. Water system not enabled."),
	("06/20/2024", "11:00:01", "Did not perform water operation. Water system not enabled.");

insert into water_log_60 ("date", "time", message)
values
        ("06/17/2024", "11:00:02", "Did not perform water operation. Water system not enabled."),
        ("06/19/2024", "11:00:02", "Did not perform water operation. Water system not enabled."),
        ("06/20/2024", "11:00:01", "Did not perform water operation. Water system not enabled.");

