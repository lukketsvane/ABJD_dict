from flask import Flask, render_template, request, jsonify
import os
import openai
from dotenv import load_dotenv
import csv
from datetime import datetime

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Set up the OpenAI client
client = openai.OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

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

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        stream=True
    )

    generated_letters = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            generated_letters += chunk.choices[0].delta.content

    return generated_letters.strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate-letters', methods=['POST'])
def api_generate_letters():
    qualities = request.json.get('qualities', [])
    if len(qualities) != 3:
        return jsonify({"error": "Please provide exactly 3 qualities"}), 400
    
    letters = generate_letters(qualities)

    # Store in CSV
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now().isoformat(), ','.join(qualities), letters])

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

if __name__ == '__main__':
    app.run(debug=True)