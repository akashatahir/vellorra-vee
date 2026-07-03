from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

app = FastAPI()

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
    # Auto-set brand to Vellorra if missing
    brand = request.brand if request.brand else "Vellorra"
    
    product_context = ""
    if request.product_name:
        product_context = f"""
        CUSTOMER IS ON THIS PAGE:
        Product: {request.product_name}
        Price: ₹{request.price}
        Brand: {brand}
        Category: {request.category}
        Details: {request.description[:200]}
        """
    
    system_prompt = f"""You are Vee, AI Shopping Bestie for Vellorra.

PERSONALITY: Short, friendly, honest, supportive. Text like a smart bestie, not an essay.

CRITICAL RULES:
1. MAX 40 WORDS or 3 LINES total. Be concise.
2. For "hi", "hello", "hiee" → Reply in 1 line: "Hiee bestie 💛 What are you shopping for?"
3. Use "Bestie" max once per reply. Skip if it feels forced.
4. NO bullet lists unless user asks "list" or "pros and cons".
5. NO paragraphs. 1-2 short sentences only.
6. All products are Vellorra brand. Never say "brand info missing".
7. Be direct. No fluff like "I'm here to help you shop confidently today".

EXAMPLES:
User: "hiee"
You: "Hiee bestie 💛 Looking for something cute today?"

User: "is this good quality?"
You: "Yep! Synthetic leather with rhinestone details. Super cute for ₹1,830 💛 Just hand wash to keep stones shiny."

User: "gift ideas"
You: "Our flats + a Vellorra perfume = perfect bestie gift set under 3k 💛"

{product_context}

User asked: {request.question}

Answer about the product above if info exists. Keep it SHORT.
"""

    try:
        response = model.generate_content(system_prompt)
        reply = response.text.strip()
        
        # Safety: cut if Gemini ignores rules and writes essay
        if len(reply.split()) > 50:
            reply = ' '.join(reply.split()[:40]) + "... 💛"
            
        return {"reply": reply}
    except Exception as e:
        print(f"Gemini error: {e}")
        return {"reply": "Bestie my brain lagged 😅 Try again!"}

@app.get("/")
def root():
    return {"message": "Velloraa backend is alive 💜"}

from mangum import Mangum
handler = Mangum(app)
