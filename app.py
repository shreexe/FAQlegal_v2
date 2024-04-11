import os
from flask import Flask, render_template, request
from groq import Groq
from pypdf import PdfReader
from bs4 import BeautifulSoup
from urllib.request import urlopen
from dotenv import load_dotenv

app = Flask(__name__)

# Initialize Groq client
client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

# Function to extract text from a PDF file


def get_text_from_document(file):
    pdf = PdfReader(file)
    text = ''
    for page in pdf.pages:
        text += page.extract_text()
    return text

# Function to extract text from a URL


def get_text_from_url(url):
    print(url)
    page = urlopen(url)
    soup = BeautifulSoup(page)
    fetched_text = ' '.join(map(lambda p: p.text, soup.find_all('p')))
    return fetched_text

# Function to generate FAQs using Groq API


def get_faqs(content):
    # print(content,"content")
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": 'system',
                'content': """Your role is to help users extract content from documents contents like terms of services they provide. Once you have the content, you will thoroughly read through it and generate questions that could be considered for a FAQ section for each content segment. Additionally, you will create concise answers for these questions, referencing the specific section or topic from which the answer was derived. carefully analyzing documents to identify key points that could form the basis of frequently asked questions.
Ensure accuracy in content extraction and interpretation. Give the content of each question in a new line.  Mention where you get the answer from at last of the respective answer."""
            },
            {
                'role': 'user',
                'content': "Here is the content I would like to generate FAQs for:" +content+"\nGenerate FAQs for each topic."
            }
        ],
        model="mixtral-8x7b-32768",
        temperature=0.8,
        stream=True,
    )
    print(chat_completion, "chat_completion")
    return chat_completion

# Flask route for the home page


@app.route('/')
def home():
    return render_template('index.html')

# Flask route to handle form submission


@app.route('/process', methods=['POST', 'GET'])
def process():
    url = request.form.get('url')
    file = request.files['file']

    if url:
        text = get_text_from_url(url)
        print(text, "text!")
    elif file:
        text = get_text_from_document(file)
    else:
        return "No input provided"

    faqs = ''
    for chunk in get_faqs(text):
        if chunk.choices[0].delta.content:
            faqs += chunk.choices[0].delta.content
            print(faqs, "FAQS")

    return render_template('result.html', faqs=faqs)


if __name__ == '__main__':
    app.run(debug=True)
