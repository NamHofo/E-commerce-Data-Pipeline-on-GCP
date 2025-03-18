# Cloud Infrastructure and Data Processing with GCP & MongoDB

## Tổng quan

Dự án này tập trung vào việc thiết lập một pipeline dữ liệu mạnh mẽ sử dụng Google Cloud Platform (GCP), Python, MongoDB và IP2Location để xử lý và lưu trữ dữ liệu thô. Dự án bao gồm:

- Tạo bucket trên Google Cloud Storage
- Thiết lập máy ảo (VM) trên GCP
- Nhập dữ liệu thô vào MongoDB
- Làm giàu dữ liệu IP với thông tin định vị địa lý
- Trích xuất tên sản phẩm từ URL
- Xuất dữ liệu đã xử lý thành file CSV để sử dụng sau này

---

## Mục tiêu

- Hiểu cách thiết lập hạ tầng đám mây trên GCP
- Làm việc với MongoDB để lưu trữ và truy vấn dữ liệu
- Thực hiện xử lý dữ liệu cơ bản với Python
- Áp dụng tra cứu vị trí địa lý từ địa chỉ IP

---

## Cấu Trúc Dự Án

1. **Thiết Lập GCP**
    - Tạo bucket Google Cloud Storage
    - Thiết lập xác thực bằng Service Account
2. **Thiết Lập Máy Ảo**
    - Cấu hình một instance VM trên GCP
    - Cài đặt MongoDB trên VM
3. **Tải Dữ Liệu Ban Đầu**
    - Nhập dữ liệu thô vào MongoDB từ bucket GCP
4. **Xử Lý Định Vị IP**
    - Làm giàu dữ liệu IP với thông tin định vị bằng IP2Location
5. **Thu Thập Tên Sản Phẩm**
    - Trích xuất tên sản phẩm từ URL và lưu vào CSV
6. **Tài Liệu & Kiểm Thử**

---

## Hướng dẫn cài đặt

### Yêu cầu

- Tài khoản Google Cloud Platform (GCP)
- Đã tạo một dự án trên GCP
- Đã thiết lập máy ảo (VM) trên GCP
- Đã tạo Google Cloud Storage (GCS) bucket
- Đã cài đặt MongoDB trên VM
- Đã cài đặt Python 3

### Thiết lập môi trường

### 1. Thiết lập GCP

- Tạo tài khoản GCP và dự án mới
- Kích hoạt các API cần thiết (Compute Engine, Cloud Storage, v.v.)
- Tải xuống **Glamira dataset**

### 2. Thiết lập GCS

- Tạo Google Cloud Storage bucket
- Cấu hình xác thực bằng tài khoản dịch vụ
- Tải dữ liệu thô lên GCS

### 3. Thiết lập máy ảo (VM)

- Tạo một máy ảo trên GCP
- Cài đặt MongoDB:
    
    ```
    wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    sudo apt-get update
    sudo apt-get install -y mongodb-org
    sudo systemctl start mongod
    sudo systemctl enable mongod
    ```
    
- Kiểm tra MongoDB đã hoạt động:
    
    ```
    mongosh
    ```
    

---

## Nhập Dữ Liệu Vào MongoDB

Vì đã upload file glamira_ubl_oct2019_nov2019.tar.gz lên buckets gcp, nên ở bước này, thì cần download file từ bucket về VM.

### 1) Mount bucket to VM

1. Tải gcsfuse

```bash
export GCSFUSE_REPO=gcsfuse-`lsb_release -c -s`
echo "deb http://packages.cloud.google.com/apt $GCSFUSE_REPO main" | sudo tee /etc/apt/sources.list.d/gcsfuse.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo apt update
sudo apt install gcsfuse -y
```

2. Tạo 1 directory để mount bucket

```bash
mkdir ~/gcs_bucket
```

3. Mount bucket

```bash
gcsfuse bucket_project05 ~/gcs_bucket
```

Error: Với cách này khá khó vì dung lượng VM chỉ có 10GB và có dính tới các quyền truy cập trên Buckets → Nên mở rộng dung lượng VM và giải nén file 

