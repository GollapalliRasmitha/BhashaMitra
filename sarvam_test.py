import os
import sys

from dotenv import load_dotenv
from sarvamai import SarvamAI

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

client = SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])

response = client.text.translate(
    input="బాగున్నారా",
    source_language_code="te-IN",
    target_language_code="kn-IN",
    model="mayura:v1",
    mode="modern-colloquial",
    output_script="fully-native",
)

print(response)
