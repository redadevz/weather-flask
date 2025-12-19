from flask import Flask, render_template, request
from pymongo import MongoClient
import requests
import mpld3
import matplotlib.pyplot as plt

app = Flask(__name__)
app.config.from_pyfile('config.py')

client = MongoClient(app.config['MONGO_URI'])
db = client.get_database()

def get_api_data(city):
    api_key = 'f192075f509e383ab6a5a24477502780'
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}'
    response = requests.get(url)
    data = response.json()
    return data

def store_data_mongodb(data):
    collection = db['meteo']
    collection.insert_one(data)

def generate_plot_html(data):
    if data:
        metrics = ['Temperature', 'Humidity']
        values = [data['main']['temp'], data['main']['humidity']]

        plt.figure(figsize=(8, 6))
        
        colors = ['red', 'blue']

        for metric, value, color in zip(metrics, values, colors):
            plt.plot([metric, metric], [0, value], marker='o', linestyle='-', color=color, label=f'{metric}: {value}')

        plt.title('Temperature and Humidity')
        plt.xlabel('Metrics')
        plt.ylabel('Values')
        plt.legend()

        plot_html = mpld3.fig_to_html(plt.gcf())
        plt.close()

        return plot_html
    else:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    city = None
    api_data = None

    if request.method == 'POST':
        city = request.form['city']
        if city:
            api_data = get_api_data(city)
            store_data_mongodb(api_data)

    return render_template('index.html', city=city, data=api_data)

@app.route('/charts')
def charts():
    city = request.args.get('city')
    data_from_mongo = db['meteo'].find_one({'name': city})
    plot_html = generate_plot_html(data_from_mongo)
    return render_template('charts.html', city=city, data=data_from_mongo, plot_html=plot_html)

@app.route('/search', methods=['GET', 'POST'])
def search():
    city = None
    data_from_mongo = None

    if request.method == 'POST':
        search_term = request.form['search_term']
        if search_term:
            data_from_mongo = db['meteo'].find_one({'name': search_term})

    return render_template('search.html', city=city, data=data_from_mongo)

@app.route('/filter', methods=['GET', 'POST'])
def filter():
    filtered_data = None

    if request.method == 'POST':
        filter_by = request.form['filter_by']
        filter_value = request.form['filter_value']

        if filter_by and filter_value:

            if filter_by == 'temperature':
                filter_condition = {'main.temp': {'$gte': float(filter_value)}}
            elif filter_by == 'humidity':
                filter_condition = {'main.humidity': {'$gte': float(filter_value)}}
            else:
                filter_condition = {}

            filtered_data = db['meteo'].find(filter_condition)

    return render_template('filter.html', data=filtered_data)

@app.route('/compare', methods=['GET', 'POST'])
def compare():
    data_city1 = None
    data_city2 = None

    if request.method == 'POST':
        city1 = request.form['city1']
        city2 = request.form['city2']

        if city1 and city2:
            data_city1 = db['meteo'].find_one({'name': city1})
            data_city2 = db['meteo'].find_one({'name': city2})

    return render_template('compare.html', city1=city1, city2=city2, data_city1=data_city1, data_city2=data_city2)

if __name__ == '__main__':
    app.run(debug=True)