### Mở rộng dung lượng VM

 Bước 1: Cài đặt `sfdisk` , `growpart`  và `cloud-guest-utils`

```bash
sudo apt update
sudo apt install fdisk cloud-guest-utils -y
sudo apt install cloud-guest-utils -y
```

 Bước 2: Chạy lại lệnh mở rộng phân vùng

```bash
sudo growpart /dev/sda 1
sudo resize2fs /dev/sda1
```

### Giải nén file data vào 1 folder tên là extracted_data/

```bash
# Tạo thư mục để chứa file giải nén
mkdir -p extracted_data

# Sao chép file từ GCS về VM
gsutil cp gs://bucket_project05/glamira_ubl_oct2019_nov2019.tar.gz .

# Giải nén file vào thư mục extracted_data
tar -xzvf glamira_ubl_oct2019_nov2019.tar.gz -C extracted_data/
```

## Import raw data into MongoDB

```bash
mongorestore --db countly --collection summary 
extracted_data/dump/countly/summary.bson
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

4. Kiểm tra số lượng document đã import:

```bash
db.summary.countDocuments()
```

5. Kiểm tra indexes đã tạo:

```bash
db.summary.getIndexes()
```

### 2. Xử Lý Định Vị IP

### Cài đặt thư viện ip2location

Cập nhật danh sách gói của hệ thống:

```bash
sudo apt update && sudo apt upgrade -y
```

Cài đặt python và pip

```bash
sudo apt install python3 python3-pip -y
```

Cài đặt thư viện `ip2location`

```bash
pip install ip2location
```

### Write Python script

1. Import pymongo

```sql
pip install pymongo
```

2. **Connect to MongoDB**
   
    Code trong file **project05_code.py**

3. Up file code lên VM
4. Up file IP2LOCATION-LITE-DB5.IPV6.BIN lên VM để load cơ sở dữ liệu IP2Location

### Chạy Script

```
python3 project05_code.py
```

### 3. Thu Thập Tên Sản Phẩm

### Trích Xuất Tên Sản Phẩm

```
db.summary_with_location.aggregate([
  { $match: { collection: { $in: ["view_product_detail", "select_product_option", "select_product_option_quality"] } } },
  { $group: { _id: "$product_id", current_url: { $first: "$current_url" } } },
  { $project: { _id: 1, product_name: { $arrayElemAt: [{ $split: [{ $arrayElemAt: [{ $split: [{ $arrayElemAt: [{ $split: ["$current_url", "/"] }, -1] }, "?"] }, 0] }, "."] }, 0] } } },
  { $out: "temp_results" }
])
```

### Xuất ra file CSV

```
mongoexport --db countly --collection temp_results --type=csv --fields _id,product_name --out output.csv
```

---

## Xử Lý Sự Cố

### **Lỗi Khởi Động MongoDB (exit-code 14)**

- Kiểm tra log: `sudo cat /var/log/mongodb/mongod.log`
- Sửa quyền:
    
    ```
    sudo chown -R mongodb:mongodb /var/lib/mongodb
    sudo chmod -R 755 /var/lib/mongodb /var/log/mongodb
    ```
    
- Xóa file socket lỗi:
    
    ```
    sudo rm -f /tmp/mongodb-27017.sock
    ```
    

### **Lỗi Quyền Truy Cập GCS**

- Đảm bảo Service Account có vai trò `storage.objectViewer`.

### **Hết Dung Lượng Đĩa**

- Mở rộng dung lượng đĩa VM và điều chỉnh phân vùng:
    
    ```
    sudo growpart /dev/sda 1
    sudo resize2fs /dev/sda1
    ```
    

---

## Cải tiến trong tương lai

- Tự động hóa xử lý dữ liệu bằng Cloud Functions
- Tối ưu hóa chỉ mục cơ sở dữ liệu để truy vấn nhanh hơn
- Tích hợp các công cụ trực quan hóa để phân tích dữ liệu tốt hơn

![gvto.svg](image/gvto.svg)
