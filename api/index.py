import os
from flask import Flask, jsonify, request
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
import google.generativeai as genai

app = Flask(__name__)

# Ambil Environment Variables
DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

def verify_signature(req):
    signature = req.headers.get("X-Signature-Ed25519")
    timestamp = req.headers.get("X-Signature-Timestamp")
    
    if not signature or not timestamp or not DISCORD_PUBLIC_KEY:
        return False
    
    try:
        verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
        verify_key.verify(f"{timestamp}{req.data.decode('utf-8')}".encode(), bytes.fromhex(signature))
        return True
    except (BadSignatureError, ValueError):
        return False

@app.route("/api/index", methods=["POST"])
@app.route("/", methods=["POST"])
def interactions():
    # 1. Verifikasi keamanan Discord
    if not verify_signature(request):
        return "Unauthorized", 401

    data = request.json or {}

    # 2. Respon PING untuk verifikasi Discord Developer Portal
    if data.get("type") == 1:
        return jsonify({"type": 1})

    # 3. Respon saat command dipanggil
    if data.get("type") == 2:
        prompt = data.get("data", {}).get("options", [{}])[0].get("value", "")
        
        if not prompt:
            return jsonify({
                "type": 4,
                "data": {"content": "❗ Format: `!prof pertanyaan`"}
            })

        try:
            # Langsung panggil Gemini dari prompt murni tanpa penambahan apapun
            response = model.generate_content(prompt)
            
            if response.text:
                text_output = response.text
            else:
                text_output = "⚠️ Gemini tidak mengembalikan respon teks."

        except Exception as e:
            text_output = f"⚠️ Terjadi error: {str(e)}"

        # Pemotong teks jika melebihi batas 2000 karakter Discord
        if len(text_output) > 1900:
            text_output = text_output[:1900] + "..."

        return jsonify({
            "type": 4,
            "data": {"content": text_output}
        })

    return jsonify({"type": 4, "data": {"content": "Unknown command"}})