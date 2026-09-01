import discord
import os
import google.generativeai as genai
from dotenv import load_dotenv
from keep_alive import keep_alive

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Setup Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.5-flash')

# Setup Discord bot
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

async def send_long_message(channel, text):
    """Memecah pesan panjang tanpa jeda agar muat di batas 2000 karakter Discord"""
    chunk_size = 1900
    for i in range(0, len(text), chunk_size):
        await channel.send(text[i:i + chunk_size])

@client.event
async def on_ready():
    print(f'✅ Bot {client.user} is online!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!prof'):
        prompt = message.content[5:].strip()
        if not prompt:
            await message.channel.send("❗ Format: `!prof pertanyaan`")
            return

        try:
            # Menggunakan async context manager untuk efek 'typing...'
            async with message.channel.typing():
                # Menggunakan generate_content_async agar tidak memblokir user lain saat banyak request
                response = await model.generate_content_async(prompt)
                
                if response.text:
                    # Mengirim jawaban lengkap walau melebihi 2000 karakter
                    await send_long_message(message.channel, response.text)
                else:
                    await message.channel.send("⚠️ Gemini tidak mengembalikan respon teks.")

        except Exception as e:
            await message.channel.send(f"⚠️ Terjadi error: {str(e)}")

keep_alive()
client.run(DISCORD_TOKEN)