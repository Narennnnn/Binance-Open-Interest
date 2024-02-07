import requests
from datetime import datetime, timedelta
import psycopg2.extras
import pprint

# Define the coins, contract types, and base symbols (COINM)
coins = ["BTC", "ETH", "XRP", "LINK", "ADA", "BNB", "BAT", "SOL", "DOGE"]
#coins = ["ADA", "BNB", "ETH", "DAI", "XRP", "DOGE", "BTC", "SOL"]
base_symbols = ["USDT"]#make it clear for Binance(possible for usdm)
markets = ["linear", "inverse"]

# Initialize the funding rates and open interest dictionary
funding_rates = {}
open_interests = {}

# Define the API endpoints
instrument_info_url = "https://api-testnet.bybit.com/v5/market/instruments-info"
funding_history_url = "https://api-testnet.bybit.com/v5/market/funding/history"
open_interest_url ="https://dapi.binance.com/dapi/v1/openInterest"

# Get the current time using datetime
current_time = datetime.now()

# Function to divide the date range into intervals
def divide_date_range(start_date, end_date, interval_days=30):
    intervals = []

    current_date = start_date
    while current_date <= end_date:
        interval_end = current_date + timedelta(days=interval_days - 1)
        if interval_end > end_date:
            interval_end is end_date
        intervals.append((current_date, interval_end))

        current_date = interval_end + timedelta(days=1)
    return intervals

# Function to convert epoch milliseconds to a datetime object
def get_launch_date(epoch_milliseconds):
    epoch_seconds = epoch_milliseconds / 1000
    date_obj = datetime.utcfromtimestamp(epoch_seconds)
    return date_obj

# Function to insert data into the database
def insert_data_into_db(cursor, table, data):
    insert_sql = f"""
    INSERT INTO {table} (symbol, timestamp, category, openinterest)
    VALUES (%(symbol)s, %(timestamp)s, %(category)s, %(openinterest)s);
    """

    try:
        cursor.execute(insert_sql, data)
        print("Inserted data:", data)
    except psycopg2.Error as e:
        print(f"Error inserting data into the table: {e}")

# Step 1: Get the launch time for the specified coins
for coin in coins:
    for base_symbol in base_symbols:
        for market in markets:
            # Create the symbol for the request
            symbol = f"{coin}{base_symbol}"
            params = {
                "category": market,
                "symbol": symbol
            }
            while True:
                try:
                    response = requests.get(instrument_info_url, params=params)
                    data = response.json()
                    if response.status_code == 200 and data.get("retCode") == 0:
                        launch_time_ms = int(data["result"]["list"][0]["launchTime"])
                        launch_time = get_launch_date(launch_time_ms)
                        if symbol not in funding_rates:
                            funding_rates[symbol] = {}
                        funding_rates[symbol][market] = {"Launch Time": launch_time}
                        print(f"{symbol} Launch Time : {launch_time}")
                    break
                except Exception as e:
                    print(e)
                    break

# print the final funding_rate dictionary
pprint.pprint(funding_rates)

print("Step 1: Get launch times for specified coins - Finished")

# Define your PostgreSQL connection parameters
host = "localhost"
port = "5432"
user = "postgres"
password = "pass"
database = "postgres"
table_name = "funding_rate"

# Create the initial PostgreSQL connection
connection = psycopg2.connect(
    host=host,
    port=port,
    user=user,
    password=password,
    database=database
)
cursor = connection.cursor()

# Function to create or replace the table schema
# def create_table(cursor, table_name="open_interest"):
#     # Define the SQL statement to create the table
#     create_table_query = sql.SQL("""
#     CREATE TABLE IF NOT EXISTS {table_name} (
#         id UUID DEFAULT uuid_generate_v4() NOT NULL,
#         symbol VARCHAR(255),
#         timestamp BIGINT,
#         category VARCHAR(255),
#         openinterest NUMERIC,
#         PRIMARY KEY (id)
#     );
#     """).format(table_name=sql.Identifier(table_name))
#
#     try:
#         cursor.execute(create_table_query)
#         print(f"Table '{table_name}' created or already exists.")
#     except psycopg2.Error as e:
#         print(f"Error creating or checking the existence of the table: {e}")

# # create_table(cursor=cursor)
# print("Step 2: Create or replace the table schema - Finished")
#
# # Step 2: Get historical funding rates in intervals from launch to current and insert data into the database
# for coin in coins:
#     for base_symbol in base_symbols:
#         symbol = f"{coin}{base_symbol}"
#         if symbol not in funding_rates:
#             continue
#         for market in markets:
#             if market not in funding_rates[symbol]:
#                 continue
#             start_time = funding_rates[symbol][market]["Launch Time"]
#             end_time = current_time
#
#             # Divide the time range into intervals
#             intervals = divide_date_range(start_time, end_time, interval_days=66)
#
#             for interval_start, interval_end in intervals:
#                 params = {
#                     "category": market,
#                     "symbol": symbol,
#                     "startTime": int(interval_start.timestamp()) * 1000,
#                     "endTime": int(interval_end.timestamp()) * 1000,
#                     "limit": 200
#                 }
#                 response = requests.get(funding_history_url, params=params)
#                 data = response.json()
#                 if response.status_code == 200 and data.get("retCode") == 0:
#                     funding_rates_data = data["result"]["list"]
#                     for rate_data in funding_rates_data:
#                         funding_rate = rate_data["fundingRate"]
#                         funding_rate_timestamp = int(rate_data["fundingRateTimestamp"])
#                         insert_data = {
#                             "symbol": symbol,
#                             "timestamp": funding_rate_timestamp,
#                             "funding_rate": funding_rate,
#                             "next_funding_interval": funding_rate_timestamp + 28800000,
#                             "market": market.upper(),
#                             "exchange": "BYBIT",
#                         }
#                         insert_data_into_db(cursor, table_name, insert_data)
#                         print(len(funding_rates_data))
#                         connection.commit()
#
# print("Step 3: Get historical funding rates and insert data into the database - Finished")

# Commit the changes and close the connection
connection.commit()
connection.close()

print("All steps completed successfully.")
