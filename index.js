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

    // Só processa mensagens enviadas por você
    if (!msg.fromMe) return;

    // =====================
    // PROCESSAMENTO DE ÁUDIO
    // =====================
    if (msg.hasMedia) {

        const media = await msg.downloadMedia();

        if (media && media.mimetype.startsWith("audio")) {

            console.log("Áudio detectado!");

            const fs = require("fs");
            const nomeArquivo = `audio_${Date.now()}.ogg`;

            fs.writeFileSync(
                nomeArquivo,
                Buffer.from(media.data, "base64")
            );

            exec(
                `python transcrever.py "${nomeArquivo}"`,
                (error, stdout, stderr) => {

                    if (error) {
                        console.error(error);
                        return;
                    }

                    const prompt = stdout.trim();

                    // transcrição não continha "tia"
                    if (!prompt) {
                        console.log("Palavra-chave não encontrada.");
                        console.log("prompt")
                        return;
                    }

                    console.log("Prompt detectado:", prompt);
                    const fs = require("fs");
                        fs.unlink(nomeArquivo, (err) => {
                        if (err) console.error(err);
                    });

                    exec(
                        `python main_bot.py ${JSON.stringify(prompt)}`,
                        (error, stdout, stderr) => {

                            if (error) {
                                console.error(error);
                                return;
                            }

                            msg.reply(stdout.trim());

                        }
                    );
                }
            );

            return;
        }
    }

    // =====================
    // PROCESSAMENTO DE TEXTO
    // =====================

    if (!msg.body) return;

    if (!msg.body.toLowerCase().startsWith("tia")) return;

    const textoUsuario = msg.body.slice(3).trim();

    exec(
        `python main_bot.py ${JSON.stringify(textoUsuario)}`,
        (error, stdout, stderr) => {

            if (error) {
                console.error(error);
                msg.reply("Ocorreu um erro ao executar o Python.");
                return;
            }

            msg.reply(stdout.trim());
        }
    );
    

});
