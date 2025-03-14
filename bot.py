from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, ContentType, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
import os
import asyncio
import openai

bot = Bot(token=os.environ["TOKEN"])
dp = Dispatcher()
router = Router()

USER_DOCS_PATH = "./user_docs"
openai.api_key = os.environ["OPENAI_TOKEN"]

documents = []  # Храним загруженные документы в памяти

ADMIN_USER_ID = 1574455983
upload = 0

upl = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
])

async def load_documents():
    global documents
    documents = []
    if not os.path.exists(USER_DOCS_PATH):
        os.makedirs(USER_DOCS_PATH)
    for file_name in os.listdir(USER_DOCS_PATH):
        if file_name.endswith((".md", ".rst")):
            with open(os.path.join(USER_DOCS_PATH, file_name), "r", encoding="utf-8") as f:
                documents.append(f.read())

@router.message(CommandStart())
async def start(message: Message):
    await message.answer("👋🏻 Привет! Отправь мне свой вопрос/ошибку, и я буду искать на них ответ исходя из загруженной документации.")
    if message.from_user.id == ADMIN_USER_ID:
        keyb = [
            [KeyboardButton(text="📥 Загрузить документы")]
        ]
        keyboard = ReplyKeyboardMarkup(keyboard=keyb, resize_keyboard=True)
        await message.answer("🛠️✅ Вы получили ряд функций, так как у Вас есть админка.", reply_markup=keyboard)

@router.message(Command("sync"))
async def sync_docs(message: Message):
    if message.from_user.id == ADMIN_USER_ID:
        if not os.path.exists(USER_DOCS_PATH):
            os.makedirs(USER_DOCS_PATH)
        await message.answer("Отправьте свои документы в формате .md или .rst для загрузки.")

@router.message(lambda message: message.content_type == ContentType.DOCUMENT)
async def handle_document(message: Message):
    if message.from_user.id == ADMIN_USER_ID and upload == 1:
        file = message.document
        file_path = os.path.join(USER_DOCS_PATH, file.file_name)
        
        file_info = await bot.get_file(file.file_id)
        await bot.download_file(file_info.file_path, file_path)
        
        if file_path.endswith(('.md', '.rst')):
            with open(file_path, "r", encoding="utf-8") as f:
                documents.append(f.read())
            await message.answer(f"✅ Документ {file.file_name} загружен и сохранен!")
        else:
            await message.answer("Пожалуйста, загрузите файл в формате .md или .rst.")

@router.message(F.text == "📥 Загрузить документы")
async def upload_docs(message: Message):
    global upload
    if message.from_user.id == ADMIN_USER_ID and upload == 0:
        upload = 1
        await message.answer("📥 Отправьте документы, которые хотите загрузить в формате .md, .rst", reply_markup=upl)

@router.message()
async def search_docs(message: Message):
    if message.text == "📥 Загрузить документы" or message.text == "📄 Просмотр загруженных документов":
        return
    
    idmes = await message.answer("🤔 Думает...")
    query = message.text
    context = "\n\n".join(documents[-10:]) if documents else "Нет загруженных документов."
    print(context)
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты помощник, отвечающий ТОЛЬКО на основе приведённого контекста. Если ответ не содержится в документах, скажи 'Нет информации'."},
                {"role": "system", "content": "Отвечай на все вопросы СТРОГО по документам, ориентируясь по запросу."},
                {"role": "system", "content": "Заголовки документа пиши без символов ###, лучше выделяй заголовок жирным шрифтом, используя **текст**."},
                {"role": "system", "content": "Также прилагай ссылку на источник, которая указана в конце документа не изменяя её, но не нужно использовать ее везде. (ОБЯЗАТЕЛЬНО)"},
                {"role": "system", "content": "Используй только предоставленную тобой информацию ничего не меняя и придумывая, и ни в коем случае не меняй источники."},
                {"role": "user", "content": f"Контекст: {context}\n\nВопрос: {query}"}
            ]
        )
        answer = response.choices[0].message.content  # Извлекаем текст ответа
    except Exception as e:
        answer = f"Ошибка при обработке запроса: {str(e)}"
    
    await bot.delete_message(message.chat.id, idmes.message_id)
    await message.answer(answer, parse_mode="Markdown")

@router.callback_query() 
async def process_callback(callback_query: CallbackQuery): 
    data = callback_query.data

    if data == "cancel":
        upload = 0
        await callback_query.message.answer("Вы отменили загрузку документов.")

async def main():
    await load_documents()  # Загружаем документы перед стартом бота
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен.")

# from aiogram import Bot, Dispatcher, Router, F
# from aiogram.types import Message, ContentType, CallbackQuery
# from aiogram.filters import CommandStart, Command
# from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
# import os
# import asyncio
# import openai

