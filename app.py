from flask import Flask, render_template, request, jsonify
import os
import openai
from dotenv import load_dotenv
import csv
from datetime import datetime
import json

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Set up the OpenAI client
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# CSV file setup
CSV_FILE = 'semitic_letters.csv'


def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['timestamp', 'qualities', 'letters'])


init_csv()


def generate_letters(qualities):
    system_message = """You are a creative linguist specializing in Semitic languages and phonosemantics, inspired by the ABJD system. Your task is to generate 3 Semitic letters based on given semantic qualities, drawing inspiration from their associated meanings and symbolism. The order of the letters is not important. 

    Provide only the 3 letters as output, without any explanation or additional information."""

    user_message = f"Generate 3 Semitic letters based on these qualities: {', '.join(qualities)}"

    stream = client.chat.completions.create(model="gpt-4o-mini",
                                            messages=[{
                                                "role": "system",
                                                "content": system_message
                                            }, {
                                                "role": "user",
                                                "content": user_message
                                            }],
                                            stream=True)

    generated_letters = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            generated_letters += chunk.choices[0].delta.content

    return generated_letters.strip()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/graph')
def graph():
    return render_template('graph.html')


@app.route('/api/generate-letters', methods=['POST'])
def api_generate_letters():
    qualities = request.json.get('qualities', [])
    if len(qualities) != 3:
        return jsonify({"error": "Please provide exactly 3 qualities"}), 400

    letters = generate_letters(qualities)

    # Store in CSV
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(
            [datetime.now().isoformat(), ','.join(qualities), letters])

    return jsonify({"letters": letters})


@app.route('/api/history', methods=['GET'])
def api_history():
    history = []
    with open(CSV_FILE, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reversed(list(reader)[-10:]):  # Get last 10 entries
            history.append({
                "timestamp": row[0],
                "qualities": row[1].split(','),
                "letters": row[2]
            })
    return jsonify(history)


@app.route('/api/graph-data', methods=['GET'])
def api_graph_data():
    nodes = []
    links = []
    node_ids = {}
    node_count = 0

    with open(CSV_FILE, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            qualities = row[1].split(',')
            letters = row[2].split(',')

            for quality in qualities:
                if quality not in node_ids:
                    node_ids[quality] = node_count
                    nodes.append({
                        "id": node_count,
                        "name": quality,
                        "group": 1
                    })
                    node_count += 1

            for letter in letters:
                if letter not in node_ids:
                    node_ids[letter] = node_count
                    nodes.append({
                        "id": node_count,
                        "name": letter,
                        "group": 2
                    })
                    node_count += 1

            for quality in qualities:
                for letter in letters:
                    links.append({
                        "source": node_ids[quality],
                        "target": node_ids[letter],
                        "value": 1
                    })

    return jsonify({"nodes": nodes, "links": links})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
