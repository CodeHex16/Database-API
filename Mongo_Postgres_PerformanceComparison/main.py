import pymongo, psycopg2, json, time


###################################################################
###### FUNCTIONS ##################################################
###################################################################
def mongo_create_time():
    start = time.time()

    mongo_db["chats"].drop()

    chats_table_mongo = mongo_db["chats"]
    inserted = chats_table_mongo.insert_many(chats)

    return time.time() - start, len(inserted.inserted_ids)


def mongo_fetachall_time():
    start = time.time()

    chats_table_mongo = mongo_db["chats"]
    results = list(chats_table_mongo.find())

    return time.time() - start, len(results)


def mongo_fetchspecific_time(query):
    start = time.time()

    chats_table_mongo = mongo_db["chats"]
    results = list(chats_table_mongo.find(query))

    return time.time() - start, len(results)


def postgres_create_time():
    start = time.time()

    postgres_cursor.execute(
        "DROP TABLE IF EXISTS chats; CREATE TABLE chats (_id VARCHAR(24) PRIMARY KEY, name VARCHAR(100), user_email VARCHAR(255), created_at VARCHAR(50), messages JSON);"
    )

    for chat in chats:
        postgres_cursor.execute(
            "INSERT INTO chats (_id, name, user_email, created_at, messages) VALUES (%s, %s, %s, %s, %s)",
            (
                chat["_id"],
                chat["name"],
                chat["user_email"],
                chat["created_at"],
                json.dumps(chat["messages"]),
            ),
        )

    return time.time() - start, len(chats)


def postgres_fetachall_time():
    start = time.time()

    postgres_cursor.execute("SELECT * FROM chats")
    results = postgres_cursor.fetchall()

    return time.time() - start, len(results)


def postgres_fetchspecific_time(query):
    start = time.time()

    postgres_cursor.execute(query)
    results = postgres_cursor.fetchall()

    return time.time() - start, len(results)


###################################################################
###### MAIN #######################################################
###################################################################
# load data
with open("data.json") as data_file:
    chats = json.load(data_file)

# mongodb connection
mongo_client = pymongo.MongoClient("mongodb://root:example@localhost:27017/")
mongo_db = mongo_client["mydatabase"]

# postgresql connection
postgres_client = psycopg2.connect(
    database="postgres",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432",
)
postgres_cursor = postgres_client.cursor()

mongo_create_times = []
postgres_create_times = []
mongo_fetchall_times = []
postgres_fetchall_times = []
mongo_fetchspecific_injsoncol_times = []
postgres_fetchspecific_injsoncol_times = []
mongo_fetchspecific_nojsoncol_times = []
postgres_fetchspecific_nojsoncol_times = []

for i in range(100):
    # create time test
    mongo_create_times.append(mongo_create_time())
    postgres_create_times.append(postgres_create_time())

    # fetchall time test
    mongo_fetchall_times.append(mongo_fetachall_time())
    postgres_fetchall_times.append(postgres_fetachall_time())

    # fetchspecific in json column time test
    mongo_fetchspecific_injsoncol_times.append(
        mongo_fetchspecific_time({"messages": {"$elemMatch": {"secender": "bot"}}})
    )
    postgres_fetchspecific_injsoncol_times.append(
        postgres_fetchspecific_time(
            "SELECT * FROM chats WHERE messages->0->>'sender' = 'bot'"
        )
    )

    # fetchspecific no json column time test
    mongo_fetchspecific_nojsoncol_times.append(
        mongo_fetchspecific_time({"user_email": "test@test.it"})
    )
    postgres_fetchspecific_nojsoncol_times.append(
        postgres_fetchspecific_time(
            "SELECT * FROM chats WHERE user_email = 'test@test.it'"
        )
    )