# bot = Bot(token="7543825811:AAH--7U_pSuGzmJIQ8UMImL54v2mBJgMHvY")
# dp = Dispatcher()
# router = Router()

# USER_DOCS_PATH = "./user_docs"
# openai.api_key = "sk-proj-SzjtxjbdKX2IZqdWSVn8T3BlbkFJC4y1Jw565XcmgJlqPQm2"

# documents = []  # Храним загруженные документы в памяти

# ADMIN_USER_ID = 1574455983
# upload = 0  # Глобальный флаг загрузки

# upl = InlineKeyboardMarkup(inline_keyboard=[
#     [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
# ])

# async def load_documents():
#     global documents
#     documents = []
#     if not os.path.exists(USER_DOCS_PATH):
#         os.makedirs(USER_DOCS_PATH)
#     for file_name in os.listdir(USER_DOCS_PATH):
#         if file_name.endswith((".md", ".rst")):
#             documents.append(file_name)  # Добавляем только название файла

# @router.message(CommandStart())
# async def start(message: Message):
#     await message.answer("👋🏻 Привет! Отправь мне свой вопрос/ошибку, и я буду искать на них ответ исходя из загруженной документации.")
#     if message.from_user.id == ADMIN_USER_ID:
#         keyb = [
#             [KeyboardButton(text="📄 Просмотр загруженных документов")],
#             [KeyboardButton(text="📥 Загрузить документы")]
#         ]
#         keyboard = ReplyKeyboardMarkup(keyboard=keyb, resize_keyboard=True)
#         await message.answer("🛠️✅ Вы получили ряд функций, так как у Вас есть админка.", reply_markup=keyboard)

# @router.message(Command("sync"))
# async def sync_docs(message: Message):
#     if message.from_user.id == ADMIN_USER_ID:
#         await load_documents()
#         await message.answer("📂 Документы синхронизированы.")

# @router.message(lambda message: message.content_type == ContentType.DOCUMENT)
# async def handle_document(message: Message):
#     global upload
#     if message.from_user.id == ADMIN_USER_ID and upload == 1:
#         file = message.document
#         file_path = os.path.join(USER_DOCS_PATH, file.file_name)
        
#         file_info = await bot.get_file(file.file_id)
#         await bot.download_file(file_info.file_path, file_path)
        
#         if file.file_name.endswith(('.md', '.rst')):
#             documents.append(file.file_name)  # Добавляем только название файла
#             await message.answer(f"✅ Документ {file.file_name} загружен и сохранен!")
#         else:
#             await message.answer("❌ Пожалуйста, загрузите файл в формате .md или .rst.")

# @router.message(F.text == "📄 Просмотр загруженных документов")
# async def check_docs(message: Message):
#     if message.from_user.id == ADMIN_USER_ID:
#         if not documents:
#             await message.answer("Нет загруженных документов.")
#         else:
#             await message.answer("\n".join(documents))

# @router.message(F.text == "📥 Загрузить документы")
# async def upload_docs(message: Message):
#     global upload
#     if message.from_user.id == ADMIN_USER_ID and upload == 0:
#         upload = 1
#         await message.answer("📥 Отправьте документы, которые хотите загрузить в формате .md, .rst", reply_markup=upl)

# @router.callback_query()
# async def process_callback(callback_query: CallbackQuery): 
#     global upload
#     data = callback_query.data

#     if data == "cancel":
#         if upload == 1:
#             upload = 0
#             await callback_query.message.answer("❌ Вы отменили загрузку документов.")

# @router.message()
# async def search_docs(message: Message):
#     if message.text == "📥 Загрузить документы" or message.text == "📄 Просмотр загруженных документов":
#         return
    
#     query = message.text
#     context = "\n\n".join(documents[-3:]) if documents else "Нет загруженных документов."
    
#     try:
#         response = openai.chat.completions.create(
#             model="gpt-4o",
#             messages=[
#                 {"role": "system", "content": "Ты помощник, отвечающий на вопросы, основываясь на загруженных документах."},
#                 {"role": "system", "content": "Отвечай на все вопросы СТРОГО по документам."},
#                 {"role": "system", "content": "Заголовки документа пиши без символов ###, лучше выделяй заголовок жирным шрифтом, используя **текст**."},
#                 {"role": "user", "content": f"Контекст: {context}\n\nВопрос: {query}"}
#             ]
#         )
#         answer = response.choices[0].message.content  # Извлекаем текст ответа
#     except Exception as e:
#         answer = f"Ошибка при обработке запроса: {str(e)}"
    
#     await message.answer(answer, parse_mode="Markdown")

# async def main():
#     await load_documents()  # Загружаем документы перед стартом бота
#     dp.include_router(router)
#     await dp.start_polling(bot)

# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         print("Бот выключен.")