import os
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import shutil

# Путь для пользовательских документов и для базы данных Chroma
USER_DOCS_PATH = "./user_docs"
CHROMA_PATH = "./chroma_db"

def load_user_documents(docs_path):
    """Загрузка документов из директории пользователя."""
    documents = []
    
    # Отладка: выводим все файлы в папке
    print(f"Проверка файлов в папке {docs_path}:")
    for root, _, files in os.walk(docs_path):
        for file in files:
            print(f"Найден файл: {file}")  # Отладочный вывод
            if file.endswith(".md") or file.endswith(".rst"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    document_content = f.read()
                    if document_content.strip():  # Проверяем, что текст не пустой
                        documents.append((file, document_content))
                    else:
                        print(f"Предупреждение: файл {file} пуст.")
    print(f"Загружено {len(documents)} документов.")
    return documents

def sync_chroma_db(documents):
    """Синхронизация базы данных Chroma с новыми документами."""
    if not documents:
        raise ValueError("Не было загружено ни одного документа.")
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    texts, metadatas = [], []

    # Разделение текста на части
    for filename, content in documents:
        chunks = text_splitter.split_text(content)
        if chunks:
            print(f"Документ '{filename}' разбит на {len(chunks)} частей.")
        else:
            print(f"Документ '{filename}' не был разбит на части.")
        
        for chunk in chunks:
            texts.append(chunk)
            metadatas.append({"source": filename})

    # Отладка: проверим, что тексты и метаданные не пустые
    print(f"Найдено {len(texts)} частей текста и {len(metadatas)} метаданных.")

    if not texts:
        raise ValueError("Тексты пусты, невозможно продолжить.")

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Отладка: проверим, что embeddings создаются корректно
    try:
        embeddings_vectors = embeddings.embed_documents(texts)
        print(f"Сгенерировано {len(embeddings_vectors)} векторных представлений.")
    except Exception as e:
        raise ValueError(f"Ошибка при создании векторных представлений: {e}")

    # Создание или обновление базы данных Chroma
    chroma_db = Chroma.from_texts(texts, embeddings, metadatas=metadatas, persist_directory=CHROMA_PATH)
    print("✅ ChromaDB успешно обновлена!")
    return chroma_db

# Загрузка документов и синхронизация БД
documents = load_user_documents(USER_DOCS_PATH)
chroma_db = sync_chroma_db(documents)
