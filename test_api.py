import os; from dotenv import load_dotenv; load_dotenv(); print(f\
OpenAI
API
Key
found:
bool(os.environ.get('OPENAI_API_KEY'))
\); import httpx; try: client = httpx.Client(timeout=10.0); response = client.get('https://api.openai.com/v1/models'); print(f'Status: {response.status_code}'); except Exception as e: print(f'Error: {e}')
