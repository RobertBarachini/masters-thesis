from datetime import datetime, timedelta
from typing import Dict, List, Union
import plotly.express as px

events = []  # type: List[Dict[str, Union[datetime, str, int, float]]]
events_covid = []  # type: List[Dict[str, Union[datetime, str, int, float]]]
events_tech = []  # type: List[Dict[str, Union[datetime, str, int, float]]]
events_crypto = []  # type: List[Dict[str, Union[datetime, str, int, float]]]
events_finance = []  # type: List[Dict[str, Union[datetime, str, int, float]]]
events_supply = []  # type: List[Dict[str, Union[datetime, str, int, float]]]
events_weather = []  # type: List[Dict[str, Union[datetime, str, int, float]]]

#
'''
	COVID-19 related events
'''
# First human case
events_covid.append({
    "date": datetime(2019, 11, 16),
    "annotation": "COV0",
    "description": "First human case of COVID-19"
})
# WHO declares a public health emergency
events_covid.append({
    "date":
        datetime(2020, 1, 30),
    "annotation":
        "COV1",
    "description":
        "WHO declares COVID-19 a public health emergency of international concern"
})
# WHO declares a pandemic
events_covid.append({
    "date": datetime(2020, 3, 11),
    "annotation": "COV2",
    "description": "WHO declares COVID-19 a pandemic"
})
# COVID-19 market crash
events_covid.append({
    "date": datetime(2020, 2, 20),
    "annotation": "MC",
    "description": "COVID-19 market crash"
})
# - GPU initiatives for protein folding
events_covid.append({
    "date":
        datetime(2020, 3, 25),
    "annotation":
        "FAH",
    "description":
        "Folding@home project  for protein folding exceeds 1.5 exaflops"
})
# COVID-19 market crash end
events_covid.append({
    "date": datetime(2020, 4, 7),
    "annotation": "MCE",
    "description": "COVID-19 market crash end"
})
# - major lockdowns
# - major vaccine announcements

#
'''
	Tech / AI related events
'''
# OpenAI ChatGPT release
events_tech.append({
    "date": datetime(2022, 11, 30),
    "annotation": "CGPT",
    "description": "OpenAI ChatGPT release"
})
# OpenAI GPT-3 release
events_tech.append({
    "date": datetime(2020, 6, 11),
    "annotation": "GPT3",
    "description": "OpenAI GPT-3 release"
})
# - OpenAI GPT-4 release
events_tech.append({
    "date": datetime(2023, 3, 14),
    "annotation": "GPT4",
    "description": "OpenAI GPT-4 release"
})
# GitHub Copilot release
events_tech.append({
    "date": datetime(2021, 6, 29),
    "annotation": "GC",
    "description": "GitHub Copilot release"
})
# - OpenAI and Microsoft partnership
events_tech.append({
    "date": datetime(2019, 7, 22),
    "annotation": "OAM1",
    "description": "OpenAI and Microsoft partnership - $1 billion investment"
})
# - OpenAI and Microsoft partnership 2
events_tech.append({
    "date": datetime(2023, 1, 23),
    "annotation": "OAM2",
    "description": "OpenAI and Microsoft partnership - $10 billion investment"
})

#
'''
	Crypto market crashes / bubbles (2020 - 2022 crypto bubble)
'''
events_crypto.append({
    "date": datetime(2020, 3, 8),
    "annotation": "CRY1",
    "description": "Bitcoin crash - 30%"
})
events_crypto.append({
    "date": datetime(2021, 1, 3),
    "annotation": "CRY2",
    "description": "Bitcoin surge before crash - 17%"
})
events_crypto.append({
    "date": datetime(2021, 2, 16),
    "annotation": "CRY3",
    "description": "Bitcoin surge $50,000"
})
events_crypto.append({
    "date": datetime(2021, 4, 14),
    "annotation": "CRY4",
    "description": "Coinbase goes public on NASDAQ"
})
events_crypto.append({
    "date": datetime(2021, 5, 19),
    "annotation": "CRY5",
    "description": "Crypto decline from ATH. Bitcoin by 30%, Ethereum by 40%"
})
events_crypto.append({
    "date": datetime(2021, 10, 20),
    "annotation": "CRY6",
    "description": "Bitcoin new ATH"
})
events_crypto.append({
    "date": datetime(2022, 9, 15),
    "annotation": "CRY7",
    "description": "Ethereum switch to PoS (proof of stake)"
})
events_crypto.append({
    "date": datetime(2022, 11, 11),
    "annotation": "CRY8",
    "description": "FTX declares bankruptcy"
})
events_crypto.append({
    "date": datetime(2022, 12, 18),
    "annotation": "CRY9",
    "description": "Crypto winter"
})

