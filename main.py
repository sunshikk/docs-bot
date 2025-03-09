from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, ContentType
from aiogram.filters import CommandStart, Command
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os
from chroma import sync_chroma_db, load_user_documents
import asyncio

bot = Bot(token=os.environ["TOKEN"])
dp = Dispatcher()
router = Router()

CHROMA_PATH = "./chroma_db"
USER_DOCS_PATH = "./user_docs"

# Загружаем модель для embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

@router.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет! Отправь мне свои документы для синхронизации с базой данных.")

@router.message(Command("sync"))
async def sync_docs(message: Message):
    if not os.path.exists(USER_DOCS_PATH):
        os.makedirs(USER_DOCS_PATH)

    await message.answer("Отправьте свои документы в формате .md или .rst для синхронизации.")

@router.message(lambda message: message.content_type == ContentType.DOCUMENT)
async def handle_document(message: Message):
    file = message.document
    file_path = os.path.join(USER_DOCS_PATH, file.file_name)

    # Получаем файл с сервера Telegram
    file_info = await bot.get_file(file.file_id)
    
    # Скачиваем файл
    await bot.download_file(file_info.file_path, file_path)

    # Проверяем, если файл подходящий (например, .md или .rst)
    if file_path.endswith(('.md', '.rst')):
        await message.answer(f"Документ {file.file_name} загружен, начинаем синхронизацию...")

        # Загрузка и синхронизация с БД Chroma
        documents = load_user_documents(USER_DOCS_PATH)
        chroma_db = sync_chroma_db(documents)

        await message.answer(f"✅ Синхронизация завершена. База данных обновлена!")
    else:
        await message.answer("Пожалуйста, загрузите файл в формате .md или .rst.")

@router.message()
async def search_docs(message: Message):
    query = message.text
    # Указываем embedding_function при создании объекта Chroma
    chroma_db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)  # Передаем embeddings
    results = chroma_db.similarity_search(query, k=1)

    if results:
        response = "\n\n".join([f"🔹 {r.metadata['source']}: {r.page_content}" for r in results])
    else:
        response = "Не нашел ничего по твоему запросу. Попробуй переформулировать."

    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            await message.answer(response[i:i+4096], parse_mode="Markdown")
    else:
        await message.answer(response, parse_mode="Markdown")

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен.")
