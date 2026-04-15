import argparse
import requests
import time
import base64
import os
import sys

BASE_URL = "http://localhost"

def measure_latency(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"[Latency] Time: {end_time - start_time:.3f} seconds")
        return result
    return wrapper

@measure_latency
def transcribe(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        sys.exit(1)

    url = f"{BASE_URL}/v1/audio/transcriptions"
    with open(file_path, "rb") as f:
        files = {"file": (file_path, f, "audio/wav")}
        data = {"model": "whisper-1"}
        try:
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            print("Success (Transcribe):", response.json())
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            sys.exit(1)

@measure_latency
def embed(text):
    url = f"{BASE_URL}/v1/embeddings"
    payload = {
        "model": "sentence-transformers/all-mpnet-base-v2",
        "input": text
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Success (Embed): Vector generated.")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        sys.exit(1)

@measure_latency
def chat(prompt, image_path):
    if not os.path.exists(image_path):
        print(f"Error: File {image_path} not found.")
        sys.exit(1)

    url = f"{BASE_URL}/v1/chat/completions"
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    payload = {
        "model": "google/gemma-4-E4B-it",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        "max_tokens": 100
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Success (Chat):", response.json()['choices'][0]['message']['content'])
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validation utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_transcribe = subparsers.add_parser("transcribe")
    parser_transcribe.add_argument("--file", required=True)

    parser_embed = subparsers.add_parser("embed")
    parser_embed.add_argument("--text", required=True)

    parser_chat = subparsers.add_parser("chat")
    parser_chat.add_argument("--prompt", required=True)
    parser_chat.add_argument("--image", required=True)

    args = parser.parse_args()

    if args.command == "transcribe":
        transcribe(args.file)
    elif args.command == "embed":
        embed(args.text)
    elif args.command == "chat":
        chat(args.prompt, args.image)