#
'''
	Supply chain issues / disruptions / accidents / war
'''
events_supply.append({
    "date": datetime(2020, 10, 20),
    "annotation": "AKM",
    "description": "Asahi Kasei fire"
})
events_supply.append({
    "date": datetime(2021, 3, 19),
    "annotation": "REC",
    "description": "Renesas Electronics fire"
})
# https://www.bloomberg.com/graphics/2021-semiconductors-chips-shortage/
events_supply.append({
    "date": datetime(2021, 2, 1),
    "annotation": "SC1",
    "description": "Lead times on chip supply extended to 15 weeks"
})
events_supply.append({
    "date":
        datetime(2021, 2, 24),
    "annotation":
        "EXS",
    "description":
        "US president signs executive order to strengthen semiconductor supply chain"
})
events_supply.append({
    "date":
        datetime(2021, 3, 1),
    "annotation":
        "SC2",
    "description":
        "Lead times for chip supply from Broadcom Inc. extended to 22.2 weeks"
})
events_supply.append({
    "date": datetime(2021, 3, 23),
    "annotation": "SCB",
    "description": "Suez Canal blockage"
})
events_supply.append({
    "date":
        datetime(2021, 9, 15),
    "annotation":
        "EUCA",
    "description":
        "President of the European Commission trails European Chips Act"
})
events_supply.append({
    "date": datetime(2022, 1, 3),
    "annotation": "ASML",
    "description": "ASML fire"
})
# Ukraine war - affects neon gas supply
events_supply.append({
    "date":
        datetime(2022, 2, 24),
    "annotation":
        "UKR1",
    "description":
        "Russia invades Ukraine, constraining supply of neon gas, krypton, and xenon"
})

#
'''
	Weather / climate / natural disasters
'''
events_weather.append({
    "date":
        datetime(2021, 2, 10),
    "annotation":
        "POW1",
    "description":
        "Sumsung halts chip production in Texas due to power outages"
})
# Taiwan drought
events_weather.append({
    "date":
        datetime(2021, 4, 8),
    "annotation":
        "TWD",
    "description":
        "Taiwan droughts threaten production (lack of ultra-pure water)"
})
events_weather.append({
    "date": datetime(2021, 12, 16),
    "annotation": "MYF",
    "description": "Malaysia floods"
})

#
'''
	Finance / business / economy
'''
events_finance.append({
    "date": datetime(2020, 9, 26),
    "annotation": "TRW1",
    "description": "China US trade war | SMIC restrictions"
})
events_finance.append({
    "date":
        datetime(2022, 10, 7),
    "annotation":
        "TRW2",
    "description":
        "China US trade war | Sanctions expanded to more Chinese tech companies"
})
events_finance.append({
    "date": datetime(2021, 4, 1),
    "annotation": "CAR1",
    "description": "Vehicle sales in decline, prices of used cars skyrocket"
})
events_finance.append({
    "date": datetime(2022, 2, 1),
    "annotation": "CAR2",
    "description": "Used car prices remain high"
})
events_finance.append({
    "date":
        datetime(2022, 3, 16),
    "annotation":
        "FED1",
    "description":
        "Fed raises its benchmark interest rate by half a percentage point",
})
events_finance.append({
    "date": datetime(2023, 3, 10),
    "annotation": "SVB",
    "description": "Silicon Valley Bank fails after a bank run"
})

# TODO:
# - chip shortage events: https://en.wikipedia.org/wiki/2020%E2%80%932023_Global_chip_shortage

# Add specific colors to event groups
for event in events_covid:
	event["color"] = px.colors.qualitative.Plotly[1]
for event in events_tech:
	event["color"] = px.colors.qualitative.Plotly[0]
