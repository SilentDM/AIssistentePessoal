import sys
import whisper

def extrair_comando(texto):
    texto_lower = texto.lower()
    if "tia" not in texto_lower:
        return None
    indice = texto_lower.find("tia")
    return texto[indice + len("tia"):].strip()


model = whisper.load_model("base")
arquivo = sys.argv[1]
resultado = model.transcribe(
    arquivo,
    language="pt"
)
texto = resultado["text"]
prompt = extrair_comando(texto)
if prompt:
    print(prompt)
else:
    print("")