
# Update zones table, zone_data - [zone, latitude, longitude, id]
UPDATE_ZONES_TABLE = '''
    UPDATE zones
        SET zone = ? ,
            latitude = ? ,
            longitude = ?
        WHERE id = ?
    '''

# Update locations table, location_data [last_used, usage_cnt, id]
UPDATE_LOCATION_USED = '''
    UPDATE locations
        SET last_used = ? ,
            usage_cnt = ?
        WHERE id = ?
    '''

# Add zone record - [zone, latitude, longitude]
ADD_ZONE_RECORD = '''
    INSERT INTO zones(
        zone, latitude, longitude)
    VALUES(?,?,?)
    '''

# Add location record - [zone_id, lat_long_key, travel_time, distance, added,
#                        last_used, usage_cnt]
ADD_LOCATION_RECORD = '''
    INSERT INTO locations(
        zone_id, lat_long_key, travel_time, distance, added, last_used,
        usage_cnt)
    VALUES(?,?,?,?,?,?,?)
    '''

CREATE_ZONES_TABLE = '''
    CREATE TABLE IF NOT EXISTS zoness (
        id              integer PRIMARY KEY,
        zone            text NOT NULL,
        latitude        real,
        longitude       real
    );'''



CREATE_LOCATIONs_TABLE = '''
    CREATE TABLE IF NOT EXISTS tasks (
        id              integer PRIMARY KEY,
        zone_id         integer,
        lat_long_key    text NOT NULL,
        added           text,
        last_used       text,
        usage_cnt       integer,
        FOREIGN KEY (zone_id) REFERENCES zones (id)
    );'''