for event in events_crypto:
	event["color"] = px.colors.qualitative.Plotly[4]
for event in events_finance:
	event["color"] = px.colors.qualitative.Plotly[2]  #3]
for event in events_supply:
	event["color"] = px.colors.qualitative.Plotly[3]
for event in events_weather:
	event["color"] = px.colors.qualitative.Plotly[6]

# Add all event groups to the main events list
events.extend(events_covid)
events.extend(events_tech)
events.extend(events_crypto)
events.extend(events_finance)
events.extend(events_supply)
events.extend(events_weather)

# Create dictionaries for each event group
events_covid_dict = {event["annotation"]: event for event in events_covid}
events_tech_dict = {event["annotation"]: event for event in events_tech}
events_crypto_dict = {event["annotation"]: event for event in events_crypto}
events_finance_dict = {event["annotation"]: event for event in events_finance}
events_supply_dict = {event["annotation"]: event for event in events_supply}
events_weather_dict = {event["annotation"]: event for event in events_weather}

# Sort by date
events.sort(key=lambda x: x["date"])


def shift_events(
    events: List[Dict[str, Union[datetime, str, int, float]]]) -> None:
	# Shift events on the plot to avoid overlapping
	date_previous = events[0]["date"]
	is_shifted = False
	for event in events[1:]:
		days_diff = (event["date"] - date_previous).days  # type: ignore
		if days_diff < 20:
			if not is_shifted:
				event["offset"] = 1
				is_shifted = True
			else:
				is_shifted = False
		else:
			is_shifted = False
		date_previous = event["date"]


# Validate events
def validate() -> None:
	event_keys = {}
	for event in events:
		if not isinstance(event["date"], datetime):
			raise ValueError("Date is not a datetime object")
		if not isinstance(event["annotation"], str):
			raise ValueError("Annotation is not a string")
		if not isinstance(event["description"], str):
			raise ValueError("Description is not a string")
		if event["annotation"] in event_keys:
			raise ValueError(f"Duplicate annotation - '{event['annotation']}'")
		event_keys[event["annotation"]] = event
	print("Events validated successfully!")


def add_event_group(
    event: Dict[str, Union[datetime, str, int, float]]) -> None:
	if "group" in event:
		return None
	annotation = event["annotation"]
	if annotation in events_covid_dict:
		event["group"] = "COVID-19"
	elif annotation in events_tech_dict:
		event["group"] = "Tech"
	elif annotation in events_crypto_dict:
		event["group"] = "Crypto"
	elif annotation in events_finance_dict:
		event["group"] = "Finance"
	elif annotation in events_supply_dict:
		event["group"] = "Supply"
	elif annotation in events_weather_dict:
		event["group"] = "Weather"
	else:
		event["group"] = "General"


# TODO
def print_events() -> None:
	# loop over events and print date, group, annotation, and description
	# format in a nice way to insert into thesis
	# 1. sort by date
	# 2. see which group each event belongs to
	# 3. iterate over all events and format them as an unordered list
	# 4. print the list
	events.sort(key=lambda x: x["date"])
	print("Events:")
	# TODO: format padded strings
	# TODO: print with terminal colors equal to the ones in the plot
	for event in events:
		group = event["group"]
		group = group.ljust(8)  # type: ignore
		annotation = event["annotation"]
		annotation = annotation.ljust(4)  # type: ignore
		print(
		    f"- {event['date'].strftime('%Y-%m-%d')} - {group} - {annotation} - {event['description']}"  # type: ignore
		)


def print_events_table() -> None:
	events.sort(key=lambda x: x["date"])
	print("Events:")
	sep = "\\"  # just some character that is not in the text
	# NOTE: tab doesn't work as it's rendered as spaces in the output
	print(f"Date{sep}Group{sep}Annotation{sep}Description")
	for event in events:
		group = event["group"]
		annotation = event["annotation"]
		print(
		    f"{event['date'].strftime('%Y-%m-%d')}{sep}{group}{sep}{annotation}{sep}{event['description']}"  # type: ignore
		)


shift_events(events)
validate()
for event in events:
	add_event_group(event)

# # print_events()
# print_events_table(
# )  # better for Word - 1. copy text to word 2. Insert > Table > Convert Text to Table
