import Database

reset_time = ("UPDATE Users SET timeLimit = %s")

with Database.pool.get_connection() as connection:
    with connection.cursor() as cursor:
        cursor.execute(reset_time, (6912000,))
        print("Reset time limits for all users!")
