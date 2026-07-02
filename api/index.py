from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()  # <-- This reads your .env file
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

app = FastAPI()

# CORS - allows Odoo to talk to your API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str
    product_name: str = ""
    brand: str = ""
    category: str = ""
    price: float = 0
    description: str = ""

@app.post("/chat")
async def chat(request: ChatRequest):
    # Vee auto-detected this product from Odoo page
    product_context = ""
    if request.product_name:
        product_context = f"""
        CUSTOMER IS CURRENTLY VIEWING:
        Product: {request.product_name}
        Price: ₹{request.price}
        Brand: {request.brand}
        Category: {request.category}
        Description: {request.description[:300]}
        """
    
    system_prompt = f"""You are Vee, the AI Shopping Bestie for Vellorra.

Your personality:
- Friendly
- Cheerful  
- Supportive
- Professional
- Honest

You love helping people shop confidently.

Always call the customer "Bestie" naturally (don't overuse it).

You specialize in:
- Makeup
- Skincare  
- Perfumes
- Fashion
- Luxury brands
- Gift recommendations
- 2026 fashion trends: coquette, old money aesthetic, quiet luxury, Y2K, clean girl, western/cottagecore

{product_context}

When recommending products:
- Explain WHY.
- Mention pros and possible drawbacks.
- Never invent product facts.
- If information is unavailable, clearly say so.

RESPONSE RULES (IMPORTANT):
- Keep responses SHORT (max 120–160 words OR max 8–10 lines)
- Use bullet points instead of long paragraphs whenever possible
- Do NOT write emotional or influencer-style paragraphs
- Avoid repetitive words like "amazing", "perfect", "you'll love this"
- "Bestie" should be used only once per response or not at all if unnatural

STRUCTURE (must follow):
1. Short friendly opening (optional)
2. Direct answer in 1–2 lines
3. Key points (2–4 bullets)
4. Honest drawback (if any)
5. Simple closing line

STYLE:
- Natural, like a smart friend
- Not salesy
- Not overly emotional  
- Not dramatic or poetic

User asked: {request.question}

If product info exists above, answer about THAT specific product. Do NOT ask "what specifically" - you already know what they're viewing.
"""

    try:
        response = model.generate_content(system_prompt)
        return {"reply": response.text}
    except Exception as e:
        print(f"Gemini error: {e}")
        return {"reply": "Bestie, my brain glitched for a sec 😅 Try asking again!"}

@app.get("/")
def root():
    return {"message": "Velloraa backend is alive 💜"}
from mangum import Mangum
handler = Mangum(app)
