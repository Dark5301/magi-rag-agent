import os
import logfire
from dotenv import load_dotenv

# Load the hidden fuel tank
load_dotenv()

# 1. Turn on the dashboard FIRST.
# We do this immediately so that if our key checks fail, 
# Logfire is already awake to record the crash.
logfire.configure(project_name='react-agent')
logfire.instrument_pydantic()

# 2. Check the fuel levels at the GLOBAL level
# Because these sit at the root of the file, agent.py can safely import them.
api_key = os.getenv('AICREDITS_API_KEY')
base_url = os.getenv('AICREDITS_URL')

# 3. Fail explicitly and specifically
if not api_key:
    logfire.error("Boot failed: Missing AICREDITS_API_KEY.")
    raise ValueError("CRITICAL: AICREDITS_API_KEY is missing from environment variables!")
    
if not base_url:
    logfire.error("Boot failed: Missing AICREDITS_URL.")
    raise ValueError("CRITICAL: AICREDITS_URL is missing from environment variables!")

# 4. Confirm successful ignition
logfire.info("System Booted: Keys found and observability active.")