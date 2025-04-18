# Cloud Infrastructure and Data Processing with GCP & MongoDB

## Tổng quan

Dự án này tập trung vào việc thiết lập một pipeline dữ liệu mạnh mẽ sử dụng Google Cloud Platform (GCP), Python, MongoDB và IP2Location để xử lý và lưu trữ dữ liệu thô. Dự án bao gồm:

- Tạo bucket trên Google Cloud Storage
- Thiết lập máy ảo (VM) trên GCP
- Nhập dữ liệu thô vào MongoDB
- Làm giàu dữ liệu IP với thông tin định vị địa lý
- Trích xuất tên sản phẩm từ URL
- Xuất dữ liệu đã xử lý thành file CSV để sử dụng sau này

## Mục tiêu

- Hiểu cách thiết lập hạ tầng đám mây trên GCP
- Làm việc với MongoDB để lưu trữ và truy vấn dữ liệu
- Thực hiện xử lý dữ liệu cơ bản với Python
- Áp dụng tra cứu vị trí địa lý từ địa chỉ IP
- Tối ưu hóa hiệu suất trích xuất tên sản phẩm từ URL

## Tổng quan về dữ liệu

Bộ dữ liệu này được lưu trữ trong MongoDB dưới collection `summary_with_location`, ghi lại các sự kiện tương tác của người dùng trên một nền tảng thương mại điện tử (ví dụ: Glamira.fr). Mỗi tài liệu đại diện cho một hành động cụ thể của người dùng, chẳng hạn như xem chi tiết sản phẩm (`view_product_detail`), kèm theo thông tin chi tiết về thiết bị, vị trí, thời gian, và các tham số liên quan đến sản phẩm.

### Đặc điểm chính:

- **Mục đích:** Theo dõi hành vi người dùng, hỗ trợ phân tích trải nghiệm người dùng và tối ưu hóa chiến dịch tiếp thị.
- **Định dạng:** Dữ liệu dạng JSON, chứa các trường đơn (string, number, boolean) và các trường lồng nhau (array, object).
- **Thông tin chính bao gồm:**
  - **Danh tính người dùng:** `user_id_db`, `device_id`, `email_address`.
  - **Thời gian:** `time_stamp` (Unix epoch), `local_time` (datetime string).
  - **Vị trí:** `ip` và thông tin địa lý chi tiết trong `location_info` (quốc gia, vùng, thành phố, tọa độ).
  - **Hành vi:** `current_url`, `referrer_url`, `collection`, `product_id`, `option`.
  - **Thiết bị:** `user_agent`, `resolution`.
  - **Tiếp thị:** `utm_source`, `utm_medium`, `recommendation`, `show_recommendation`.
- **Kích thước mẫu:** Mỗi tài liệu đại diện cho một sự kiện riêng lẻ, với các trường tùy chọn có thể trống (ví dụ: `utm_source`, `utm_medium`).

## Cấu Trúc Dự Án

