import sqlite3

db = sqlite3.connect('user_requests.db')
cursor = db.cursor()


def create_database():
    """
    The first initialization of the database
    """
    db.execute('CREATE TABLE IF NOT EXISTS requests(user_id INTEGER, date TEXT, command TEXT, hotels_found BLOB)')
    db.commit()


def add_row(user_id, time, command, matches):
    """
    Adds a new row into the database
    """
    cursor.execute('INSERT INTO requests VALUES(?, ?, ?, ?)', (user_id, time, command, matches))
    db.commit()


def show_tables(message):
    """
    Obtains the last 5 successful search results from the database.
    """
    result = cursor.execute('SELECT * FROM requests WHERE user_id == ? ORDER BY date DESC LIMIT 5',
                            (message.from_user.id,)).fetchall()
    return result
