const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const { exec } = require("child_process");


const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});


// 2. Inicialização do WhatsApp
client.on('qr', (qr) => {
    qrcode.generate(qr, { small: true });
    console.log("Escaneie o QR Code acima com o seu WhatsApp.");
});

client.on('ready', () => {
    console.log('tIA está online e conectada!');
});

client.initialize();

// 4. Ouvinte de Mensagens
client.on('message_create', async (msg) => {
    // Filtro para responder apenas comandos que começam com "tia"
    if (!msg.body.toLowerCase().startsWith("tia")) return;

    const textoUsuario = msg.body.slice(3).trim();

    // Executa o script Python (presumo que ele atualize o events.txt)
    exec(
        `python main_bot.py ${JSON.stringify(textoUsuario)}`,
        (error, stdout, stderr) => {
        if (error) {
            console.error(error);
            msg.reply("Ocorreu um erro ao executar o python.");
            return;
        }
        // Se o Python rodou com sucesso, responder
        msg.reply(stdout.trim());
        
    });
});