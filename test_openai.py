import openai; print(f'API Key set: {bool(openai.api_key) if hasattr(openai, 'api_key') else 'Not directly accessible'}'); print(f'API Base: {openai.base_url if hasattr(openai, 'base_url') else 'Not available'}'); print(f'Loading modules: {dir(openai)[:5]}...')