###################################################################
###### PRINT RESULTS ##############################################
###################################################################
print(
    "MongoDB Create Time: ",
    sum([i[0] for i in mongo_create_times]) / len(mongo_create_times),
    "sec for ",
    mongo_create_times[0][1],
    " rows",
)
print(
    "PostgreSQL Create Time: ",
    sum([i[0] for i in postgres_create_times]) / len(postgres_create_times),
    "sec for ",
    postgres_create_times[0][1],
    " rows \n",
)

print(
    "MongoDB Fetchall Time: ",
    sum([i[0] for i in mongo_fetchall_times]) / len(mongo_fetchall_times),
    "sec for ",
    mongo_fetchall_times[0][1],
    " rows",
)
print(
    "PostgreSQL Fetchall Time: ",
    sum([i[0] for i in postgres_fetchall_times]) / len(postgres_fetchall_times),
    "sec for ",
    postgres_fetchall_times[0][1],
    " rows \n",
)
print(
    "MongoDB Fetchspecific Time in json column: ",
    sum([i[0] for i in mongo_fetchspecific_injsoncol_times])
    / len(mongo_fetchspecific_injsoncol_times),
    "sec for ",
    mongo_fetchspecific_injsoncol_times[0][1],
    " rows",
)
print(
    "PostgreSQL Fetchspecific Time in json column: ",
    sum([i[0] for i in postgres_fetchspecific_injsoncol_times])
    / len(postgres_fetchspecific_injsoncol_times),
    "sec for ",
    postgres_fetchspecific_injsoncol_times[0][1],
    " rows \n",
)
print(
    "MongoDB Fetchspecific Time no json column: ",
    sum([i[0] for i in mongo_fetchspecific_nojsoncol_times])
    / len(mongo_fetchspecific_nojsoncol_times),
    "sec for ",
    mongo_fetchspecific_nojsoncol_times[0][1],
    " rows",
)
print(
    "PostgreSQL Fetchspecific Time no json column: ",
    sum([i[0] for i in postgres_fetchspecific_nojsoncol_times])
    / len(postgres_fetchspecific_nojsoncol_times),
    "sec for ",
    postgres_fetchspecific_nojsoncol_times[0][1],
    " rows \n",
)


# print time difference in percentage between mongodb and postgres for each test
print("\nTIME DIFFERENCE IN PERCENTAGE")
print(
    "Mongodb create time difference: ",
    (
        sum([i[0] for i in mongo_create_times]) / len(mongo_create_times)
        - sum([i[0] for i in postgres_create_times]) / len(postgres_create_times)
    )
    / (sum([i[0] for i in mongo_create_times]) / len(mongo_create_times))
    * 100,
    "%",
)
print(
    "Mongodb fetchall time difference: ",
    (
        sum([i[0] for i in mongo_fetchall_times]) / len(mongo_fetchall_times)
        - sum([i[0] for i in postgres_fetchall_times]) / len(postgres_fetchall_times)
    )
    / (sum([i[0] for i in mongo_fetchall_times]) / len(mongo_fetchall_times))
    * 100,
    "%",
)
print(
    "Mongodb fetchspecific time difference in json column: ",
    (
        sum([i[0] for i in mongo_fetchspecific_injsoncol_times])
        / len(mongo_fetchspecific_injsoncol_times)
        - sum([i[0] for i in postgres_fetchspecific_injsoncol_times])
        / len(postgres_fetchspecific_injsoncol_times)
    )
    / (sum([i[0] for i in mongo_fetchspecific_injsoncol_times])
       / len(mongo_fetchspecific_injsoncol_times))
    * 100,
    "%",
)
print(
    "Mongodb fetchspecific time difference no json column: ",
    (
        sum([i[0] for i in mongo_fetchspecific_nojsoncol_times])
        / len(mongo_fetchspecific_nojsoncol_times)
        - sum([i[0] for i in postgres_fetchspecific_nojsoncol_times])
        / len(postgres_fetchspecific_nojsoncol_times)
    )
    / (sum([i[0] for i in mongo_fetchspecific_nojsoncol_times])
       / len(mongo_fetchspecific_nojsoncol_times))
    * 100,
    "%",
)