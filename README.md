# Cloud Infrastructure and Data Processing with GCP & MongoDB
## Tổng quan

Dự án này tập trung vào việc thiết lập một pipeline dữ liệu mạnh mẽ sử dụng Google Cloud Platform (GCP), Python, MongoDB và IP2Location để xử lý và lưu trữ dữ liệu thô. Dự án bao gồm việc tạo bucket trên Google Cloud Storage, thiết lập máy ảo (VM), nhập dữ liệu thô vào MongoDB, làm giàu dữ liệu IP với thông tin định vị địa lý, trích xuất tên sản phẩm từ URL và xuất dữ liệu đã xử lý thành file CSV để sử dụng sau này.

## Mục tiêu

- Hiểu cách thiết lập hạ tầng đám mây trên GCP
- Làm việc với MongoDB để lưu trữ và truy vấn dữ liệu
- Thực hiện xử lý dữ liệu cơ bản với Python
- Áp dụng tra cứu vị trí địa lý từ địa chỉ IP

## Cấu Trúc Dự Án
1. Thiết Lập GCP
    ◦ Tạo bucket Google Cloud Storage
    ◦ Thiết lập xác thực bằng Service Account
2. Thiết Lập Máy Ảo
    ◦ Cấu hình một instance VM trên GCP
    ◦ Cài đặt MongoDB trên VM
3. Tải Dữ Liệu Ban Đầu
    ◦ Nhập dữ liệu thô vào MongoDB từ bucket GCP
4. Xử Lý Định Vị IP
    ◦ Làm giàu dữ liệu IP với thông tin định vị bằng IP2Location
5. Thu Thập Tên Sản Phẩm
    ◦ Trích xuất tên sản phẩm từ URL và lưu vào CSV
6. Tài Liệu & Kiểm Thử

## Hướng dẫn cài đặt

### Yêu cầu

- Tài khoản Google Cloud Platform (GCP)
- Đã tạo một dự án trên GCP
- Đã thiết lập máy ảo (VM) trên GCP
- Đã tạo Google Cloud Storage (GCS) bucket
- Đã cài đặt MongoDB trên VM
- Đã cài đặt Python 3

### Thiết lập môi trường

1. **Thiết lập GCP**
    - Tạo tài khoản GCP và dự án mới
    - Kích hoạt các API cần thiết (Compute Engine, Cloud Storage, v.v.)
    - Tải xuống **Glamira dataset**
2. **Thiết lập GCS**
    - Tạo Google Cloud Storage bucket
    - Cấu hình xác thực bằng tài khoản dịch vụ
    - Tải dữ liệu thô lên GCS
3. **Thiết lập máy ảo (VM)**
    - Tạo một máy ảo trên GCP
    - Cài đặt MongoDB: `mongosh` (MongoDB Shell) trên Debian 11

    1. Thêm kho lưu trữ MongoDB:
    
    ```bash
    wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    sudo apt-get update
    
    ```
    
    2. Cài đặt MongoDB:
    
    ```bash
    sudo apt-get install -y mongodb-org
    ```
    
    3. Khởi động MongoDB:
    
    ```bash
    sudo systemctl start mongod
    sudo systemctl enable mongod
    
    ```
    
    4. Kiểm tra `mongosh` đã hoạt động chưa
    
    ```bash
    mongosh
    ```
    
    ### Lưu ý
    
    - MongoDB của không khởi động được do lỗi **"exit-code 14"**, thường liên quan đến quyền truy cập, thiếu thư mục dữ liệu hoặc file cấu hình sai.
    - ### Cách xử lý

    Kiểm tra nhật ký lỗi
    
    ```bash
    sudo cat /var/log/mongodb/mongod.log
    ```
    
    Lỗi chính trong log là:
    
    `"Failed to unlink socket file" -> "Operation not permitted"`
    
    MongoDB không thể xóa file socket `/tmp/mongodb-27017.sock`, dẫn đến lỗi khởi động.
    
    → 

     **Xóa file socket lỗi**
    
    ```bash
    sudo rm -f /tmp/mongodb-27017.sock
    ```
    
    **Kiểm tra quyền thư mục `/tmp`**
    
    Đảm bảo thư mục `/tmp` có quyền phù hợp:
    
    **Xác minh quyền MongoDB**
    
    Chắc chắn rằng MongoDB có quyền trên thư mục dữ liệu:
    
    ```bash
    sudo chown -R mongodb:mongodb /var/lib/mongodb /var/log/mongodb
    sudo chmod -R 755 /var/lib/mongodb /var/log/mongodb
    ```
    
    Khởi động lại MongoDB
    ## Kết nối tới VM từ local

    Cài đặt project đang thực hiện
    
    Tạo SSH Key Mới Trên Máy Local
    
    Thêm Key Mới Vào Metadata của VM
    
    Kết Nối Lại Bằng SSH
