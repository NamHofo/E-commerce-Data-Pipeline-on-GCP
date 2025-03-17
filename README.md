# Cloud Infrastructure and Data Processing with GCP & MongoDB
## Tổng quan

Dự án này tập trung vào việc thiết lập hạ tầng đám mây trên Google Cloud Platform (GCP), làm việc với MongoDB và xử lý dữ liệu định vị IP. Bộ dữ liệu sử dụng trong dự án là **Glamira dataset**. Mục tiêu là xây dựng một pipeline để xử lý dữ liệu thô, trích xuất thông tin liên quan và lưu trữ kết quả có cấu trúc để phân tích sâu hơn.

## Mục tiêu

- Hiểu cách thiết lập hạ tầng đám mây trên GCP
- Làm việc với MongoDB để lưu trữ và truy vấn dữ liệu
- Thực hiện xử lý dữ liệu cơ bản với Python
- Áp dụng tra cứu vị trí địa lý từ địa chỉ IP

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
        




























