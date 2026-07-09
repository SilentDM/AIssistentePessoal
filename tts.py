import sys
import asyncio
import edge_tts

texto = sys.argv[1]
async def gerar():
    communicate = edge_tts.Communicate(
        text=texto,
        voice="pt-BR-AntonioNeural",
        rate="-5%",
        pitch="-5Hz",
        volume="-5%"
    )
    await communicate.save("resposta.mp3")

asyncio.run(gerar())


#"Bem vindos a Phaetón!"