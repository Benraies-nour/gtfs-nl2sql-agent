CREATE TABLE agency (
    agency_id TEXT PRIMARY KEY,
    agency_name TEXT,
    agency_url TEXT,
    agency_timezone TEXT,
    agency_phone TEXT
);

CREATE TABLE calendar (
    service_id TEXT PRIMARY KEY,
    monday INTEGER,
    tuesday INTEGER,
    wednesday INTEGER,
    thursday INTEGER,
    friday INTEGER,
    saturday INTEGER,
    sunday INTEGER,
    start_date TEXT,
    end_date TEXT
);

CREATE TABLE routes (
    route_id TEXT PRIMARY KEY,
    agency_id TEXT NOT NULL,
    route_short_name TEXT,
    route_long_name TEXT,
    route_type INTEGER,
    FOREIGN KEY (agency_id) REFERENCES agency(agency_id)
);

CREATE TABLE shapes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shape_id TEXT,
    shape_pt_lat REAL,
    shape_pt_lon REAL,
    shape_pt_sequence INTEGER
);

CREATE TABLE trips (
    trip_id TEXT PRIMARY KEY,
    route_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    trip_headsign TEXT,
    direction_id INTEGER,
    shape_id TEXT,
    FOREIGN KEY (route_id) REFERENCES routes(route_id),
    FOREIGN KEY (service_id) REFERENCES calendar(service_id)
);

CREATE TABLE stops (
    stop_id TEXT PRIMARY KEY,
    stop_name TEXT,
    stop_lat REAL,
    stop_lon REAL
);

CREATE TABLE stop_times (
    trip_id TEXT NOT NULL,
    arrival_time TEXT,
    departure_time TEXT,
    stop_id TEXT NOT NULL,
    stop_sequence INTEGER,
    stop_headsign TEXT,
    pickup_type INTEGER,
    shape_dist_traveled REAL,
    timepoint INTEGER,
    PRIMARY KEY (trip_id, stop_sequence),
    FOREIGN KEY (trip_id) REFERENCES trips(trip_id),
    FOREIGN KEY (stop_id) REFERENCES stops(stop_id)
);

-- Indexes

CREATE INDEX idx_routes_agency_id
ON routes(agency_id);

CREATE INDEX idx_trips_route_id
ON trips(route_id);

CREATE INDEX idx_trips_service_id
ON trips(service_id);

CREATE INDEX idx_stop_times_trip_id
ON stop_times(trip_id);

CREATE INDEX idx_stop_times_stop_id
ON stop_times(stop_id);