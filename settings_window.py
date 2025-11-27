import tkinter as tk
from tkinter import ttk, messagebox
import backend

class SettingsWindow:
    def __init__(self, content_frame, current_uid, user_data):
        self.content_frame = content_frame
        self.current_uid = current_uid
        self.user_data = user_data or {}
        self.show_settings()
    
    def show_settings(self):
        """Màn hình Cài Đặt & Tài Khoản - Lấy data từ Firestore"""
        frame = ttk.Frame(self.content_frame, padding="30 30 30 30")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="THÔNG TIN TÀI KHOẢN", 
                 font=('Arial', 16, 'bold'), foreground='#6f42c1').pack(pady=(10, 20))

        # Kiểm tra nếu có user data
        if not self.user_data:
            ttk.Label(frame, text="Không thể tải thông tin người dùng", 
                     foreground='red').pack(pady=20)
            return

        # Khung chính
        main_frame = ttk.Frame(frame)
        main_frame.pack(fill='x', padx=50, pady=10)
        
        # Avatar frame - ICON MẶC ĐỊNH
        avatar_frame = ttk.Frame(main_frame)
        avatar_frame.grid(row=0, column=0, padx=20, pady=10, sticky='n')
        
        avatar_label = ttk.Label(avatar_frame, text="👤", font=('Arial', 40), background='#f0f0f0')
        avatar_label.pack(pady=10)
        ttk.Label(avatar_frame, text="Người dùng", font=('Arial', 9), foreground='#666').pack()
        
        # Info frame - LẤY DATA THỰC TỪ FIRESTORE
        info_frame = ttk.LabelFrame(main_frame, text="THÔNG TIN CÁ NHÂN", padding=20)
        info_frame.grid(row=0, column=1, padx=20, pady=10, sticky='nsew')
        
        # Lấy giá trị thực từ Firestore, nếu không có thì để trống
        self.edit_vars = {
            'fullname': tk.StringVar(value=self.user_data.get('fullname', '')),
            'birthdate': tk.StringVar(value=self.user_data.get('birthdate', '')),
            'hometown': tk.StringVar(value=self.user_data.get('hometown', '')),
            'job': tk.StringVar(value=self.user_data.get('job', ''))
        }
        
        fields = [
            ("👤 Họ tên:", "fullname"),
            ("🎂 Ngày sinh:", "birthdate"), 
            ("🏠 Quê quán:", "hometown"),
            ("💼 Nghề nghiệp:", "job"),
            ("📧 Email:", "email")
        ]
        
        for i, (label, field) in enumerate(fields):
            ttk.Label(info_frame, text=label, font=('Arial', 10, 'bold')).grid(
                row=i, column=0, sticky='w', padx=10, pady=8)
            
            if field == 'email':
                email_text = self.user_data.get('email', '')
                ttk.Label(info_frame, text=email_text, font=('Arial', 10)).grid(
                    row=i, column=1, sticky='w', padx=10, pady=8)
            else:
                entry = ttk.Entry(info_frame, textvariable=self.edit_vars[field], 
                                width=30, font=('Arial', 10))
                entry.grid(row=i, column=1, sticky='w', padx=10, pady=8)

        # Update button
        button_frame = ttk.Frame(info_frame)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=15, sticky='e')
        
        ttk.Button(button_frame, text="💾 Cập Nhật", 
                  command=self.update_user_info).pack(side='right', padx=5)
        
        main_frame.columnconfigure(1, weight=1)

        # Logout section
        logout_frame = ttk.Frame(frame)
        logout_frame.pack(fill='x', padx=50, pady=20)
        
        ttk.Button(logout_frame, text="🚪 Đăng Xuất", 
                  command=self.logout, style='TButton').pack()

    def update_user_info(self):
        """Cập nhật thông tin người dùng LÊN FIRESTORE"""
        try:
            updated_data = {
                'fullname': self.edit_vars['fullname'].get().strip(),
                'birthdate': self.edit_vars['birthdate'].get().strip(),
                'hometown': self.edit_vars['hometown'].get().strip(),
                'job': self.edit_vars['job'].get().strip()
            }
            
            # Kiểm tra dữ liệu trống
            if not all(updated_data.values()):
                messagebox.showwarning("Cảnh báo", "Vui lòng điền đầy đủ thông tin!")
                return
            
            # Gọi backend cập nhật LÊN FIRESTORE
            success = backend.update_user_profile(self.current_uid, updated_data)
            
            if success:
                messagebox.showinfo("Thành công", "Đã cập nhật thông tin lên Firestore!")
                # Cập nhật lại user_data local
                self.user_data.update(updated_data)
            else:
                messagebox.showerror("Lỗi", "Không thể cập nhật thông tin!")
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi cập nhật: {e}")

    def logout(self):
        """Đăng xuất"""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn đăng xuất?"):
            self.content_frame.master.destroy()
            import subprocess
            subprocess.Popen(["python", "2.py"])