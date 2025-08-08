import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from iq_interface import IQBot
from data_collector import process_candles
from gpt_analyzer import analisar_com_openrouter
import asyncio

# Estados
LOGIN, PASSWORD, AGUARDANDO_OI, CONTA, ATIVO, TEMPO = range(6)

# Usuários autenticados e dados por chat_id
usuarios = {}

# Comando /start e colate do e-mail
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Comando /start recebido!")
    await update.message.reply_text("Olá Informe seu e-mail para login na IQ Option:")
    return LOGIN

# Coleta da senha
async def receber_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text
    await update.message.reply_text("Agora informe sua senha:")
    return PASSWORD

# Coleta a senha e autentica (Simulação)
async def receber_senha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["senha"] = update.message.text
    chat_id = update.effective_chat.id

    email = context.user_data["email"]
    senha = context.user_data["senha"]
    
    try:
        bot_iq = IQBot(email, senha)
        
        # Tentativa de conexão com timeout
        tentativas = 0
        while not bot_iq.IQ.check_connect():
            print("Conectando...")
            await update.message.reply_text("Conectando...")
            await asyncio.sleep(1)
            tentativas += 1
            if tentativas > 10:
                raise Exception("Não foi possível conectar após várias tentativas.")

        usuarios[chat_id] = {
            "email": email,
            "senha": senha,
            "bot_iq": bot_iq
        }

        await update.message.reply_text("✅ Login realizado com sucesso! Me diga 'oi' quando quiser começar.")
        return AGUARDANDO_OI

    except Exception as e:
        await update.message.reply_text(f"❌ Erro no login: {str(e)}\nTente novamente com /start.")
        return ConversationHandler.END
    
# Aguardando o usuário iniciar
async def receber_oi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Qual conta você deseja usar? (real ou demo)")
    return CONTA
    
async def escolher_conta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conta = update.message.text.lower()
    if conta not in ["real", "demo"]:
        await update.message.reply_text("Por favor diga 'real' ou 'demo'.")
        return CONTA
    
    context.user_data["conta"] = "REAL" if conta == "real" else "PRACTICE"
    await update.message.reply_text("Qual ativo deseja operar? (ex: EURUSD, GBPUSD)")
    return ATIVO
    
# Ativo
async def escolher_ativo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ativo"] = update.message.text.upper()
    await update.message.reply_text("Por quanto tempo deseja operar? (em minutos. ex: 1, 5)")
    return TEMPO

# Tempo
async def escolher_tempo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        tempo = int(update.message.text)
        context.user_data["tempo"] = tempo

        conta = context.user_data["conta"]
        ativo = context.user_data["ativo"]
        chat_id = update.effective_chat.id
        bot_iq = usuarios[chat_id]["bot_iq"]

        bot_iq.IQ.change_balance(conta)

        await update.message.reply_text(
            f"""✅ Iniciando análise por {tempo} minutos no ativo {ativo}.
            Aguarde os sinais a cada 60 segundos...
            """
        )

        for minuto in range(1, tempo + 1):
            candles = bot_iq.get_candles(ativo, 60, 100) # pega 100 candles de 60 segundos.
            df = process_candles(candles)
            sinal = analisar_com_openrouter(df, ativo)

            await update.message.reply_text(
                f"""🕑 *Minuto {minuto}/{tempo}*
                📊 Análise do ativo "{ativo}":
                Minha sugestão: *{sinal.upper()}*
                """
            )

            await asyncio.sleep(60)

        await update.message.reply_text("🔚 *Análise finalizada* Deseja iniciar novamente? Envie 'oi'.")

        return ConversationHandler.END
    
    except Exception as e:
        await update.message.reply_text(f"⚠️ Erro: {e} \n Por favor, envie um número inteiro de minutos.")
        return TEMPO
    
# Cancelar
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operação cancelada. Envie /start para começar de novo.")
    return ConversationHandler.END

# Inicialização
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    app = ApplicationBuilder().token("8234860026:AAG3L7T1KzwLCbWHH-ZINGR9bHFC0ZhUoTg").build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_login)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_senha)],
            AGUARDANDO_OI: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_oi)],
            CONTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, escolher_conta)],
            ATIVO: [MessageHandler(filters.TEXT & ~filters.COMMAND, escolher_ativo)],
            TEMPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, escolher_tempo)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)]
    )

    app.add_handler(conv)
    print("Bot rodando...")
    app.run_polling()