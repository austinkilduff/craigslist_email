import requests
from bs4 import BeautifulSoup
import subprocess
import sys
import os
import austinDB
from config import craigslist_url, email_address, project_dir

# Initialize the database and tables
db_filename = project_dir + "db.json"
db = austinDB.Database(db_filename)

if "cars" not in [table.table_name for table in db.tables]:
    db.create("cars", ["url", "text", "time", "price", "distance", "status"])
cars_table = db.read("cars")
db_car_url_rows = cars_table.read(["url"])
db_car_statusless_rows = cars_table.read(["url", "text", "time", "price", "distance"])

db.create("email_cars", ["url", "text", "time", "price", "distance", "status"])
email_cars_table = db.read("email_cars")

# Get the craigslist page
r = requests.get(craigslist_url)
page_text = r.text
soup = BeautifulSoup(page_text, "html.parser")
results = soup.find_all("div", "result-info")
for result in results:
    # Build up the car row with empty status
    url = result.find("h3", class_="result-heading").find("a")["href"]
    text = result.find("h3", class_="result-heading").find("a").get_text()
    time = result.find("time", class_="result-date")["title"]
    price = result.find("span", class_="result-meta").find("span", class_="result-price").get_text()
    distance = result.find("span", class_="result-meta").find("span", class_="result-tags").find("span", class_="maptag").get_text()
    status = ""
    cl_car = [url, text, time, price, distance, status]

    distance_param = float(craigslist_url.split("search_distance=")[1].split("&")[0])
    if ("mi" in distance and float(distance[:-2]) <= distance_param) or ("km" in distance and float(distance[:-2]) <= 1.6 * distance_param):
        # If the car's URL is not in the database, add the car to the cars table and the email cars table
        if url not in [db_car_url_row[0] for db_car_url_row in db_car_url_rows]:
            cl_car[-1] = "New"
            cars_table.create(cl_car)
            email_cars_table.create(cl_car)
        # If the car's URL is in the database, but something other than status is different, update the cars table and add the car to the email cars table
        elif cl_car[:-1] not in db_car_statusless_rows:
            cl_car[-1] = "Updated"
            cars_table.update(["url", "text", "time", "price", "distance", "status"], cl_car, ["url"], [(lambda u: url == u)])
            email_cars_table.create(cl_car)

# Find cars that have been removed from Craigslist, add them to the email cars table, and delete them from the cars table
for db_car_url_row in db_car_url_rows:
    db_car_url = db_car_url_row[0]
    if db_car_url not in [result.find("h3", class_="result-heading").find("a")["href"] for result in results]:
        db_car = cars_table.read(["url", "text", "time", "price", "distance", "status"], ["url"], [(lambda url: url == db_car_url)])[0]
        db_car[-1] = "Removed"
        email_cars_table.create(db_car)
        cars_table.delete(["url"], [(lambda url: url == db_car_url)])

# Get the cars to be emailed, build the email body, send the email, and clean up the email cars table
email_car_rows = email_cars_table.read()
if len(email_car_rows) > 0:
    email_filename = project_dir + "email.txt"
    email_text = ""
    for email_car_row in email_car_rows:
        url, text, time, price, distance, status = email_car_row
        email_text += status + ": " + text + "\n"
        email_text += time + "\n"
        email_text += price + " - " + distance + "\n"
        email_text += url + "\n\n"

    with open(email_filename, "w") as email_f:
        email_f.write(email_text)

    args = ["neomutt", "-s", "Craiglist car updates", email_address]
    with open(email_filename) as email_f:
        subprocess.Popen(args, stdin=email_f, stdout=sys.stdout, stderr=sys.stderr)

    db.delete("email_cars")
    os.remove(email_filename)

# Print the number of cars that were emailed
# print(str(len(email_car_rows)))
