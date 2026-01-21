def count_places_query():
    return """
    SELECT COUNT(*) AS total FROM places;
    """

def count_events_query():
    return """
    SELECT COUNT(*) AS total FROM events;
    """

def count_persons_query():
    return """
    SELECT COUNT(*) AS total FROM persons;
    """

def distribution_by_year_query():
    return """
    SELECT EXTRACT(YEAR FROM start_date) AS year, COUNT(*) AS count
    FROM events
    GROUP BY year
    ORDER BY year;
    """
def historical_persons_distribution_query():
    return """
    SELECT SUBSTR(dates, 1, 4) AS century, COUNT(*) AS count
    FROM persons
    GROUP BY century
    ORDER BY century;
    """

def historical_places_period_query():
    return """
    SELECT historical_period, COUNT(*) AS count
    FROM places
    GROUP BY historical_period
    ORDER BY count DESC;
    """

def fetch_places(cursor):
    cursor.execute("SELECT * FROM places ORDER BY place_name LIMIT 10;")
    return cursor.fetchall()

def fetch_events(cursor):
    cursor.execute("SELECT * FROM events ORDER BY start_date DESC LIMIT 10;")
    return cursor.fetchall()

def fetch_persons(cursor):
    cursor.execute("SELECT * FROM persons ORDER BY name ASC LIMIT 10;")
    return cursor.fetchall()