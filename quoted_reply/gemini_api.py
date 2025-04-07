# gemini_api.py
import os
import logging
import google.generativeai as genai
import re # Import regex
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('GEMINI_APIKEY')

# Ensure the environment variable is set *before* initializing genai
if API_KEY:
    os.environ["GOOGLE_API_KEY"] = API_KEY
else:
    logging.error("GEMINI_APIKEY not found in .env file. Please set it.")
    raise ValueError("GEMINI_APIKEY not found in environment variables.")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeminiHandler:
    def __init__(self):
        logger.info("Initializing GeminiHandler")
        self.api_key = os.environ.get("GOOGLE_API_KEY") # Get from env var directly now

        if not self.api_key:
            logger.error("Google API key not configured correctly.")
            raise ValueError("Google API key not configured.")

        try:
            genai.configure(api_key=self.api_key)
            # Use 'gemini-1.5-flash' or 'gemini-pro'
            self.model = genai.GenerativeModel('gemini-2.0-flash') # Or 'gemini-pro'
            logger.info(f"Successfully initialized Gemini API connection with model: {self.model.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {str(e)}", exc_info=True)
            raise

    def _parse_reply_context(self, content):
        """Helper to extract sections from the reply context file content."""
        data = {}
        # Use regex to find sections based on the '** Title : **' format
        patterns = {
            'thread_title': r'\*\* Thread Title : \*\*\s*(.*?)\s*\*\* Original Thread Content:',
            'original_thread_content': r'\*\* Original Thread Content: \*\*\s*(.*?)\s*\*\* My Previous Comment:',
            'my_previous_comment': r'\*\* My Previous Comment: \*\*\s*(.*?)\s*\*\* Quoted Comment:',
            'quoted_comment': r'\*\* Quoted Comment: \*\*\s*(.*)'
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            data[key] = match.group(1).strip() if match else f"[{key} not found in context]"
        return data

    def send_message(self, prompt_content):
        """Sends the prepared content to the Gemini API and returns the text response."""
        logger.debug(f"Sending prompt to Gemini API. Length: {len(prompt_content)}")
        try:
            # Generate content using the combined prompt and context
            # Consider adding safety settings if needed
            # safety_settings = [
            #     {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            #     {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            # ]
            # response = self.model.generate_content(prompt_content, safety_settings=safety_settings)
            response = self.model.generate_content(prompt_content)


            if response.candidates:
                generated_text = getattr(response.candidates[0].content.parts[0], 'text', None)
                if generated_text:
                    logger.info("Successfully received response text from Gemini API.")
                    return generated_text.strip()
                else:
                    logger.warning("Gemini API response candidate did not contain text.")
                    if hasattr(response.candidates[0], 'finish_reason') and response.candidates[0].finish_reason != 'STOP':
                         safety_ratings = getattr(response.candidates[0], 'safety_ratings', [])
                         logger.warning(f"Generation stopped. Reason: {response.candidates[0].finish_reason}. Safety Ratings: {safety_ratings}")
                    return None
            else:
                logger.warning(f"Gemini API response did not contain candidates. Prompt Feedback: {getattr(response, 'prompt_feedback', 'N/A')}")
                return None

        except Exception as e:
            logger.error(f"Error sending message to Gemini API: {str(e)}", exc_info=True)
            return None

    def get_comments(self, reply_context_filepath, thread_content_filepath, prompt_file="prompt.txt"):
        """
        Reads instructions, specific reply context, and full thread context,
        combines them, sends to Gemini API, and returns ONLY the generated comment text.
        """
        logger.info(f"Generating comment using reply context: {reply_context_filepath} and thread context: {thread_content_filepath}")

        # 1. Read Prompt Instructions
        try:
            with open(prompt_file, "r", encoding="utf-8") as f_prompt:
                prompt_instructions = f_prompt.read().strip()
            logger.debug(f"Successfully read prompt instructions from {prompt_file}")
        except FileNotFoundError:
            logger.error(f"Prompt file '{prompt_file}' not found.")
            return None
        except Exception as e:
            logger.error(f"Error reading prompt file '{prompt_file}': {e}")
            return None

        # 2. Read and Parse Specific Reply Context
        try:
            with open(reply_context_filepath, "r", encoding="utf-8") as f_context:
                reply_context_content = f_context.read().strip()
            # Parse the content into distinct parts
            reply_data = self._parse_reply_context(reply_context_content)
            logger.debug(f"Successfully read and parsed reply context from {reply_context_filepath}")
        except FileNotFoundError:
            logger.error(f"Reply context file '{reply_context_filepath}' not found.")
            return None
        except Exception as e:
            logger.error(f"Error reading or parsing reply context file '{reply_context_filepath}': {e}")
            return None

        # 3. Read Full Thread Content
        try:
            with open(thread_content_filepath, "r", encoding="utf-8") as f_thread:
                full_thread_content = f_thread.read().strip()
            # Add a small note for clarity if the file is empty
            if not full_thread_content:
                 full_thread_content = "[No other thread content found or file was empty]"
            logger.debug(f"Successfully read full thread content from {thread_content_filepath}")
        except FileNotFoundError:
            logger.warning(f"Full thread content file '{thread_content_filepath}' not found. Proceeding without full thread context.")
            full_thread_content = "[Full thread content file not found]"
        except Exception as e:
            logger.error(f"Error reading full thread content file '{thread_content_filepath}': {e}")
            # Decide if you want to proceed without it or return None
            full_thread_content = "[Error reading full thread content file]"
            # return None # Uncomment this line if full thread context is mandatory

        # 4. Combine all parts for the final prompt to the API
        # Use the parsed data and the full thread content
        full_prompt_content = f"""{prompt_instructions}

--- START OF INPUT DATA ---

** Thread Title : **
{reply_data.get('thread_title', '[Not Found]')}

** Original Thread Post : **
{reply_data.get('original_thread_content', '[Not Found]')}

** My Previous Comment : **
{reply_data.get('my_previous_comment', '[Not Found]')}

** Quoted Comment (Reply Target) : **
{reply_data.get('quoted_comment', '[Not Found]')}

** Full Thread Content (For Context & Uniqueness Check - Includes OP and all replies) : **
{full_thread_content}

--- END OF INPUT DATA ---

Generate your reply below:
"""

        # 5. Send the combined content to the Gemini API
        generated_comment = self.send_message(full_prompt_content)

        if generated_comment:
             logger.info("Successfully generated unique comment.")
        else:
             logger.warning("Failed to generate unique comment from Gemini API.")

        return generated_comment # Return the result (string or None)


# Example usage (for testing)
if __name__ == '__main__':
    # Create dummy files for testing
    DUMMY_PROMPT = "prompt_test.txt"
    DUMMY_REPLY_CONTEXT = "reply_context_test.txt"
    DUMMY_THREAD_CONTENT = "thread_content_test.txt"
    try:
        # Create prompt file
        with open(DUMMY_PROMPT, "w", encoding="utf-8") as f:
            # Use a simplified version of your actual prompt for testing focus
             f.write("Reply to the quoted comment, considering the previous comment and ensuring uniqueness based on the full thread content. Be concise and natural.\nOutput Format:\n- Reply text only.\n- No quotes.")

        # Create reply context file
        with open(DUMMY_REPLY_CONTEXT, "w", encoding="utf-8") as f:
            f.write("** Thread Title : ** \n Best Pizza Toppings\n\n")
            f.write("** Original Thread Content: ** \n What's everyone's favorite pizza topping?\n\n")
            f.write("** My Previous Comment: ** \n Pineapple belongs on pizza!\n\n")
            f.write("** Quoted Comment: ** \n No way, pineapple is gross on pizza.\n")

        # Create full thread content file
        with open(DUMMY_THREAD_CONTENT, "w", encoding="utf-8") as f:
            f.write("OP: What's everyone's favorite pizza topping?\n")
            f.write("UserA: Pepperoni is classic.\n")
            f.write("UserB: I like mushrooms and olives.\n")
            f.write("UserC: Pepperoni is the only way to go.\n") # Example of repeated point
            f.write("Me (BinaryGhost): Pineapple belongs on pizza!\n") # Your previous comment might be here
            f.write("UserD: No way, pineapple is gross on pizza.\n") # The comment quoting you

        print("Attempting to initialize GeminiHandler...")
        gemini_handler = GeminiHandler()
        print("\nAttempting to generate comment with full context...")
        # Call get_comments with both file paths
        response = gemini_handler.get_comments(DUMMY_REPLY_CONTEXT, DUMMY_THREAD_CONTENT, prompt_file=DUMMY_PROMPT)

        if response:
            print("\n--- Gemini API Response ---")
            print(response)
            print("---------------------------\n")
            # Manual check: Does the response address the "pineapple is gross" comment?
            # Does it avoid just saying "pepperoni"?
            print("Check if the response directly addresses the quoted comment about pineapple and sounds unique.")
        else:
            print("\nFailed to get a response from the Gemini API during test.")

    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during test: {e}")
    finally:
        # Clean up dummy files
        for fname in [DUMMY_PROMPT, DUMMY_REPLY_CONTEXT, DUMMY_THREAD_CONTENT]:
             if os.path.exists(fname):
                 os.remove(fname)