1. [Thiết Lập Hạ Tầng GCP](#Thiết-Lập-Hạ-Tầng-GCP)

   - Tạo bucket trên Google Cloud Storage (GCS) để lưu trữ dữ liệu thô.
   - Thiết lập xác thực bằng Service Account để truy cập GCS và các dịch vụ GCP khác.

2. [Cấu Hình Máy Ảo (VM)](#Cấu-Hình-Máy-Ảo-(VM))

   - Tạo và cấu hình instance VM trên GCP Compute Engine.
   - Cài đặt MongoDB, Python, và các thư viện cần thiết (`playwright`, `pymongo`, `psutil`, `beautifulsoup4`).

3. [Nhập Dữ Liệu Vào MongoDB](#Nhập-Dữ-Liệu-Vào-MongoDB)

   - Tải file dữ liệu (`glamira_ubl_oct2019_nov2019.tar.gz`) từ GCS về VM.
   - Giải nén và nhập dữ liệu vào MongoDB (collection `summary` trong database `countly`).

4. [Xử Lý Định Vị IP](#Xử-Lý-Định-Vị-IP)

-  - Sử dụng thư viện `ip2location` và cơ sở dữ liệu `IP2LOCATION-LITE-DB5.IPV6.BIN` để thêm thông tin định vị địa lý (quốc gia, thành phố, tọa độ) vào collection `summary_with_location`.

5. [Thu Thập Tên Sản Phẩm](#Thu-Thập-Tên-Sản-Phẩm)
-  - [Web Crawling với Playwright[:
     - Truy vấn `summary_with_location` để lấy danh sách `product_id` và `current_url`, lưu vào collection `product_id_and_url`.
     - Sử dụng Playwright và đa luồng (`ThreadPoolExecutor`) để crawl tên sản phẩm từ HTML (ưu tiên thẻ `<span class="base">`).
     - Tối ưu hiệu suất: 4 luồng, độ trễ 1.5 giây, kiểm tra bộ nhớ (80% ngưỡng), user-agent ngẫu nhiên.
     - Ghi kết quả vào `product_names.csv` và các URL thất bại vào `failed_urls.txt`.

6. [Kiểm Thử và Giám Sát](#Kiểm-Thử-và-Giám-Sát)

   - Kiểm tra dữ liệu trong MongoDB (`summary`, `summary_with_location`, `product_id_and_url`, `temp_results`).
   - Theo dõi log (`crawl_log.txt`) để phát hiện lỗi (timeout, chống bot, bộ nhớ cao).
   - Xử lý lỗi cụ thể, như `Event loop is closed!`, bằng cách quản lý vòng lặp sự kiện trong đa luồng.
   - Đánh giá hiệu suất (thời gian chạy, sử dụng tài nguyên) và điều chỉnh tham số nếu cần.

7. [Tài Liệu Hóa và Báo Cáo](#Tài-Liệu-Hóa-và-Báo-Cáo)

   - Ghi lại quy trình, lỗi gặp phải, và cách khắc phục.
   - Tạo báo cáo chi tiết (Markdown) bao gồm hướng dẫn cài đặt, chạy script, và các cải tiến tương lai.

## Hướng dẫn cài đặt

### Yêu cầu

- Tài khoản Google Cloud Platform (GCP)
- Đã tạo một dự án trên GCP
- Đã thiết lập máy ảo (VM) trên GCP
- Đã tạo Google Cloud Storage (GCS) bucket
- Đã cài đặt MongoDB trên VM
- Đã cài đặt Python 3
- Các thư viện Python: `playwright`, `pymongo`, `psutil`, `beautifulsoup4`

### Thiết lập môi trường

#### Thiết Lập Hạ Tầng GCP

- Tạo tài khoản GCP và dự án mới
- Kích hoạt các API cần thiết (Compute Engine, Cloud Storage, v.v.)
- Tạo Google Cloud Storage bucket
- Cấu hình xác thực bằng tài khoản dịch vụ
- Tải dữ liệu thô (`glamira_ubl_oct2019_nov2019.tar.gz`) lên GCS

#### Cấu Hình Máy Ảo (VM)

- Tạo một máy ảo trên GCP

- Cài đặt MongoDB:

  ```bash
  wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
  echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
  sudo apt-get update
  sudo apt-get install -y mongodb-org
  sudo systemctl start mongod
  sudo systemctl enable mongod
  ```

- Kiểm tra MongoDB đã hoạt động:

  ```bash
  mongosh
  ```

- Cài đặt Python và các thư viện:

  ```bash
  sudo apt update
  sudo apt install python3 python3-pip -y
  pip install playwright pymongo psutil beautifulsoup4
  playwright install
  ```

## Nhập Dữ Liệu Vào MongoDB

Vì đã upload file `glamira_ubl_oct2019_nov2019.tar.gz` lên buckets GCP, nên ở bước này, cần download file từ bucket về VM.

### 1) Mount bucket to VM

1. Tải `gcsfuse`:

   ```bash
   export GCSFUSE_REPO=gcsfuse-`lsb_release -c -s`
   echo "deb http://packages.cloud.google.com/apt $GCSFUSE_REPO main" | sudo tee /etc/apt/sources.list.d/gcsfuse.list
   curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
   sudo apt update
   sudo apt install gcsfuse -y
   ```

2. Tạo directory để mount bucket:

   ```bash
   mkdir ~/gcs_bucket
   ```

3. Mount bucket:

   ```bash
   gcsfuse bucket_project05 ~/gcs_bucket
   ```

**Lưu ý**: Nếu gặp vấn đề về quyền truy cập hoặc dung lượng VM (10GB), mở rộng dung lượng VM và giải nén file.

### Mở rộng dung lượng VM

**Bước 1**: Cài đặt `sfdisk`, `growpart`, và `cloud-guest-utils`:

```bash
sudo apt update
sudo apt install fdisk cloud-guest-utils -y
```

**Bước 2**: Mở rộng phân vùng:

```bash
sudo growpart /dev/sda 1
sudo resize2fs /dev/sda1
```

### Giải nén file data vào thư mục `extracted_data/`:

```bash
mkdir -p extracted_data
gsutil cp gs://bucket_project05/glamira_ubl_oct2019_nov2019.tar.gz .
tar -xzvf glamira_ubl_oct2019_nov2019.tar.gz -C extracted_data/
```

### Import raw data vào MongoDB:

```bash
mongorestore --db countly --collection summary extracted_data/dump/countly/summary.bson
```

**Kiểm tra dữ liệu sau khi import**

1. Mở Mongo shell:

   ```bash
   mongosh --host 127.0.0.1 --port 27017
   ```

2. Chuyển sang database `countly`:

   ```bash
   use countly
   ```

3. Kiểm tra dữ liệu:

   ```bash
   db.summary.findOne()
   ```

4. Kiểm tra số lượng document:

   ```bash
   db.summary.countDocuments()
   ```

5. Kiểm tra indexes:

   ```bash
   db.summary.getIndexes()
   ```

## Xử Lý Định Vị IP

### Cài đặt thư viện `ip2location`

Cập nhật danh sách gói:

```bash
sudo apt update && sudo apt upgrade -y
```

Cài đặt Python và pip:

```bash
sudo apt install python3 python3-pip -y
```

Cài đặt `ip2location`:

```bash
pip install ip2location
```

### Write Python script

1. Cài đặt `pymongo`:

   ```bash
   pip install pymongo
   ```

2. **Kết nối MongoDB**:

   - Code trong file `project05_code.py` (đã được upload lên VM).
   - Upload file cơ sở dữ liệu `IP2LOCATION-LITE-DB5.IPV6.BIN` lên VM để tra cứu vị trí địa lý.

3. **Chạy script**:

   ```bash
   python3 ip_location_processing.py
   ```

## Thu Thập Tên Sản Phẩm

### Trích Xuất Tên Sản Phẩm

Để trích xuất tên sản phẩm từ các URL trong collection `summary_with_location`, chúng ta sử dụng phương pháp **web crawling** bằng Python với Playwright.

#### Web Crawling với Playwright (Python)

Để lấy tên sản phẩm chính xác hơn, chúng ta sử dụng Playwright để crawl nội dung HTML của các URL và trích xuất tên sản phẩm từ các thẻ như `<span>`, `<h1>`, `<title>`, hoặc `<meta>`. Phương pháp này được tối ưu hóa với đa luồng để giảm thời gian chạy.

##### Cài đặt Playwright:

```bash
pip install playwright
playwright install
```

##### Quy trình:

1. **Lấy danh sách URL từ MongoDB**:

   - Truy vấn collection `summary_with_location` để lấy `product_id` và danh sách `current_url`:

     ```javascript
     db.summary_with_location.aggregate([
       { $match: { collection: { $in: ["view_product_detail", "select_product_option", "select_product_option_quality"] } } },
       { $group: { _id: "$product_id", urls: { $addToSet: "$current_url" } } },
       { $out: "product_id_and_url" }
     ])
     ```

   - Lưu kết quả vào collection `product_id_and_url`.

2. **Python script để crawl**:

   - Sử dụng script `web_crawler_multithread.py` (đã upload lên VM) để crawl tên sản phẩm.
   - Script sử dụng Playwright với đa luồng (`ThreadPoolExecutor`) để crawl song song, tối ưu hiệu suất:
     - Giới hạn 4 luồng (`MAX_THREADS = 4`) để tận dụng CPU đa lõi.
     - Độ trễ 1.5 giây (`DELAY_BETWEEN_REQUESTS = 1.5`) để tránh chống bot.
     - Kiểm tra bộ nhớ (`MEMORY_THRESHOLD = 80%`) để ngăn crash.
     - User-agent ngẫu nhiên để giảm nguy cơ bị chặn.
     - Tải trang với `wait_until="domcontentloaded"` để tăng tốc.
     - Ưu tiên tìm tên sản phẩm trong thẻ `<span class="base">`.

3. **Xử lý lỗi**:

   - Retry logic (3 lần thử) cho các lỗi tạm thời như timeout.
   - Ghi các URL thất bại vào `failed_urls.txt`.
   - Đồng bộ ghi file CSV với `threading.Lock` để tránh race condition.

##### Chạy script:

```bash
python3 product_name_crawl.py
```

##### Kết quả:

- File `product_names.csv` chứa các cặp `product_id` và tên sản phẩm.
- File `failed_urls.txt` chứa các URL không crawl được (do timeout, chống bot, hoặc lỗi khác).
- Log chi tiết trong `crawl_log.txt`, bao gồm % bộ nhớ, lỗi, và trạng thái mỗi URL.

##### Tối ưu hóa hiệu suất:

- **Đa luồng**: Sử dụng 4 luồng để crawl song song, giảm thời gian chạy từ \~2.75 phút (async, 2 trình duyệt) xuống \~1.2 phút cho 50 URLs.
- **Kiểm tra tài nguyên**: Ngừng crawl nếu bộ nhớ vượt 80%.
- **Chống bot**: User-agent ngẫu nhiên và độ trễ 1.5 giây để giảm nguy cơ bị chặn.
- **Tải trang nhanh**: Dùng `wait_until="domcontentloaded"` để giảm thời gian tải.

##### Xử lý lỗi cụ thể:

- **Lỗi** `Event loop is closed!`: Đã sửa bằng cách tạo vòng lặp sự kiện riêng cho mỗi luồng và đóng nó sau khi hoàn thành.
- **Timeout**: Retry 3 lần với độ trễ tăng dần (exponential backoff).
- **Chống bot**: Nếu gặp lỗi 429/403, tăng độ trễ hoặc dùng proxy.

#### Xuất ra file CSV (từ MongoDB):

Nếu sử dụng aggregation pipeline:

```bash
mongoexport --db countly --collection temp_results --type=csv --fields _id,product_name --out output.csv
```

Nếu sử dụng Playwright, file `product_names.csv` đã được tạo bởi script.


## Kiểm Thử và Giám Sát

- **Kiểm tra dữ liệu**:

  - Xác minh dữ liệu trong các collection MongoDB (`summary`, `summary_with_location`, `product_id_and_url`, `temp_results`) bằng lệnh:

    ```bash
    mongosh --host 127.0.0.1 --port 27017
    use countly
    db.summary.findOne()
    db.summary_with_location.countDocuments()
    ```

  - Đảm bảo số lượng document và cấu trúc dữ liệu đúng như mong đợi.

- **Theo dõi log**:

  - Kiểm tra file `crawl_log.txt` để phát hiện lỗi (timeout, chống bot, bộ nhớ cao).
  - Ví dụ lỗi: `Event loop is closed!` được xử lý bằng cách quản lý vòng lặp sự kiện riêng trong đa luồng.

- **Đánh giá hiệu suất**:

  - Đo thời gian chạy của script `web_crawler_multithread.py` (ước tính \~1.2 phút cho 50 URLs).

  - Theo dõi % CPU và RAM bằng:

    ```bash
    top
    free -h
    ```

  - Nếu bộ nhớ &gt; 80%, giảm `MAX_THREADS` trong script.

- **Xử lý lỗi**:

  - Timeout: Tăng độ trễ hoặc retry thêm.
  - Chống bot (lỗi 429/403): Dùng proxy hoặc tăng `DELAY_BETWEEN_REQUESTS`.
  - Bộ nhớ cao: Giảm số luồng hoặc nâng cấp VM.

## Xử Lý Sự Cố

### Lỗi Khởi Động MongoDB (exit-code 14)

- Kiểm tra log:

  ```bash
  sudo cat /var/log/mongodb/mongod.log
  ```

- Sửa quyền:

  ```bash
  sudo chown -R mongodb:mongodb /var/lib/mongodb
  sudo chmod -R 755 /var/lib/mongodb /var/log/mongodb
  ```

- Xóa file socket lỗi:

  ```bash
  sudo rm -f /tmp/mongodb-27017.sock
  ```

### Lỗi Quyền Truy Cập GCS

- Đảm bảo Service Account có vai trò `storage.objectViewer`.

### Hết Dung Lượng Đĩa

- Mở rộng dung lượng đĩa VM:

  ```bash
  sudo growpart /dev/sda 1
  sudo resize2fs /dev/sda1
  ```

### Lỗi Web Crawling với Playwright

- **Lỗi** `Event loop is closed!`:
  - **Nguyên nhân**: Xung đột vòng lặp sự kiện trong đa luồng.
  - **Khắc phục**: Sử dụng `playwright.async_api` và tạo vòng lặp sự kiện riêng cho mỗi luồng.
- **Lỗi Timeout (**`Page.goto: Timeout 60000ms exceeded`**)**:
  - **Nguyên nhân**: Trang tải chậm hoặc chống bot.
  - **Khắc phục**: Retry 3 lần, tăng độ trễ, hoặc dùng proxy.
- **Lỗi 429/403 (Chống bot)**:
  - **Nguyên nhân**: Website (Glamira) phát hiện bot.
  - **Khắc phục**: User-agent ngẫu nhiên, tăng độ trễ, hoặc dùng proxy xoay vòng.
- **Bộ nhớ cao**:
  - **Nguyên nhân**: 4 trình duyệt tiêu tốn \~4–8GB RAM.
  - **Khắc phục**: Giảm `MAX_THREADS = 2` nếu RAM &lt; 8GB, kiểm tra `MEMORY_THRESHOLD = 80%`.

## Tài Liệu Hóa và Báo Cáo

- **Quy trình**: Ghi lại chi tiết các bước từ thiết lập GCP, nhập dữ liệu, xử lý IP, đến trích xuất tên sản phẩm.

- **Xử lý lỗi**: Tài liệu hóa các lỗi phổ biến (MongoDB, GCS, Playwright) và cách khắc phục.

- **Báo cáo**:

  - Tạo file Markdown (`Cloud_Infrastructure_and_Data_Processing_Report.md`) bao gồm:
    - Mô tả dự án, mục tiêu, và cấu trúc.
    - Hướng dẫn cài đặt và chạy script.
    - Phân tích hiệu suất và so sánh phương pháp (aggregation pipeline vs. web crawling).
    - Đề xuất cải tiến tương lai.

- **Hướng dẫn sử dụng**: Báo cáo có thể được render thành PDF/HTML bằng Pandoc:

  ```bash
  pandoc Cloud_Infrastructure_and_Data_Processing_Report.md -o report.pdf
  ```

## Cải tiến trong tương lai

- **Tự động hóa pipeline**: Sử dụng Cloud Functions hoặc Cloud Run để tự động chạy script crawl và xử lý dữ liệu khi có dữ liệu mới trong GCS.

- **Tối ưu hóa MongoDB**:

  - Tạo chỉ mục (index) cho `product_id` và `current_url` để tăng tốc truy vấn:

    ```javascript
    db.summary_with_location.createIndex({ "product_id": 1, "current_url": 1 })
    ```

- **Tăng tốc crawling**:

  - Dùng proxy xoay vòng để tránh chống bot.

  - Tối ưu BeautifulSoup bằng `lxml` parser:

    ```bash
    pip install lxml
    ```

- **Giảm tài nguyên**: Tái sử dụng trình duyệt Playwright cho nhiều URL trong cùng luồng để giảm overhead khởi tạo.

- **Phân tích dữ liệu**: Tích hợp BigQuery để phân tích dữ liệu và trực quan hóa với Looker Studio.

- **Giám sát hiệu suất**: Thêm monitoring (ví dụ: Cloud Monitoring) để theo dõi % CPU, RAM, và lỗi crawling.

## Kết luận

Phần **Thu Thập Tên Sản Phẩm** đã được cải tiến với phương pháp web crawling sử dụng Playwright và đa luồng, giảm thời gian chạy từ \~2.75 phút (async) xuống \~1.2 phút cho 50 URLs, đồng thời đảm bảo độ chính xác cao bằng cách lấy tên sản phẩm từ HTML. Lỗi `Event loop is closed!` được khắc phục bằng cách dùng `playwright.async_api` và quản lý vòng lặp sự kiện riêng cho mỗi luồng. Các biện pháp như kiểm tra bộ nhớ, user-agent ngẫu nhiên, và đồng bộ ghi file giữ hệ thống ổn định. Dự án có thể được mở rộng với tự động hóa, tối ưu hóa MongoDB, và tích hợp phân tích dữ liệu để nâng cao hiệu quả.

---

### Hướng dẫn chạy phần mới

1. **Chuẩn bị**:

   - Đảm bảo VM có RAM ≥ 8GB, CPU ≥ 4 lõi. Kiểm tra:

     ```bash
     free -h
     lscpu
     ```

   - Cài đặt thư viện:

     ```bash
     pip install playwright pymongo psutil beautifulsoup4
     playwright install
     ```

2. **Tạo collection** `product_id_and_url`:

   ```javascript
   db.summary_with_location.aggregate([
     { $match: { collection: { $in: ["view_product_detail", "select_product_option", "select_product_option_quality"] } } },
     { $group: { _id: "$product_id", urls: { $addToSet: "$current_url" } } },
     { $out: "product_id_and_url" }
   ])
   ```

3. **Cập nhật** `config.py`:

   ```python
   mongo_port = "mongodb://localhost:27017"
   db_name = "countly"
   product_id_and_url_collection = "product_id_and_url"
   ```

4. **Chạy script**:

   ```bash
   python3 web_crawler_multithread.py
   ```

5. **Kiểm tra kết quả**:

   - Xem `product_names.csv` và `failed_urls.txt`.
   - Theo dõi log (`crawl_log.txt`) để kiểm tra lỗi, % bộ nhớ, và hiệu suất.
  
   ![gvto.svg](attachment:b2796a21-acbc-4bb6-8865-0b5af6a5afe1:gvto.svg)
