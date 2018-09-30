import csv

print("Loading...")

with open('quotes.csv', 'rb') as csvfile:
    content = csv.reader(csvfile, delimiter='|', quotechar='"')
    quotes = list(content)

print(quotes[0][2])
