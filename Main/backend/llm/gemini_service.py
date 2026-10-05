from google import genai

from backend.config.settings import GEMINI_API_KEY


class GeminiService:

    def __init__(self):

        self.client = genai.Client(
            api_key=GEMINI_API_KEY
        )
        self.models = ["gemini-flash-lite-latest", "gemini-3.5-flash-lite", "gemini-3.5-flash"]

    def generate(self, prompt: str):
        last_error = None
        for model_name in self.models:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                print(f"[GEMINI WARNING] Model '{model_name}' hit error ({e}). Trying fallback...")
                last_error = e
        if last_error is not None:
            raise last_error
        raise RuntimeError("No models configured or available to generate content.")