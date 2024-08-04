from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
from models import *
import instructor
from itertools import chain
import json
import os
import time
import asyncio

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize the OpenAI client with the API key from .env
openai_api_key = os.getenv("OPENAI_API_KEY")
client = instructor.from_openai(OpenAI(api_key=openai_api_key))


@app.get("/")
def read_root():
    return {"Hello": "World"}


# Asynchronous generator for streaming responses for HTML generation
async def code_generation(
    input: str,
    html_code: str,
    css_context: str,
    ResponseModel: instructor.Partial[ReturnData],
):
    print("Prompt: ", input)
    print("HTML Code: ", html_code)
    print("CSS Context: ", css_context)
    return client.chat.completions.create(
        model="gpt-4o",
        temperature=0.1,
        messages=[
            {
                "role": "user",
                "content": f"Prompt: {input} If the following HTML Code and CSS Context is nothing then I am asking you to create an entirely new website so please generate both HTML and CSS code\n\nHTML Code:\n{html_code}\n\nCSS Context:\n{css_context}. When returning the code, please include Google Font Imports to make the websites prettier.",
            }
        ],
        response_model=ResponseModel,
        stream=True,
    )


@app.websocket("/ws")
async def websocket_generate_html(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")

    try:
        while True:  # Continuously listen for new messages
            message = await websocket.receive_json()
            data = message.get("data")
            print("Received data:", data)

            if data and data.get("prompt"):
                prompt = data.get("prompt")
                html = data.get("html")
                css = data.get("css")
                print("Prompt received:", prompt)
                print("HTML received:", html)
                print("CSS received:", css)

                response_model = instructor.Partial[ReturnData]
                stream = await code_generation(prompt, html, css, response_model)

                for response in stream:
                    obj = response.model_dump()
                    html_string_code = obj.get("html")
                    css_string_code = obj.get("css")

                    print("HTML code:", html_string_code)
                    print("CSS code:", css_string_code)
                    await websocket.send_text(
                        json.dumps(
                            {
                                "action": "newCode",
                                "data": {
                                    "html": html_string_code,
                                    "css": css_string_code,
                                },
                            }
                        )
                    )
            else:
                await websocket.send_text("No prompt provided, just waiting")
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error occurred: {e}")
