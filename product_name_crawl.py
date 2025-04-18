from bs4 import BeautifulSoup
import csv
import logging
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from config import mongo_port, db_name, product_id_and_url_collection
import psutil
import time
import random

# Cấu hình logging
logging.basicConfig(filename='crawl_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

FAILED_URLS_FILE = "failed_urls.txt"
MAX_RETRIES = 2
TIMEOUT = 60000  # 60 giây timeout
DELAY_BETWEEN_REQUESTS = 1.5  # Độ trễ giữa các yêu cầu
MONGO_CONNECTION_RETRIES = 3
MONGO_RETRY_DELAY = 2  # Giây chờ giữa các lần thử kết nối MongoDB
MAX_THREADS = 7  # Số luồng tối đa
MEMORY_THRESHOLD = 90  # Ngưỡng bộ nhớ (%)

# Danh sách user-agent để xoay vòng
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

# Khóa để đồng bộ ghi file
csv_lock = threading.Lock()
failed_lock = threading.Lock()

def connect_to_mongo(mongo_port, db_name, collection_name):
    for attempt in range(1, MONGO_CONNECTION_RETRIES + 1):
        try:
            client = MongoClient(
                mongo_port,
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000
            )
            client.admin.command('ping')
            db = client[db_name]
            collection = db[collection_name]
            logging.info("✅ Kết nối thành công tới MongoDB")
            return collection
        except (ServerSelectionTimeoutError, ConnectionFailure) as e:
            logging.error(f"❌ Lỗi kết nối MongoDB (lần thử {attempt}/{MONGO_CONNECTION_RETRIES}): {str(e)}")
            if attempt == MONGO_CONNECTION_RETRIES:
                raise Exception("❌ Không thể kết nối tới MongoDB sau nhiều lần thử")
            time.sleep(MONGO_RETRY_DELAY)
        except Exception as e:
            logging.error(f"❌ Lỗi MongoDB không xác định: {str(e)}")
            raise

async def get_product_name_async(url, retries=MAX_RETRIES):
    for attempt in range(1, retries + 1):
        browser = None
        page = None
        try:
            # Kiểm tra bộ nhớ
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > MEMORY_THRESHOLD:
                logging.error(f"❌ Bộ nhớ quá cao ({memory_percent}%) tại URL: {url}. Dừng tác vụ.")
                return None

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(user_agent=random.choice(USER_AGENTS))
                logging.info(f"🌐 Thử {attempt}/{retries} cho URL: {url} (Bộ nhớ: {memory_percent}% đã dùng)")
                await page.goto(url, timeout=TIMEOUT, wait_until="domcontentloaded")
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")

                # Tìm tên sản phẩm, ưu tiên span.base
                span_title = soup.find("span", class_="base", attrs={"data-ui-id": "page-title-wrapper"})
                if span_title and span_title.text.strip():
                    return span_title.text.strip()

                h1 = soup.find("h1")
                if h1 and h1.text.strip():
                    return h1.text.strip()

                title = soup.find("title")
                if title and title.text.strip():
                    return title.text.strip()

                meta = soup.find("meta", attrs={"name": "title"})
                if meta and meta.get("content"):
                    return meta["content"].strip()

                logging.info(f"⚠️ Không tìm thấy tên sản phẩm cho {url}")
                return None
        except PlaywrightTimeoutError as e:
            logging.error(f"❌ Lỗi timeout (thử {attempt}/{retries}) cho {url}: {e}")
            if attempt == retries:
                logging.error(f"❌ Đạt tối đa số lần thử cho {url}")
                return None
            await asyncio.sleep(attempt * 2)
        except Exception as e:
            logging.error(f"❌ Lỗi (thử {attempt}/{retries}) cho {url}: {e}")
            if attempt == retries:
                logging.error(f"❌ Đạt tối đa số lần thử cho {url}")
                return None
            await asyncio.sleep(attempt * 2)
        finally:
            if page:
                await page.close()
            if browser:
                await browser.close()
            await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

def get_product_name(url):
    # Chạy tác vụ async trong luồng
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(get_product_name_async(url))
        return result
    finally:
        loop.close()

def crawl_urls(docs):
    results = []
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_url = {}
        for doc in docs:
            product_id = doc.get("product_id")
            urls = doc.get("urls", [])
            for url in urls:
                future = executor.submit(get_product_name, url)
                future_to_url[future] = (product_id, url)

        for future in as_completed(future_to_url):
            product_id, url = future_to_url[future]
            try:
                result = future.result()
                results.append((product_id, url, result))
            except Exception as e:
                logging.error(f"❌ Lỗi luồng cho {url}: {e}")
                results.append((product_id, url, None))
    return results

def main():
    try:
        collection = connect_to_mongo(mongo_port, db_name, product_id_and_url_collection)
        logging.info(f"📦 Tổng số tài liệu trong collection: {collection.count_documents({})}")

        # Lấy tối đa 10 tài liệu, chỉ lấy trường cần thiết
        docs = list(collection.find({}, {"product_id": 1, "urls": 1}).limit(1000))

        # Crawl các URL
        results = crawl_urls(docs)

        # Ghi kết quả
        with open("product_names.csv", mode="w", newline="", encoding="utf-8") as csvfile, open(FAILED_URLS_FILE, "w", encoding="utf-8") as failed_file:
            writer = csv.writer(csvfile)
            writer.writerow(["product_id", "product_name"])

            for product_id, url, result in results:
                if isinstance(result, str) and result:
                    with csv_lock:
                        writer.writerow([product_id, result])
                    logging.info(f"✅ Tìm thấy: {result} cho product_id: {product_id}")
                else:
                    with failed_lock:
                        failed_file.write(f"{product_id},{url}\n")
                    logging.info(f"❌ Không tìm thấy tên sản phẩm cho URL: {url}")

        logging.info("🎉 HOÀN TẤT ghi tên sản phẩm vào file.")
    except Exception as e:
        logging.error(f"❌ Lỗi nghiêm trọng trong main: {str(e)}")
        raise

if __name__ == "__main__":
    main()