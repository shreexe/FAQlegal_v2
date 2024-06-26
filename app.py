import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from groq import Groq
from pypdf import PdfReader
from bs4 import BeautifulSoup
from urllib.request import urlopen
from octoai.client import Client
from openai import OpenAI
import time


load_dotenv()

app = Flask(__name__)


client = Client()
client1 = OpenAI()


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

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": 'system',
                'content': """Your role is to help the users in generating FAQs in the legal context from the documents provided.Once you get the content, construct three consise and accurate question-answer pairs for each section. Provide the section from where you referred.
                               Thoroughly read the entire text given and complete the response by providing FAQs as said. Be accurate and mention the sections."""
            },
            {
                'role': 'user',
                'content': "Here is the content I would like to generate FAQs for:" + content+"\nGenerate FAQs for each topic."
            }
        ],
        model="mixtral-8x7b-instruct",
        temperature=0.1,
        stream=False,
        max_tokens=4096


    )
    print(chat_completion, "----FAQ")

    # faqs = ''
    # for chunk in get_faqs(chat_completion):
    #     if chunk.choices[0].delta.content:
    #         faqs += chunk.choices[0].delta.content

    return get_format(chat_completion.choices[0].message.content)


def get_format(content):

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": 'system',
                'content': """You have to provide the html tags for the given content. h5 and bold tag for the heading. label in bold where questions as 'Q' and answers as 'A' in bold. Don't provide questions or answers in bold.
                           Provide a break after every answer.Thoroughly follow the instruction through out the content provided. Don't mix the tags and stick to the instructions strictly."""
            },
            {
                'role': 'user',
                'content': "Here is the content I would like to the HTML tags for " + content+"\nProvide corressponding HTML tags."
            }
        ],
        model="mixtral-8x7b-instruct",
        temperature=0.1,
        stream=False,
        max_tokens=4096


    )
    print(chat_completion, "-----FORMAT")

    return chat_completion.choices[0].message.content


def openai(content):
    chat = client1.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": 'system',
            'content': """Your role is to help the users in generating FAQs in the legal context from the documents provided.Once you get the content, construct three consise and accurate question-answer pairs for each section. Provide the section from where you referred.
                               Thoroughly provide the FAQs for the entire text given and complete the response. Be accurate and mention the sections."""
        },
            {
            'role': 'user',
                'content': "Here is the content I would like to generate FAQs for:" + content+"\nGenerate FAQs for each topic."
        }
        ],
        stream=False,
        temperature=0.1
    )
    print(chat, "----CHATGPT")
    return openai_format(chat.choices[0].message.content)


def openai_format(content):
    chat = client1.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": 'system',
            'content': """You have to provide the html tags for the given content. h5 and bold tag for the heading. bold label questions and answers as  'Q' and 'A' respectively. Don't provide questions or answers in bold.
                           Provide a break after every answer.Thoroughly follow the instruction through out the content provided. Don't mix the tags and stick to the instructions strictly. Heading in h5 and bold.
                         Make sure to complete the response with respective html tags as plain text without triple backticks"""
        },
            {
            'role': 'user',
                'content': "Here is the content I would like to generate FAQs for:" + content+"\nGenerate FAQs for each topic."
        }
        ],
        stream=False,
        temperature=0.1
    )
    print(chat, "----FORMAT")
    return chat.choices[0].message.content


@app.route('/')
def home():
    return render_template('index.html')

# Flask route to handle form submission


@app.route('/process', methods=['POST'])
def process():
    start = time.time()

    url = request.form.get('url')
    file = request.files['file']

    if url:
        text = get_text_from_url(url)

    elif file:
        text = get_text_from_document(file)
    else:
        return "No input provided"

    faqs = get_faqs(text)
    end = time.time()
    print("****Time*******", (end-start))

    return render_template('result.html', faqs=faqs)


@app.route('/chatgpt', methods=['POST'])
def chatgpt():
    start = time.time()
    url = request.form.get('url')
    file = request.files['file']

    if url:
        text = get_text_from_url(url)

    elif file:
        text = get_text_from_document(file)
    else:
        return "No input provided"

    faqs = openai(text)

    end = time.time()
    print("****Time*******", (end-start))

    return render_template('result.html', faqs=faqs)


if __name__ == '__main__':
    app.run(debug=True)
