# gemini_api.py
import os
import logging
import google.generativeai as genai  # Import the library (assuming it's installed)
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file
API_KEY = os.getenv('GEMINI_API_KEY1')
#print(f"API Key from .env: {API_KEY}")  # ADD THIS LINE!

os.environ["GOOGLE_API_KEY"] = API_KEY  # Set the environment variable *before* configuring


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GeminiHandler:
    def __init__(self):
        logger.info("Initializing GeminiHandler")

        # Get the API key from environment variables
        self.api_key = API_KEY

        if not self.api_key:
            logger.error("Gemini API key not found in environment variables.  Set GEMINI_API_KEY in .env file.")
            raise ValueError("Gemini API key not found.")

        try:
            
            genai.configure(api_key=API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')  # Or your desired model
            logger.info("Successfully initialized Gemini API connection")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {str(e)}", exc_info=True)
            raise

    def send_message(self, prompt):
        """Sends a message to the Gemini API and returns the response."""
        try:
            response = self.model.generate_content(prompt)
            return response.text  # Or process the response as needed
        except Exception as e:
            logger.error(f"Error sending message to Gemini API: {str(e)}", exc_info=True)
            return None  # Or raise the exception, depending on your error handling strategy

# Example usage (for testing the Gemini API handler class)
if __name__ == '__main__':
    try:
        gemini_handler = GeminiHandler()
        test_prompt = "What is the capital of France?"
        response = gemini_handler.send_message(test_prompt)

        if response:
            print(f"Gemini API Response: {response}")
        else:
            print("Failed to get a response from the Gemini API.")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")