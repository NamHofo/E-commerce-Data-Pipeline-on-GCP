from pymongo import MongoClient, UpdateOne
import IP2Location
import logging
from config import mongo_port, db_name,old_collection_name,new_collection_name

# Cấu hình logging để hiển thị ra cả file và màn hình
logging.basicConfig(
    filename="ip_location_processing.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)


def process_ip_locations():
    """Xử lý dữ liệu từ MongoDB và cập nhật location cho từng IP, dùng bulk_write để tối ưu."""
    try:
        # Kết nối MongoDB
        client = MongoClient(mongo_port)
        db = client[db_name]
        old_collection = db[old_collection_name]
        new_collection = db[new_collection_name]

        # Khởi tạo thư viện IP2Location
        ip_db = IP2Location.IP2Location("IP2LOCATION-LITE-DB5.IPV6.BIN")

        batch_size = 1000  # Giảm batch size để tránh tốn RAM quá nhiều
        cursor = old_collection.find({"ip": {"$exists": True}})
        logging.info("Connected to MongoDB successfully!")

        bulk_operations = []
        total_processed = 0  # Biến đếm số lượng bản ghi đã xử lý

        for doc in cursor:
            ip_address = doc.get("ip")
            if ip_address:
                try:
                    record = ip_db.get_all(ip_address)
                    location_info = {
                        "ip": ip_address,
                        "country": record.country_long,
                        "region": record.region,
                        "city": record.city,
                        "latitude": record.latitude,
                        "longitude": record.longitude,
                    }
                    doc["location_info"] = location_info
                    logging.info(f"Processed IP: {ip_address} -> {location_info['country']}, {location_info['city']}")
                except Exception as e:
                    logging.error(f"Error processing IP {ip_address}: {e}")
                    doc["location_info"] = None
            else:
                doc["location_info"] = None

            # Thêm vào danh sách bulk update
            bulk_operations.append(UpdateOne({"_id": doc["_id"]}, {"$set": doc}, upsert=True))

            # Nếu đạt batch_size thì thực hiện bulk_write
            if len(bulk_operations) >= batch_size:
                new_collection.bulk_write(bulk_operations)
                total_processed += len(bulk_operations)
                logging.info(f"Inserted {total_processed} records into 'summary_with_location'")
                bulk_operations = []  # Reset batch

        # Xử lý batch còn lại
        if bulk_operations:
            new_collection.bulk_write(bulk_operations)
            total_processed += len(bulk_operations)
            logging.info(f"Inserted {total_processed} records into 'summary_with_location'")

        logging.info("Hoàn thành cập nhật toàn bộ bản ghi.")

    except Exception as e:
        logging.error(f"Error in processing IP locations: {e}")


if __name__ == "__main__":
    process_ip_locations()
