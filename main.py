from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import json

# Set up chrome driver
chrome_options = Options()  
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

# Helper function
def find(lst, key, value):
	for i, dic in enumerate(lst):
		if dic[key] == value:
			return i
	return -1

# Collecting coffee info
def web_scraping(driver):
	# List of coffee dictionaries
	coffees = []
	# Iterate through each element
	for coffee in driver.find_elements_by_id("post-53"):
		name = coffee.find_element_by_xpath(".//div/div/div[2]/div/h1/a")
		link = name.get_attribute("href")
		name = name.text.lower().title()
		available = coffee.find_elements_by_class_name("addcart")
		boolean = len(available) > 0
		# Check if available; if so, show price
		if boolean:
			price = available[0].find_element_by_xpath(".//a").get_attribute("textContent").replace("\t", "").replace("\n", "").replace("+ to cart", "")
		else:
			price = "N/A"
		country = coffee.find_elements_by_class_name("country-label")
		# Check if coffee is single-origin or espresso blend
		if len(country) > 0:
			country = country[0].text.lower().title()
		else:
			country = "Espresso Blend"
		# Assign right variable to bool
		if boolean:
			boolean = "O"
		else:
			boolean = "X"
		notes = coffee.find_element_by_class_name("flavors").text.lower().title()
		item_dict = {"name": name, "link": link, "availability": boolean, "price": price, "country": country, "notes": notes}
		coffees.append(item_dict)
	return coffees

# Compare with existing coffees, notify about new coffees, price changes, availability changes, then write to coffees.json
def compare_coffee_list(prev, new):
	# List of dictionaries to track changes
	coffees_changes = []
	with open(prev) as json_file:
		data = json.load(json_file)
		original = data["coffees"]
	coffees_changes = {"coffees": [], "time": new["time"]}
	# Check if coffee already exists in previous dict
	for coffee_info in new["coffees"]:
		if coffee_info not in original:
			# Check if coffee exists already
			index = find(original, "name", coffee_info["name"])
			if index != -1:
				# First add it to the tracking list
				coffees_changes["coffees"].append(coffee_info.copy())
				# Check if availability changed
				if coffee_info["availability"] != original[index]["availability"]:
					if coffee_info["availability"] == "O":
						coffees_changes["coffees"][-1]["availability"] = "Now In Stock!"
					else:
						coffees_changes["coffees"][-1]["availability"] = "Now Out of Stock!"
				# Check price change
				if coffee_info["price"] != original[index]["price"]:
					coffees_changes["coffees"][-1]["price"] = str(original[index]["price"])+" --> "+str(coffee_info["price"])
				else:
					coffees_changes["coffees"][-1]["price"] = str(original[index]["price"])
			else:
				# Add to the front of the tracking list
				coffees_changes["coffees"].insert(0, coffee_info.copy())
				if coffee_info["availability"] == "O":
					coffees_changes["coffees"][0]["availability"] = "Brand New Coffee "+coffee_info["name"]+" in stock at "+coffee_info["price"]+"!"
				else:
					coffees_changes["coffees"][0]["availability"] = "Brand New Coffee "+coffee_info["name"]+" out of stock. Check back later!"
	return coffees_changes

# Copies and backs up previous list while overwriting new list
def write_coffee_list(file, new, time, updates):
	with open(file) as json_file:
		data = json.load(json_file)
	with open("/Users/HarryShin/Desktop/automation/coffees "+time+".json", "w+") as fl:
		json.dump(data, fl, indent=4)
	data = new
	with open(file, "w") as f:
		json.dump(data, f, indent=4)
	if len(updates["coffees"]) == 0:
		updates["coffees"].append({"name": "Nothing New!", "link": "https://store.georgehowellcoffee.com/coffees/", "availability": "N/A", "price": "N/A", "country": "N/A", "notes": "N/A"})
	with open("/Users/HarryShin/Desktop/automation/updates.json") as uf:
		data = json.load(uf)
	data = updates
	with open("/Users/HarryShin/Desktop/automation/updates.json", "w") as uf:
		json.dump(updates, uf, indent=4)

def run():
	now = datetime.now()
	dt_string_file = now.strftime("%m:%d:%Y %H:%M:%S")
	dt_string_update = now.strftime("%m/%d/%Y %H:%M:%S")
	# Open George Howell Coffee Shop Online Store
	driver.get("https://store.georgehowellcoffee.com/coffees/")
	prev = "/Users/HarryShin/Desktop/automation/coffees.json"
	new_coffees = web_scraping(driver)
	new_list = {"coffees": new_coffees, "time": dt_string_update}
	updates = compare_coffee_list(prev, new_list)
	write_coffee_list(prev, new_list, dt_string_file, updates)
	driver.quit()
	