## 3. Tải Dữ Liệu Ban Đầu
### Tải Xuống và Giải Nén Dữ Liệu
1. Cấp quyền đọc cho Service Account của VM:
2. Tải file từ bucket:
3. Giải nén file:
### Nhập Vào MongoDB
1. Khôi phục dữ liệu vào MongoDB:
```bash
    mongosh
    use countly
    db.summary.countDocuments()
```
### 4. Xử Lý Định Vị IP

### Cài Đặt Thư Viện

1. Cài đặt Python và các thư viện cần thiết:
    
2. Tải cơ sở dữ liệu IP2Location và script lên VM:
    
### Chạy Script

1. Tạo collection mới:
```bash
    use countly
    db.createCollection("summary_with_location")`
```
    `
    
3. Chạy script Python:

4. Kiểm tra kết quả:

### 5. Thu Thập Tên Sản Phẩm

### Trích Xuất Tên Sản Phẩm

1. Chạy truy vấn tổng hợp để trích xuất tên sản phẩm:

```bash
   db.summary_with_location.aggregate([
  { $match: { collection: { $in: ["view_product_detail", "select_product_option", "select_product_option_quality"] } } },
  { $group: { _id: "$product_id", current_url: { $first: "$current_url" } } },
  { $project: { _id: 1, product_name: { $arrayElemAt: [{ $split: [{ $arrayElemAt: [{ $split: [{ $arrayElemAt: [{ $split: ["$current_url", "/"] }, -1] }, "?"] }, 0] }, "."] }, 0] } } },
  { $out: "temp_results" }
])
```
2. Xuất ra file CSV:
    
```bash
   mongoexport --db countly --collection temp_results --type=csv --fields _id,product_name --out output.csv
```
    
3. Tải file CSV về máy local:
    
## Cách Sử Dụng

- **Khám Phá Dữ Liệu**: Sử dụng truy vấn MongoDB để phân tích collection summary_with_location (ví dụ: đếm số bản ghi theo quốc gia hoặc khu vực).
- **File Đầu Ra**: File output.csv chứa ID sản phẩm và tên tương ứng để xử lý tiếp.

---

## Xử Lý Sự Cố

- **Lỗi Khởi Động MongoDB (exit-code 14)**:
    - Kiểm tra log: sudo cat /var/log/mongodb/mongod.log
    - Sửa quyền: sudo chown -R mongodb:mongodb /var/lib/mongodb
    - Xóa file socket: sudo rm -f /tmp/mongodb-27017.sock
- **Lỗi Quyền Truy Cập GCS**:
    - Đảm bảo Service Account có vai trò storage.objectViewer.
- **Hết Dung Lượng Đĩa**:
    - Mở rộng dung lượng đĩa VM và điều chỉnh phân vùng:
        
        bash
        
        Thu gọnBọc lạiSao chép
        
        `sudo growpart /dev/sda 1
        sudo resize2fs /dev/sda1`

## Cải tiến trong tương lai

- Tự động hóa xử lý dữ liệu bằng Cloud Functions

- Tối ưu hóa chỉ mục cơ sở dữ liệu để truy vấn nhanh hơn

- Tích hợp các công cụ trực quan hóa để phân tích dữ liệu tốt hơn






