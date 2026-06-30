const { exec } = require("child_process");
const fs = require("fs");
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true, // 👈 MUITO IMPORTANTE
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

client.on('qr', (qr) => {
    qrcode.generate(qr, { small: true });
    console.log("Escaneia o QR com o WhatsApp");
});

client.on('ready', () => {
    console.log('WhatsApp conectado!');
});

client.initialize();

const axios = require('axios');

async function perguntarIA(mensagem) {
    const eventos = fs.readFileSync("events.txt", "latin1");
    const promptpronto = ` 
        Você é uma assistente chamada tIA, simpática, organizada e direta, que ajuda o usuário com base na agenda dele.
        Eventos do usuário: ${eventos}
        Responda as perguntas com base nas informações e eventos lidos.
        <|im_start|>User:${mensagem}<|im_end|>
        <|im_start|>assistant:<|im_end|>
    `;
    try {
        const response = await axios.post('http://localhost:5001/api/v1/generate', {
            "prompt": promptpronto,
            "max_length": 256,
            "temperature": 0.5,
            "top_p": 0.9,
            "rep_pen": 1.1,
            "stop_sequence": ["User:", "Assistant:", "USER:", "ASSISTANT:", "<|im_end|>"]
        });

        return response.data.results[0].text;
    } 
    
    catch (error) {
        console.error("🔥 ERRO NA IA:");
        console.error(error);

        if (error.response) {
            console.error("Resposta da API:", error.response.data);
        }

        return "Erro ao falar com a IA.";
    }
    ``

}

client.on('message_create', async (msg) => {

    if (!msg.body.toLowerCase().startsWith("tia")) return;
    const texto = msg.body.slice(3).trim();

    exec("python main_bot.py", async (error, stdout, stderr) => {
        if (error) {
            console.error(error);
            msg.reply("Erro ao rodar o Python.");
            return;
        }

    
    try {
        const resposta = await perguntarIA(texto);
        msg.reply(resposta);
    } catch (err) {
        console.error("🔥 ERRO COMPLETO:");
        console.error(err);
        if (err.response) {
            console.error("Resposta da API:", err.response.data);
        }
        msg.reply("Erro ao gerar resposta.");
}


    
    });
});