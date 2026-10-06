-- v_departures: one stop passage (trip, stop, time), ready to filter by stop,
-- line, destination or time. One row per stop_times row.
CREATE VIEW v_departures AS
SELECT
    st.stop_id,
    s.stop_name,
    r.route_id,
    r.route_short_name,
    r.route_long_name,
    t.trip_id,
    t.trip_headsign,
    t.direction_id,
    st.departure_time,
    st.stop_sequence
FROM stop_times st
JOIN trips  t ON t.trip_id  = st.trip_id
JOIN routes r ON r.route_id = t.route_id
JOIN stops  s ON s.stop_id  = st.stop_id;

-- v_route_stops: for each line and direction, the ordered list of its stops
-- (a stop can appear on several trips of the same line; DISTINCT removes
-- duplicates). To guarantee the order, always sort explicitly by
-- stop_sequence in the query that uses this view: SQLite does not
-- guarantee that an ORDER BY in the view survives an enclosing query.
CREATE VIEW v_route_stops AS
SELECT DISTINCT
    r.route_id,
    r.route_short_name,
    t.direction_id,
    st.stop_sequence,
    st.stop_id,
    s.stop_name
FROM stop_times st
JOIN trips  t ON t.trip_id  = st.trip_id
JOIN routes r ON r.route_id = t.route_id
JOIN stops  s ON s.stop_id  = st.stop_id
ORDER BY r.route_id, t.direction_id, st.stop_sequence;

-- v_trajets: one row per pair of stops (A then B) on the same trip, i.e. every
-- direct ride a passenger can take. The domain rules live here, not in prompts:
-- A always precedes B (stop_sequence), and the duration is computed from
-- seconds (times are TEXT: '06:46:00' - '06:30:00' would give 0).
CREATE VIEW v_trajets AS
SELECT
    a.stop_id                  AS depart_id,
    sa.stop_name               AS depart_nom,
    b.stop_id                  AS arrivee_id,
    sb.stop_name               AS arrivee_nom,
    t.route_id,
    t.direction_id,
    t.trip_id,
    a.departure_time           AS heure_depart,
    b.departure_time           AS heure_arrivee,
    (strftime('%s', b.departure_time) - strftime('%s', a.departure_time)) / 60 AS duree_min,
    b.stop_sequence - a.stop_sequence AS nb_arrets
FROM stop_times a
JOIN stop_times b ON b.trip_id = a.trip_id AND a.stop_sequence < b.stop_sequence
JOIN trips t  ON t.trip_id  = a.trip_id
JOIN stops sa ON sa.stop_id = a.stop_id
JOIN stops sb ON sb.stop_id = b.stop_id;
