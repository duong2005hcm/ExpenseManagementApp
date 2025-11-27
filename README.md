#  Ứng dụng Quản Lý Chi Tiêu Cá Nhân

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-green.svg)](https://docs.python.org/3/library/tkinter.html)
[![Firebase](https://img.shields.io/badge/Database-Firebase-orange.svg)](https://firebase.google.com)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

**Ứng dụng quản lý chi tiêu cá nhân với giao diện trực quan và đồ thị thống kê, giúp bạn kiểm soát tài chính hiệu quả.**

## ✨ Tính Năng Nổi Bật

### 👤 Quản Lý Người Dùng
-  **Đăng ký & Đăng nhập** tài khoản cá nhân
-  **Lưu trữ riêng tư** dữ liệu theo từng user trên Firebase
-  **Đăng xuất** và bảo mật thông tin

### 💳 Quản Lý Chi Tiêu
-  **Thêm/Xóa/Sửa** khoản chi tiêu
-  **Phân loại theo danh mục** (Ăn uống, Mua sắm, Giải trí, ...)
-  **Lọc dữ liệu** theo Ngày/Tuần/Tháng/Danh mục

### 📊 Thống Kê & Báo Cáo
-  **Biểu đồ cột (Bar Chart)** - So sánh chi tiêu theo thời gian
-  **Biểu đồ tròn (Pie Chart)** - Phân bổ chi tiêu theo danh mục
-  **Thống kê realtime** - Cập nhật tức thì

### 👑 Chức Năng Admin
-  **Xem danh sách người dùng**
-  **Theo dõi tổng chi tiêu** từng user
-  **Phân quyền Admin/User** linh hoạt

## 🛠 Công Nghệ Sử Dụng

### **Ngôn ngữ & Framework**
- `Python 3.8+` - Ngôn ngữ lập trình chính
- `Tkinter` - Giao diện người dùng đồ họa
- `Firebase Realtime Database` - Cơ sở dữ liệu thời gian thực

### **Thư Viện Python**
```python
firebase_admin    # Kết nối Firebase
pyrebase4         # Firebase authentication
matplotlib        # Vẽ biểu đồ thống kê
tkcalendar        # Lịch chọn ngày
Pillow            # Xử lý hình ảnh UI
datetime          # Xử lý ngày tháng

