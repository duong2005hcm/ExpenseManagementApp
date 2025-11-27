import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from ttkthemes import ThemedTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker as mtick
from tkcalendar import Calendar
from datetime import datetime,date,timedelta
from backend import Backend, signup_user, login_user, get_user_data, update_user_profile, add_plan, get_plans, delete_plan
from settings_window import SettingsWindow
import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px
from PIL import Image, ImageTk
import io
from dateutil import parser
import numpy as np


# Khai báo global backend
backend = Backend()

# --- Cấu hình giao diện và giao diện người dùng (UI Configuration) ---
class ExpenseApp:
    """
    Lớp chính đại diện cho ứng dụng quản lý chi tiêu sử dụng Tkinter.
    Đã được cấu trúc để chứa các chức năng: Quản lý, Kế hoạch, Báo cáo & Thống kê.
    """
    def __init__(self, master, current_uid=None, role="user"):
        self.master = master
        self.current_uid = current_uid
        self.roles = role or "user"
        master.title("Ứng Dụng Quản Lý Chi Tiêu (Tkinter/Firebase)")
        
        # Đặt kích thước và vị trí trung tâm cửa sổ
        window_width = 1400  # Tăng chiều rộng để chứa nhiều nội dung hơn
        window_height = 800
        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        master.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        try:
            self.bg_image = Image.open("assets/background.avif")  # Đặt ảnh vào thư mục assets/
            self.bg_image = self.bg_image.resize((window_width, window_height))
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)

            self.bg_label = tk.Label(master, image=self.bg_photo)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"⚠️ Không tìm thấy hình nền: {e}")
        
        # Cấu hình phong cách chung
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TButton', font=('Arial', 10), padding=10)
        self.style.configure('Header.TLabel', font=('Arial', 18, 'bold'), foreground='#333333', background='#f0f0f0')
        self.style.map('TButton', 
                       background=[('active', '#e0e0e0'), ('!disabled', '#ffffff')],
                       foreground=[('active', '#007bff'), ('!disabled', '#333333')])

        # --- 1. Khung Điều Hướng (Menu/Sidebar) ---
        self.nav_frame = ttk.Frame(master, width=200, relief='solid', padding=15, style='TFrame')
        self.nav_frame.pack(side="left", fill="y")
        
        ttk.Label(self.nav_frame, text="TRANG CHỦ", font=('Arial', 14, 'bold'), 
                  background='#f0f0f0', foreground='#007bff').pack(pady=(10, 25))

        # --- 2. Khung Nội Dung Chính ---
        self.content_frame = ttk.Frame(master, style='TFrame')
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Danh sách các chức năng theo yêu cầu
        self.pages = {
            "dashboard": {"text": "🏠 Bảng Điều Khiển", "func": self.show_dashboard},
            "manage_expenses": {"text": "📝 Quản Lý Chi Tiêu", "func": self.show_manage_expenses},
            "planning": {"text": "🗓️ Lập Kế Hoạch Chi", "func": self.show_planning},
            "stats_reports": {"text": "📊 Báo Cáo & Thống Kê", "func": self.show_stats_reports},
            "settings": {"text": "⚙️ Cài Đặt & Tài Khoản", "func": self.show_settings},
        }
        
        if self.roles == "admin":
            self.pages["admin_panel"] = {
                "text": "🛠️ Quản Trị Viên", 
                "func": self.show_admin_panel
            }

        # Tạo các nút chức năng (Menu)
        self._create_nav_buttons()
        
        self.calendar_window = None
        self.calendar_visible = False
        self.category_picker_window = None
        self.users_tree = None
        self.selected_user_id = None
        self.admin_role_var = None
        self.editing_original_type = None

        # Quản lý loại giao dịch và danh mục
        self.transaction_type = tk.StringVar(value='Chi')
        self.transaction_categories = {
            "Thu": ["Lương", "Thưởng", "Đầu tư", "Kinh doanh", "Cho thuê", "Khác"],
            "Chi": [
                "Ăn uống", "Giải trí", "Giao thông vận tải", "Sở thích",
                "Sinh hoạt", "Áo quần", "Làm đẹp", "Sức khỏe",
                "Giáo dục", "Sự kiện", "Mua sắm", "Khác"
            ],
            "Chuyển khoản": [
                "Chuyển vào tiết kiệm", "Chuyển cho bạn bè",
                "Trả nợ", "Nhận từ người khác", "Chuyển giữa ví", "Khác"
            ]
        }
        self.transaction_buttons = {}
        
        # Hiển thị màn hình mặc định
        self.show_page("dashboard")
        
        self.style.configure('TFrame', background='#f8f9fa')
        self.style.configure('TButton', font=('Arial', 11), padding=12, background='#007bff', foreground='white')
        self.style.configure('Header.TLabel', font=('Arial', 20, 'bold'), foreground='#2c3e50', background='#f8f9fa')
        self.style.configure('Card.TFrame', background='white', relief='raised', borderwidth=2)
        self.style.configure('Accent.TButton', background='#28a745', foreground='white')
        
        # Modern color scheme
        self.colors = {
            'primary': '#007bff',
            'success': '#28a745', 
            'danger': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8',
            'dark': '#343a40',
            'light': '#f8f9fa'
        }
        self.style.configure('Hover.TButton', background="#3ff217")
        
    def create_hover_effect(widget, color='#e9ecef'):
        """Tạo hiệu ứng hover cho widget"""
        def on_enter(e):
            widget.configure(background=color)
        
        def on_leave(e):
            widget.configure(background='ffffff')
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def _create_nav_buttons(self):
        """Tạo các nút navigation hiện đại"""
        # Header navigation
        nav_header = ttk.Frame(self.nav_frame, style='Card.TFrame', padding=15)
        nav_header.pack(fill='x', pady=(0, 20))
        
        ttk.Label(nav_header, text="🎯 ỨNG DỤNG", font=('Arial', 16, 'bold'), 
                foreground='#007bff', background='white').pack()
        ttk.Label(nav_header, text="Quản Lý Chi Tiêu", font=('Arial', 11), 
                foreground='#6c757d', background='white').pack()
        
        # Navigation buttons với hover effect
        for name, info in self.pages.items():
            btn_frame = ttk.Frame(self.nav_frame, style='TFrame')
            btn_frame.pack(fill='x', pady=2)
            
            button = ttk.Button(
                btn_frame, 
                text=info["text"], 
                command=lambda n=name: self.show_page(n),
                style='TButton'
            )
            button.pack(fill='x', padx=5, pady=3)

    def clear_content_frame(self):
        """Xóa tất cả widget hiện tại trong khung nội dung."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_page(self, page_name):
        """Chuyển đổi màn hình nội dung chính."""
        # Xóa nội dung cũ
        self.clear_content_frame()
        
        if page_name == "admin_panel" and self.roles != "admin":
            messagebox.showerror("Lỗi", "Bạn không có quyền truy cập trang này!")
            return
        
        if page_name in self.pages:
            self.pages[page_name]["func"]()
            self.master.title(f"Ứng Dụng Quản Lý Chi Tiêu - {self.pages[page_name]['text']}")
        else:
            ttk.Label(self.content_frame, text="Lỗi: Không tìm thấy trang.", 
                      font=('Arial', 16), foreground='red').pack(pady=50)

    def show_dashboard(self):
        """Màn hình Bảng Điều Khiển: Tổng quan chi tiêu, số dư, và tóm tắt giao dịch."""
        frame = ttk.Frame(self.content_frame, padding="30 30 30 30")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="TRANG CHỦ", style='Header.TLabel').pack(pady=(10, 30))

        try:
            expenses = backend.get_expenses(self.current_uid)

            if not expenses:
                ttk.Label(frame, text="Chưa có dữ liệu chi tiêu",
                          font=('Arial', 14), foreground='gray').pack(pady=50)
                return

            # Chuẩn hóa lại dữ liệu thô để phục vụ cho phép lọc nhiều mốc thời gian
            parsed_expenses = []
            for expense_id, expense_data in expenses.items():
                date_str = expense_data.get('date', '')
                if not date_str:
                    continue

                try:
                    expense_date = parser.parse(date_str).date()
                except Exception as e:
                    print(f"⚠️ Không thể xử lý định dạng ngày: {date_str} - Lỗi: {e}")
                    continue

                parsed_expenses.append({
                    "date": expense_date,
                    "amount": expense_data.get('amount', 0) or 0
                })

            if not parsed_expenses:
                ttk.Label(frame, text="Không thể xử lý dữ liệu chi tiêu để hiển thị",
                          font=('Arial', 12), foreground='gray').pack(pady=30)
                return

            # Giữ lại lựa chọn lọc trước đó để trải nghiệm thống nhất giữa các lần mở trang
            previous_choice = getattr(self, 'dashboard_filter_value', "Tuần")
            self.dashboard_filter_var = tk.StringVar(value=previous_choice)
            self.dashboard_filter_value = previous_choice
            self.dashboard_expense_cache = parsed_expenses

            # --- Bộ lọc thời gian Tuần/Tháng/Năm cho bảng điều khiển ---
            filter_frame = ttk.LabelFrame(frame, text="Bộ lọc thời gian", padding=15)
            filter_frame.pack(fill='x', pady=(0, 15))

            ttk.Label(filter_frame, text="Chọn phạm vi thời gian:",
                      font=('Arial', 11, 'bold')).pack(side='left')

            combo = ttk.Combobox(
                filter_frame,
                textvariable=self.dashboard_filter_var,
                values=("Tuần", "Tháng", "Năm"),
                state="readonly",
                width=18
            )
            combo.pack(side='left', padx=15)
            combo.bind("<<ComboboxSelected>>", lambda _event: self._render_dashboard_overview())

            ttk.Label(
                filter_frame,
                text="Lọc nhanh bảng điều khiển theo tuần, tháng hoặc năm.",
                font=('Arial', 10),
                foreground='#6c757d'
            ).pack(side='left', padx=10)

            self.dashboard_summary_container = ttk.Frame(frame)
            self.dashboard_summary_container.pack(fill='x', pady=10)

            self.dashboard_chart_container = ttk.Frame(frame)
            self.dashboard_chart_container.pack(fill='both', expand=True, pady=5)

            self.dashboard_info_frame = ttk.Frame(frame)
            self.dashboard_info_frame.pack(fill='x', pady=5)

            # Vẽ các thẻ thống kê + biểu đồ lần đầu tiên
            self._render_dashboard_overview()
        except Exception as e:
            ttk.Label(
                frame,
                text=f"Lỗi tải dữ liệu: {e}",
                font=('Arial', 12),
                foreground='red'
            ).pack(pady=30)


    def _render_dashboard_overview(self):
        """Cập nhật thống kê bảng điều khiển theo bộ lọc thời gian."""
        if not hasattr(self, 'dashboard_expense_cache'):
            return

        timeframe_var = getattr(self, 'dashboard_filter_var', None)
        if timeframe_var is None:
            return

        display_value = timeframe_var.get() or "Tháng"
        self.dashboard_filter_value = display_value
        timeframe_map = {
            "Tuần": "week",
            "Tuần (7 ngày)": "week",
            "Tháng": "month",
            "Năm": "year"
        }
        # Chuyển tên hiển thị thành khóa logic để xử lý phía dưới
        timeframe_key = timeframe_map.get(display_value, "month")

        stats = self._calculate_dashboard_stats(self.dashboard_expense_cache, timeframe_key)

        summary_holder = getattr(self, 'dashboard_summary_container', None)
        chart_holder = getattr(self, 'dashboard_chart_container', None)
        info_holder = getattr(self, 'dashboard_info_frame', None)

        # Xóa nội dung cũ mỗi khi người dùng đổi bộ lọc
        for holder in (summary_holder, chart_holder, info_holder):
            if holder:
                for widget in holder.winfo_children():
                    widget.destroy()

        if summary_holder is None or chart_holder is None:
            return

        # Các thẻ thống kê chính trên cùng
        stats_cards = [
            (f"Tổng chi ({stats['period_desc']}):", f"{stats['total']:,.0f} VNĐ", '#dc3545'),
            (f"Chi TB/{stats['avg_unit']}:", f"{stats['avg']:,.0f} VNĐ", '#ffc107'),
            ("Phạm vi theo dõi:", stats['range_text'], '#007bff'),
            ("Tổng giao dịch:", f"{stats['transaction_count']} giao dịch", '#28a745'),
        ]

        for i, (label, value, color) in enumerate(stats_cards):
            card = ttk.Frame(summary_holder, relief='raised', padding=15)
            card.grid(row=0, column=i, padx=15, sticky='ew')
            ttk.Label(card, text=label, font=('Arial', 12), foreground=color).pack()
            ttk.Label(card, text=value, font=('Arial', 16, 'bold'), foreground=color).pack()

        # Khu vực biểu đồ chính (ẩn nếu không có dữ liệu)
        if sum(stats['chart_values']) > 0:
            chart_frame = ttk.LabelFrame(chart_holder, text=stats['chart_title'], padding=15)
            chart_frame.pack(fill='both', expand=True)

            labels = stats['labels']
            values = stats['chart_values']

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(
                labels,
                values,
                marker='o',
                markersize=10,
                markerfacecolor='#FF6B6B',
                markeredgecolor='white',
                markeredgewidth=2,
                color='#3366CC',
                linewidth=3,
                alpha=0.85,
                zorder=2
            )
            ax.fill_between(labels, values, alpha=0.2, color='#3366CC', zorder=1)
            ax.set_title(stats['chart_title'], fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('Mốc thời gian', fontsize=12, fontweight='bold', labelpad=10)
            ax.set_ylabel('Số Tiền (VNĐ)', fontsize=12, fontweight='bold', labelpad=10)
            ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _p: f"{x:,.0f}"))
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.set_axisbelow(True)
            ax.set_facecolor('#f8f9fa')
            fig.patch.set_facecolor('white')

            peak_value = max(values)
            peak_index = values.index(peak_value)
            ax.annotate(
                f"Cao nhất: {peak_value:,.0f} VNĐ",
                xy=(labels[peak_index], peak_value),
                xytext=(15, 15),
                textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#fff9c4',
                          edgecolor='#ffd54f', alpha=0.9),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.2',
                                color='#ff6b6b', lw=1.5),
                fontsize=10,
                fontweight='bold'
            )

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            image = Image.open(buf)
            chart_image = ImageTk.PhotoImage(image)
            plt.close()

            chart_label = tk.Label(chart_frame, image=chart_image, bg='white')
            chart_label.image = chart_image
            chart_label.pack(fill='both', expand=True, padx=10, pady=5)

            ttk.Label(
                chart_frame,
                text=f"Khoảng thời gian: {stats['range_text']}",
                font=('Arial', 10),
                foreground='#6c757d',
                background='white'
            ).pack(pady=(5, 0))
        else:
            ttk.Label(
                chart_holder,
                text="Chưa có dữ liệu trong phạm vi được chọn.",
                font=('Arial', 12),
                foreground='gray'
            ).pack(pady=30)

        if info_holder:
            # Hiển thị thêm thông tin phụ để người dùng dễ theo dõi khi thay đổi bộ lọc
            ttk.Label(
                info_holder,
                text=f"Cập nhật: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                font=('Arial', 10),
                foreground='#666'
            ).pack(side='left')
            ttk.Label(
                info_holder,
                text=f"Dữ liệu hợp lệ: {stats['transaction_count']} giao dịch",
                font=('Arial', 10),
                foreground='#666'
            ).pack(side='right')


    def _calculate_dashboard_stats(self, expenses, timeframe):
        """Chuẩn hóa dữ liệu thống kê cho từng phạm vi thời gian."""
        today = datetime.now().date()

        # Xây dựng phạm vi ngày/tháng tương ứng để gom dữ liệu
        if timeframe == "week":
            start_date = today - timedelta(days=6)
            end_date = today
            labels = []
            label_map = {}
            current = start_date
            while current <= end_date:
                key = current.strftime('%d/%m')
                labels.append(key)
                label_map[key] = 0
                current += timedelta(days=1)
            avg_unit = "ngày"
            period_desc = "7 ngày gần nhất"
        elif timeframe == "year":
            start_date = date(today.year, 1, 1)
            end_date = today
            labels = []
            label_map = {}
            for month in range(1, today.month + 1):
                key = f"Thg {month:02d}"
                labels.append(key)
                label_map[key] = 0
            avg_unit = "tháng"
            period_desc = f"Năm {today.year}"
        else:
            start_date = today.replace(day=1)
            end_date = today
            labels = []
            label_map = {}
            current = start_date
            while current <= end_date:
                key = current.strftime('%d/%m')
                labels.append(key)
                label_map[key] = 0
                current += timedelta(days=1)
            avg_unit = "ngày"
            period_desc = f"Tháng {today.strftime('%m/%Y')}"

        filtered = []
        for expense in expenses:
            expense_date = expense['date']
            if start_date <= expense_date <= end_date:
                filtered.append(expense)
                if timeframe == "year":
                    label_key = f"Thg {expense_date.month:02d}"
                else:
                    label_key = expense_date.strftime('%d/%m')
                if label_key in label_map:
                    label_map[label_key] += expense.get('amount', 0) or 0

        total = sum(label_map.values())
        avg = total / max(1, len(labels))

        chart_titles = {
            "week": "BIỂU ĐỒ CHI TIÊU 7 NGÀY GẦN NHẤT",
            "month": "BIỂU ĐỒ CHI THEO NGÀY (THÁNG HIỆN TẠI)",
            "year": "BIỂU ĐỒ CHI THEO THÁNG (NĂM HIỆN TẠI)"
        }

        return {
            "total": total,
            "avg": avg,
            "avg_unit": avg_unit,
            "period_desc": period_desc,
            "range_text": f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
            "transaction_count": len(filtered),
            "labels": labels,
            "chart_values": [label_map[label] for label in labels],
            "chart_title": chart_titles[timeframe]
        }


    def show_manage_expenses(self):
        """Màn hình Quản Lý Chi Tiêu: Thêm, Sửa, Xóa và Hiển thị danh sách từ Firestore"""
        frame = ttk.Frame(self.content_frame, padding="30 30 30 30")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="QUẢN LÝ GIAO DỊCH (THU/CHI/CHUYỂN KHOẢN)", style='Header.TLabel').pack(pady=(10, 30))
        
        # Khung cho Form Thêm/Sửa
        form_frame = ttk.LabelFrame(frame, text="THÊM MỚI / CHỈNH SỬA GIAO DỊCH", padding=15)
        form_frame.pack(pady=10, padx=50, fill='x')
        
        # Biến lưu trữ dữ liệu form
        self.date_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.amount_var = tk.StringVar()
        self.note_var = tk.StringVar()
        self.editing_id = None
        self.editing_original_type = None
        self.date_var.set(datetime.now().strftime('%Y-%m-%d'))

        # Bộ chọn loại giao dịch (Thu/Chi/Chuyển khoản)
        type_frame = ttk.Frame(form_frame)
        type_frame.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky='w')
        ttk.Label(type_frame, text="Loại giao dịch:", font=('Arial', 11, 'bold')).pack(side='left', padx=(0, 15))

        for option in ["Thu", "Chi", "Chuyển khoản"]:
            btn = tk.Button(
                type_frame,
                text=option,
                width=12,
                font=('Arial', 11),
                relief=tk.RAISED,
                bg='#e9ecef',
                fg='#333333',
                command=lambda opt=option: self.set_transaction_type(opt)
            )
            btn.pack(side='left', padx=5)
            self.transaction_buttons[option] = btn
        self.update_transaction_buttons()

        # Các trường nhập liệu
        fields = [
            ("Ngày: ", self.date_var),
            ("Danh Mục:", self.category_var),
            ("Số Tiền (VNĐ):", self.amount_var),
            ("Ghi Chú/Mô Tả:", self.note_var)
        ]
        start_row = 1
        for i, (field_name, var) in enumerate(fields):
            row_index = start_row + i
            ttk.Label(form_frame, text=field_name).grid(row=row_index, column=0, padx=10, pady=5, sticky='w')
            if field_name == "Ngày: ":
                date_frame = ttk.Frame(form_frame)
                date_frame.grid(row=row_index, column=1, padx=10, pady=5, sticky='ew')
                
                ttk.Entry(date_frame, textvariable=var, width=40).pack(side='left', fill='x', expand=True)
                
                ttk.Button(
                    date_frame,
                    text="📅",
                    command=self.toggle_calendar,
                    width=3
                ).pack(side='right', padx=(5, 0))
            
            elif field_name == "Danh Mục:":
                category_frame = ttk.Frame(form_frame)
                category_frame.grid(row=row_index, column=1, padx=10, pady=5, sticky='ew')
                category_frame.columnconfigure(0, weight=1)
                
                ttk.Entry(category_frame, textvariable=var, state='readonly').grid(row=0, column=0, sticky='ew')
                ttk.Button(category_frame, text="Chọn", command=self.open_category_picker).grid(row=0, column=1, padx=(8, 0))
            else:
                ttk.Entry(form_frame, textvariable=var, width=50).grid(row=row_index, column=1, padx=10, pady=5, sticky='ew')

        # Nút hành động
        action_buttons = ttk.Frame(form_frame)
        action_buttons.grid(row=start_row + len(fields), column=1, padx=10, pady=15, sticky='e')
        
        ttk.Button(action_buttons, text="💾 Lưu Giao Dịch", 
                   command=self.save_expense).pack(side='left', padx=5)
        
        ttk.Button(action_buttons, text="✏️ Sửa", 
                   command=self.edit_selected_expense).pack(side='left', padx=5)
        
        ttk.Button(action_buttons, text="🗑️ Xóa Giao Dịch", 
                   command=self.delete_selected_expense).pack(side='left', padx=5)
        
        ttk.Button(action_buttons, text="🔄 Làm Mới", 
                   command=self.refresh_expenses_list).pack(side='left', padx=5)
        
        # Bảng hiển thị giao dịch
        ttk.Label(frame, text="LỊCH SỬ GIAO DỊCH", 
                  font=('Arial', 12, 'bold')).pack(pady=(20, 10), anchor='w')
        
        # Bảng Treeview
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill='both', expand=True, padx=50)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        columns = ('date', 'category', 'amount', 'note')
        self.expenses_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', 
                                        yscrollcommand=scrollbar.set, height=12)
        scrollbar.config(command=self.expenses_tree.yview)
        
        self.expenses_tree.heading('date', text='Ngày')
        self.expenses_tree.heading('category', text='Danh Mục')
        self.expenses_tree.heading('amount', text='Số Tiền (VNĐ)')
        self.expenses_tree.heading('note', text='Ghi Chú')
        
        self.expenses_tree.column('date', width=120, anchor=tk.CENTER)
        self.expenses_tree.column('category', width=120, anchor=tk.CENTER)
        self.expenses_tree.column('amount', width=150, anchor=tk.E)
        self.expenses_tree.column('note', width=300, anchor=tk.W)
        
        self.expenses_tree.pack(fill='both', expand=True)
        
        # Tải dữ liệu khi mở màn hình
        self.refresh_expenses_list()

    def save_expense(self):
        """Lưu giao dịch lên Firestore collection Expenses"""
        try:
            date = self.date_var.get().strip()
            category = self.category_var.get().strip()
            amount_str = self.amount_var.get().strip()
            note = self.note_var.get().strip()
            transaction_type = self.transaction_type.get()
            
            if not all([date, category, amount_str]):
                messagebox.showwarning("Cảnh báo", "Vui lòng điền đầy đủ Ngày, Danh mục và Số tiền!")
                return
            
            try:
                amount = int(amount_str)
                if amount <= 0:
                    messagebox.showwarning("Cảnh báo", "Số tiền phải lớn hơn 0!")
                    return
            except ValueError:
                messagebox.showerror("Lỗi", "Số tiền không hợp lệ!")
                return
            
            # Đảm bảo có current_uid
            if not hasattr(self, 'current_uid'):
                messagebox.showerror("Lỗi", "Chưa đăng nhập!")
                return
            
            # Lưu lên Firestore
            if self.editing_id:
                # Chế độ sửa
                success = backend.update_expense(
                    self.current_uid,
                    self.editing_id,
                    date,
                    category,
                    amount,
                    note,
                    transaction_type,
                    getattr(self, "editing_original_type", transaction_type)
                )
                action = "cập nhật"
            else:
                # Chế độ thêm mới
                success = backend.add_expense(
                    self.current_uid,
                    date,
                    category,
                    amount,
                    note,
                    transaction_type
                )
                action = "thêm"
            
            if success:
                messagebox.showinfo("Thành công", f"Đã {action} giao dịch {transaction_type}!")
                self.clear_form()
                self.refresh_expenses_list()
            else:
                messagebox.showerror("Lỗi", f"Không thể {action} giao dịch!")
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xử lý: {e}")

    def edit_selected_expense(self):
        """Chỉnh sửa giao dịch đã chọn"""
        selected_item = self.expenses_tree.selection()
        if not selected_item:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn giao dịch để sửa!")
            return
        
        item = self.expenses_tree.item(selected_item[0])
        expense_id = item['tags'][0]
        data_type = item['tags'][1] if len(item['tags']) > 1 else self.transaction_type.get()
        values = item['values']
        
        self.date_var.set(values[0])
        self.category_var.set(values[1])
        self.amount_var.set(values[2].replace(' VNĐ', '').replace(',', ''))
        self.note_var.set(values[3])
        self.transaction_type.set(data_type)
        self.update_transaction_buttons()
        self.editing_id = expense_id
        self.editing_original_type = data_type
        
        messagebox.showinfo("Thông báo", "Đã tải dữ liệu vào form. Sửa và nhấn Lưu.")

    def delete_selected_expense(self):
        """Xóa giao dịch đã chọn"""
        selected_item = self.expenses_tree.selection()
        if not selected_item:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn giao dịch để xóa!")
            return
        
        item = self.expenses_tree.item(selected_item[0])
        expense_id = item['tags'][0]
        data_type = item['tags'][1] if len(item['tags']) > 1 else self.transaction_type.get()
        date = item['values'][0]
        amount = item['values'][2]
        
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa giao dịch ngày {date} - {amount}?"):
            success = backend.delete_expense(self.current_uid, expense_id, data_type)
            if success:
                messagebox.showinfo("Thành công", "Đã xóa giao dịch!")
                self.refresh_expenses_list()
            else:
                messagebox.showerror("Lỗi", "Không thể xóa giao dịch!")

    def refresh_expenses_list(self):
        """Làm mới danh sách giao dịch từ Firestore"""
        try:
            # Xóa dữ liệu cũ
            for item in self.expenses_tree.get_children():
                self.expenses_tree.delete(item)
            
            # Kiểm tra current_uid
            if not hasattr(self, 'current_uid'):
                return
            
            current_type = self.transaction_type.get()
            expenses = backend.get_expenses(self.current_uid, current_type)
            shown = 0
            for expense_id, expense_data in expenses.items():
                data_type = expense_data.get('transaction_type', current_type)
                
                self.expenses_tree.insert('', tk.END, values=(
                    expense_data.get('date', ''),
                    expense_data.get('category', ''),
                    f"{expense_data.get('amount', 0):,} VNĐ",
                    expense_data.get('note', '')
                ), tags=(expense_id, data_type))
                shown += 1
                
            print(f"✅ Đã tải {shown} giao dịch loại {current_type}")
            
        except Exception as e:
            print(f"❌ Lỗi làm mới danh sách: {e}")

    def clear_form(self):
        """Xóa form nhập liệu"""
        
        self.date_var.set(datetime.now().strftime('%Y-%m-%d'))
        self.category_var.set('')
        self.amount_var.set('')
        self.note_var.set('')
        self.editing_id = None
        self.editing_original_type = None
        self.close_category_picker()

    def on_transaction_type_change(self):
        """Thay đổi tab giao dịch và làm mới danh sách."""
        self.update_transaction_buttons()
        self.category_var.set('')
        self.close_category_picker()
        if hasattr(self, 'expenses_tree'):
            self.refresh_expenses_list()

    def set_transaction_type(self, option):
        """Cập nhật loại giao dịch khi nhấn các nút phân trang."""
        if self.transaction_type.get() == option:
            return
        self.transaction_type.set(option)
        self.on_transaction_type_change()

    def update_transaction_buttons(self):
        """Đổi màu nút theo tab đang chọn."""
        active = self.transaction_type.get()
        for option, button in self.transaction_buttons.items():
            if option == active:
                button.config(bg='#007bff', fg='white', relief=tk.SUNKEN)
            else:
                button.config(bg='#e9ecef', fg='#333333', relief=tk.RAISED)

    def open_category_picker(self):
        """Mở cửa sổ chọn danh mục theo loại giao dịch."""
        categories = self.transaction_categories.get(self.transaction_type.get(), [])
        if not categories:
            messagebox.showwarning("Thông báo", "Chưa có danh mục cho loại giao dịch này.")
            return

        if self.category_picker_window and self.category_picker_window.winfo_exists():
            self.category_picker_window.lift()
            return

        self.category_picker_window = tk.Toplevel(self.master)
        self.category_picker_window.title("Chọn danh mục")
        self.category_picker_window.resizable(False, False)
        self.category_picker_window.transient(self.master)
        self.category_picker_window.grab_set()
        self.category_picker_window.protocol("WM_DELETE_WINDOW", self.close_category_picker)

        ttk.Label(
            self.category_picker_window,
            text=f"Danh mục cho {self.transaction_type.get()}",
            font=('Arial', 12, 'bold')
        ).pack(pady=(5, 10))

        grid_frame = ttk.Frame(self.category_picker_window, padding=5)
        grid_frame.pack(fill='both', expand=True)
        columns = 3
        for col in range(columns):
            grid_frame.columnconfigure(col, weight=1)

        for index, category in enumerate(categories):
            row = index // columns
            col = index % columns

            ttk.Button(
                grid_frame,
                text=category,
                width=20,
                command=lambda c=category: self._select_category(c)
            ).grid(row=row, column=col, padx=5, pady=5, sticky='ew')

    def _select_category(self, category_name):
        self.category_var.set(category_name)
        self.close_category_picker()

    def close_category_picker(self):
        """Đóng popup chọn danh mục nếu đang mở."""
        if self.category_picker_window and self.category_picker_window.winfo_exists():
            try:
                self.category_picker_window.grab_release()
            except tk.TclError:
                pass
            self.category_picker_window.destroy()
        self.category_picker_window = None

    def toggle_calendar(self):
        """Mở / đóng cửa sổ lịch popup để chọn ngày."""
        if self.calendar_visible:
            self.hide_calendar()
            return

        self.calendar_window = tk.Toplevel(self.master)
        self.calendar_window.title("Chọn ngày")
        self.calendar_window.resizable(False, False)
        self.calendar_window.transient(self.master)
        self.calendar_window.grab_set()
        self.calendar_window.configure(padx=10, pady=10, bg="#ffffff")
        self.calendar_window.protocol("WM_DELETE_WINDOW", self.hide_calendar)

        # Đặt vị trí lịch gần khu vực form nhập liệu
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        self.calendar_window.geometry(f"+{parent_x + 250}+{parent_y + 150}")

        cal = Calendar(
            self.calendar_window,
            selectmode='day',
            date_pattern='yyyy-mm-dd'
        )
        cal.pack(padx=10, pady=(5, 10))

        def select_date():
            """Gán ngày đã chọn cho trường Ngày."""
            self.date_var.set(cal.get_date())
            self.hide_calendar()

        btn_frame = ttk.Frame(self.calendar_window)
        btn_frame.pack(fill='x')

        ttk.Button(btn_frame, text="Chọn ngày", command=select_date).pack(
            side='left', expand=True, fill='x', padx=(0, 5)
        )
        ttk.Button(btn_frame, text="Đóng", command=self.hide_calendar).pack(
            side='right', expand=True, fill='x', padx=(5, 0)
        )

        self.calendar_visible = True

    def hide_calendar(self):
        """Đóng cửa sổ lịch."""
        if self.calendar_window:
            try:
                self.calendar_window.grab_release()
            except tk.TclError:
                pass
            self.calendar_window.destroy()
            self.calendar_window = None
            self.calendar_visible = False

    def show_planning(self):
        """Màn hình Lập Kế Hoạch Chi Tiêu Dự Kiến - Lưu lên Firestore"""
        frame = ttk.Frame(self.content_frame, padding="30 30 30 30")
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="LẬP KẾ HOẠCH CHI TIÊU DỰ KIẾN",
            style='Header.TLabel',
            foreground='#007bff'
        ).pack(pady=(10, 20))

        ttk.Label(
            frame,
            text="Chọn ngày trong tương lai để lập kế hoạch chi tiêu.",
            font=('Arial', 12)
        ).pack(pady=10)

        # --- Lịch hiển thị ---
        cal = Calendar(frame, selectmode='day', date_pattern='yyyy-mm-dd')
        cal.pack(padx=50, pady=20)

        # --- Danh sách kế hoạch đã tạo ---
        plans_frame = ttk.LabelFrame(frame, text="CÁC KẾ HOẠCH ĐÃ TẠO", padding=10)
        plans_frame.pack(fill='both', expand=True, padx=30, pady=10)

        # Treeview để hiển thị kế hoạch
        columns = ('date', 'desc', 'amount')
        tree = ttk.Treeview(plans_frame, columns=columns, show='headings', height=8)
    
        tree.heading('date', text='Ngày')
        tree.heading('desc', text='Mô tả')
        tree.heading('amount', text='Số tiền (VNĐ)')
    
        tree.column('date', width=120, anchor=tk.CENTER)
        tree.column('desc', width=250, anchor=tk.W)
        tree.column('amount', width=150, anchor=tk.E)
    
        scrollbar = ttk.Scrollbar(plans_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
    
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def refresh_plans():
            """Lấy và hiển thị kế hoạch từ Firestore"""
            # Xóa dữ liệu cũ
            for item in tree.get_children():
                tree.delete(item)
        
            # Lấy kế hoạch từ Firestore
            plans = get_plans(self.current_uid)
        
            # Hiển thị kế hoạch
            for plan_id, plan_data in plans.items():
                tree.insert('', tk.END, values=(
                    plan_data.get('date', ''),
                    plan_data.get('desc', ''),
                    f"{plan_data.get('amount', 0):,} VNĐ"
                ), tags=(plan_id,))

        def on_date_click():
            """Xử lý khi chọn ngày để thêm kế hoạch"""
            selected_date = cal.get_date()
            today = datetime.today().strftime('%Y-%m-%d')

            # Kiểm tra chỉ được chọn ngày tương lai
            if selected_date <= today:
                messagebox.showwarning("Cảnh báo", "Chỉ chọn ngày trong tương lai!")
                return

            # Nhập mô tả
            desc = simpledialog.askstring("Mô tả", f"Kế hoạch cho ngày {selected_date}:")
            if not desc:
                return
        
            # Nhập số tiền
            try:
                amount = simpledialog.askinteger("Số tiền (VNĐ)", "Nhập số tiền dự kiến:")
                if amount is None or amount <= 0:
                    messagebox.showwarning("Cảnh báo", "Số tiền phải lớn hơn 0!")
                    return
            except ValueError:
                messagebox.showerror("Lỗi", "Số tiền không hợp lệ!")
                return

            # Lưu kế hoạch lên Firestore
            success = add_plan(self.current_uid, selected_date, desc, amount)
        
            if success:
                messagebox.showinfo("Thành công", f"Đã lưu kế hoạch cho ngày {selected_date}!")
                refresh_plans()  # Làm mới danh sách
            else:
                messagebox.showerror("Lỗi", "Không thể lưu kế hoạch!")

        def delete_selected_plan():
            """Xóa kế hoạch đã chọn"""
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn kế hoạch để xóa!")
                return
        
            plan_id = tree.item(selected_item[0])['tags'][0]
            plan_date = tree.item(selected_item[0])['values'][0]
        
            if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa kế hoạch ngày {plan_date}?"):
                success = delete_plan(self.current_uid, plan_id)
                if success:
                    messagebox.showinfo("Thành công", "Đã xóa kế hoạch!")
                    refresh_plans()
                else:
                    messagebox.showerror("Lỗi", "Không thể xóa kế hoạch!")

        # Nút thao tác
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="➕ Thêm Kế Hoạch", 
                   command=on_date_click).pack(side=tk.LEFT, padx=5)
    
        ttk.Button(button_frame, text="🗑️ Xóa Kế Hoạch", 
                   command=delete_selected_plan).pack(side=tk.LEFT, padx=5)
    
        ttk.Button(button_frame, text="🔄 Làm Mới", 
                   command=refresh_plans).pack(side=tk.LEFT, padx=5)

        # Tải kế hoạch khi mở màn hình
        refresh_plans()

    def apply_filters_paginated(self, user_id, time_combo, category_combo):
        """Phiên bản sửa đổi của apply_filters để hỗ trợ phân trang"""
        print("📊 [DEBUG] Đang lọc dữ liệu cho user:", user_id)
        selected_month = time_combo.get()
        print("📊 [DEBUG] Thời gian lọc: {selected_month}")
        
        if hasattr(self, 'month_label'):
            self.month_label.config(text=f"KẾT QUẢ LỌC THEO: {selected_month}")
            
        def fetch_expenses(user_id):
            data = backend.get_expenses(user_id)
            expenses = []

            if isinstance(data, dict):
                for key, val in data.items():
                    if "date" in val:
                        if "date" in val:
                            date_str = val["date"]
                            try:
                                # Kiểm tra định dạng, nếu chỉ có năm thì bỏ qua
                                if len(date_str) == 4:
                                    print(f"⚠️ Bỏ qua ngày không hợp lệ (chỉ có năm): {date_str}")
                                    continue
                                
                                # Xử lý nhiều định dạng ngày
                                formatted_date = None
                                
                                #YYYY-MM-DD
                                if '-' in date_str:
                                    try:
                                        #(2025-11-1)
                                        parts = date_str.split('-')
                                        if len(parts) == 3:
                                            year = parts[0]
                                            month = parts[1].zfill(2)  # Thêm 0 nếu cần
                                            day = parts[2].zfill(2)    # Thêm 0 nếu cần
                                            formatted_date_str = f"{year}-{month}-{day}"
                                            formatted_date = datetime.strptime(formatted_date_str, "%Y-%m-%d").date()
                                    except ValueError:
                                        pass
                                
                                #(2025/4/3)
                                elif '/' in date_str:
                                    try:
                                        parts = date_str.split('/')
                                        if len(parts) == 3:
                                            year = parts[0]
                                            month = parts[1].zfill(2)  # Thêm 0 nếu cần
                                            day = parts[2].zfill(2)    # Thêm 0 nếu cần
                                            formatted_date_str = f"{year}-{month}-{day}"
                                            formatted_date = datetime.strptime(formatted_date_str, "%Y-%m-%d").date()
                                    except ValueError:
                                        pass
                                
                                # YYYY.MM.DD 
                                elif '.' in date_str:
                                    try:
                                        parts = date_str.split('.')
                                        if len(parts) == 3:
                                            year = parts[0]
                                            month = parts[1].zfill(2)
                                            day = parts[2].zfill(2)
                                            formatted_date_str = f"{year}-{month}-{day}"
                                            formatted_date = datetime.strptime(formatted_date_str, "%Y-%m-%d").date()
                                    except ValueError:
                                        pass
                                
                                # Nếu không parse được, thử trực tiếp
                                if formatted_date is None:
                                    try:
                                        formatted_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                                    except ValueError:
                                        try:
                                            formatted_date = datetime.strptime(date_str, "%Y/%m/%d").date()
                                        except ValueError:
                                            print(f"⚠️ Không thể chuyển định dạng ngày: {date_str}")
                                            continue
                                
                                val["date"] = formatted_date
                                print(f"✅ Đã chuyển đổi: {date_str} -> {formatted_date}")
                                
                            except Exception as e:
                                print(f"⚠️ Lỗi xử lý ngày {date_str}: {e}")
                                continue
                        else:
                            # Nếu không có trường 'date' thì bỏ qua
                            print("⚠️ Bỏ qua mục không có ngày:", val)
                            continue
                    
                    expenses.append(val)
            return expenses

        def filter_expenses(expenses, month_filter, category_filter):
            filtered = []

            for item in expenses:
                if month_filter:
                    try:
                        expense_month = item["date"].strftime('%Y-%m')
                        match_month = (expense_month == month_filter)
                    except:
                        match_month = False
                else:
                    match_month = True

                # Kiểm tra khớp danh mục
                match_category = (category_filter == "Tất cả" or item["category"] == category_filter)

                if match_month and match_category:
                    filtered.append(item)

            return filtered

        # Fetch & Filter
        expenses = fetch_expenses(user_id)
        print("📊 [DEBUG] Số dòng dữ liệu lấy được:", len(expenses))
        
        filtered = filter_expenses(expenses, time_combo.get(), category_combo.get())
        print("📊 [DEBUG] Số dòng sau khi lọc:", len(filtered))

        # Tổng hợp theo danh mục
        category_totals = {}
        for item in filtered:
            cat = item.get("category", "Khác")
            amount = item.get("amount", 0)
            category_totals[cat] = category_totals.get(cat, 0) + amount

        # Xóa nội dung cũ trong các tab
        for frame in [self.column_frame, self.pie_frame, self.raw_data_frame]:
            for widget in frame.winfo_children():
                widget.destroy()

        #BIỂU ĐỒ CỘT 
        if category_totals:
        # Tạo figure với kích thước lớn
            fig1, ax1 = plt.subplots(figsize=(10, 4.9))
            
            categories = list(category_totals.keys())
            amounts = list(category_totals.values())
            
            # Tạo biểu đồ cột
            bars = ax1.bar(categories, amounts, color='#1f77b4', alpha=0.8)
            
            # Thêm số liệu trên các cột
            for bar, amount in zip(bars, amounts):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + max(amounts)*0.01,
                        f'{amount:,.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            # Định dạng biểu đồ
            ax1.set_title('TỔNG CHI THEO DANH MỤC', fontsize=14, fontweight='bold', pad=15)
            ax1.set_xlabel('Danh mục', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Số tiền (VNĐ)', fontsize=12, fontweight='bold')
            
            ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, p: f'{x:,.0f}'))
            
            plt.xticks(rotation=0, ha='right')
            
            # Thêm lưới
            ax1.grid(True, alpha=0.3, axis='y')
            ax1.set_axisbelow(True)
            
            # Tự động điều chỉnh layout
            plt.tight_layout()
            
            buf1 = io.BytesIO()
            plt.savefig(buf1, format='png', dpi=100, bbox_inches='tight')
            buf1.seek(0)
            image1 = Image.open(buf1)
            photo1 = ImageTk.PhotoImage(image1)
            plt.close(fig1)
            
            # Hiển thị trong Tkinter
            label1 = tk.Label(self.column_frame, image=photo1, bg='white')
            label1.image = photo1
            label1.pack(fill='both', expand=True, padx=5, pady=5)
        else:
            ttk.Label(self.column_frame, text="📭 Không có dữ liệu để hiển thị biểu đồ cột", 
                    font=('Arial', 12), foreground='gray').pack(pady=20)

        #BIỂU ĐỒ TRÒN
        if category_totals:
        # Tạo figure
            fig2, ax2 = plt.subplots(figsize=(8, 5))
            
            categories = list(category_totals.keys())
            amounts = list(category_totals.values())
            
            # Màu sắc cho biểu đồ tròn
            colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
            
            # Tạo biểu đồ tròn
            wedges, texts, autotexts = ax2.pie(amounts, labels=categories, autopct='%1.1f%%',
                                            colors=colors, startangle=90,
                                            textprops={'fontsize': 10})
            
            ax2.legend(wedges, categories, loc="center left", bbox_to_anchor=(1.1, 0, 0.5, 1),fontsize =9)
            
            # Tùy chỉnh phần trăm
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(8)
            
            # Tiêu đề
            ax2.set_title('TỈ LỆ CHI TIÊU THEO DANH MỤC', fontsize=12, fontweight='bold', pad=20)
            
            # Đảm bảo biểu đồ tròn là hình tròn
            ax2.axis('equal')
            
            plt.tight_layout()
            
            # Chuyển đổi thành hình ảnh
            buf2 = io.BytesIO()
            plt.savefig(buf2, format='png', dpi=90, bbox_inches='tight')
            buf2.seek(0)
            image2 = Image.open(buf2)
            photo2 = ImageTk.PhotoImage(image2)
            plt.close(fig2)
            
            # Hiển thị trong Tkinter
            label2 = tk.Label(self.pie_frame, image=photo2, bg='white')
            label2.image = photo2
            label2.pack(fill='both', expand=True, padx=5, pady=5)
        else:
            ttk.Label(self.pie_frame, text="📭 Không có dữ liệu để hiển thị biểu đồ tròn", 
                    font=('Arial', 12), foreground='gray').pack(pady=0)

        # DỮ LIỆU CHI TIẾT
        if filtered:
            columns = ('date', 'category', 'amount', 'note')
            tree = ttk.Treeview(self.raw_data_frame, columns=columns, show='headings', height=15)
            
            tree.heading('date', text='📅 Ngày')
            tree.heading('category', text='🏷️ Danh mục')
            tree.heading('amount', text='💰 Số tiền (VNĐ)')
            tree.heading('note', text='📝 Ghi chú')
            
            tree.column('date', width=120, anchor=tk.CENTER)
            tree.column('category', width=150, anchor=tk.CENTER)
            tree.column('amount', width=150, anchor=tk.E)
            tree.column('note', width=300, anchor=tk.W)

            for item in filtered:
                tree.insert('', tk.END, values=(
                    item.get('date').strftime('%d/%m/%Y'),
                    item.get('category', ''),
                    f"{item.get('amount', 0):,}",
                    item.get('note', '')
                ))

            scrollbar = ttk.Scrollbar(self.raw_data_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=tk.LEFT, fill='both', expand=True, padx=10, pady=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

            # Thông tin phân trang
            info_label = ttk.Label(self.raw_data_frame, 
                    text=f"📄 Hiển thị {len(filtered)} giao dịch | " 
                        f"Lọc: {time_combo.get()} | Danh mục: {category_combo.get()}",
                    font=('Arial', 10))
            info_label.pack(side=tk.BOTTOM, fill='x', padx=10, pady=5)

        else:
            ttk.Label(self.raw_data_frame, text="📭 Không có dữ liệu phù hợp với bộ lọc", 
                    font=('Arial', 12), foreground='gray').pack(pady=50)

    
    def show_stats_reports(self):
        """Màn hình Báo Cáo & Thống Kê: Lọc dữ liệu, biểu đồ."""
        frame = ttk.Frame(self.content_frame, padding="30 30 30 30")
        frame.pack(fill="both", expand=True)
        
        if not hasattr(self, "current_uid"):
            messagebox.showerror("Lỗi", "Bạn chưa đăng nhập!")
            return

        expenses = backend.get_expenses(self.current_uid)
        if not expenses:
            messagebox.showinfo("Thông báo", "Chưa có dữ liệu chi tiêu để hiển thị.")
            return
        
        available_months = self._generate_month_list()
        self.selected_month = tk.StringVar(value=available_months[0] if available_months else datetime.now().strftime('%Y-%m'))
        
        category_totals = {}
        for expense in expenses.values():
            category = expense.get('category', 'Khác')
            amount = expense.get('amount', 0)
            category_totals[category] = category_totals.get(category, 0) + amount

        ttk.Label(frame, text="BÁO CÁO VÀ THỐNG KÊ CHI TIÊU", style='Header.TLabel', foreground='#ffc107').pack(pady=(10, 30))
        
        month_frame = ttk.LabelFrame(frame, text="CHỌN LỌC THEO THÁNG", padding=15)
        month_frame.pack(fill='x', padx=50, pady=10)
        
        selection_frame = ttk.Frame(month_frame)
        selection_frame.pack(fill='x', pady=5)
        
        ttk.Label(selection_frame, text="Chọn tháng:", font=('Arial', 11, 'bold')).pack(side='left', padx=(0, 15))
        
        # Combobox chọn tháng
        months = self._generate_month_list()  # Tạo danh sách tháng
        month_combo = ttk.Combobox(selection_frame, textvariable=self.selected_month, 
                                values=available_months, width=15, font=('Arial', 11))
        month_combo.pack(side='left', padx=(0, 20))
        
        # Nút áp dụng
        ttk.Button(selection_frame, text="📊 Xem Thống Kê", 
                command=lambda: self.apply_filters_paginated(self.current_uid, month_combo, category_combo),
                style='Accent.TButton').pack(side='left')
        
        # Dòng lọc danh mục
        category_frame = ttk.Frame(month_frame)
        category_frame.pack(fill='x', pady=5)
        
        ttk.Label(category_frame, text="Lọc theo Danh mục:").pack(side='left', padx=(0, 10))
        category_combo = ttk.Combobox(category_frame, 
                                    values=["Tất cả", "Ăn uống", "Giải trí", "Giao thông vận tải", "Sở thích","Sinh hoạt", "Áo quần", "Làm đẹp", "Sức khỏe","Giáo dục", "Sự kiện", "Mua sắm", "Khác"], 
                                    width=15)
        category_combo.pack(side='left')
        category_combo.current(0)
        
        # Khung phan trang
        chart_notebook = ttk.Notebook(frame)
        chart_notebook.pack(fill='both', expand=True, padx=10, pady=2)
        
        self.column_frame = ttk.Frame(chart_notebook)
        chart_notebook.add(self.column_frame, text="Biểu đồ Cột ")
        
        self.pie_frame = ttk.Frame(chart_notebook)
        chart_notebook.add(self.pie_frame, text="Biểu đồ Tròn ")
        
        self.raw_data_frame = ttk.Frame(chart_notebook)
        chart_notebook.add(self.raw_data_frame, text="Dữ liệu Chi Tiêu ")
        
        # ttk.Button(filter_frame, text="ÁP DỤNG LỌC",command=lambda: self.apply_filters_paginated(self.current_uid, time_combo, category_combo)).grid(row=0, column=2, rowspan=2, padx=10, pady=5)
        

        # Bảng Tóm Tắt (Yêu cầu Tóm tắt)
        summary_frame = ttk.LabelFrame(frame, text="📈 TÓM TẮT THÁNG", padding=15)
        summary_frame.pack(fill='x', padx=50, pady=10)
        
        # Hiển thị tháng đang xem
        self.month_label = ttk.Label(summary_frame, 
                                text=f"Đang xem tháng: {self.selected_month.get()}",
                                font=('Arial', 12, 'bold'),
                                foreground='#007bff')
        self.month_label.pack(pady=(0, 10))
        
        # Frame chứa các chỉ số thống kê
        self.summary_stats_frame = ttk.Frame(summary_frame)
        self.summary_stats_frame.pack(fill='x')
        
        # Áp dụng lọc mặc định
        self.apply_filters_paginated(self.current_uid, month_combo, category_combo)

    def _generate_month_list(self):
        """Tạo danh sách các tháng có dữ liệu"""
        try:
            expenses = backend.get_expenses(self.current_uid)
            months_set = set()
            
            for expense_data in expenses.values():
                date_str = expense_data.get('date', '')
                if date_str:
                    try:
                        from dateutil import parser
                        expense_date = parser.parse(date_str).date()
                        months_set.add(expense_date.strftime('%Y-%m'))
                    except:
                        continue
            
            # Sắp xếp từ mới nhất đến cũ nhất
            months_list = sorted(months_set, reverse=True)
            
            # Nếu không có dữ liệu, thêm tháng hiện tại
            if not months_list:
                months_list = [datetime.now().strftime('%Y-%m')]
                
            return months_list
            
        except Exception as e:
            print(f"Lỗi tạo danh sách tháng: {e}")
            return [datetime.now().strftime('%Y-%m')]
    
    def show_settings(self):
        """Màn hình Cài Đặt & Tài Khoản"""
        from settings_window import SettingsWindow
    
        # Xóa nội dung cũ
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
        # Lấy thông tin user
        user_data = {}
        if hasattr(self, "current_uid"):
            user_data = get_user_data(self.current_uid)

        # Tạo settings window
        SettingsWindow(self.content_frame, getattr(self, 'current_uid', None), user_data)

    def show_admin_panel(self):
        """Trang quản trị: chỉ dành cho admin"""
        frame = ttk.Frame(self.content_frame, padding="30 30 30 30")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="👑 TRANG QUẢN TRỊ HỆ THỐNG",
                  style='Header.TLabel',
                  foreground='red').pack(pady=(0, 20))

        table_frame = ttk.Frame(frame)
        table_frame.pack(fill="both", expand=True, pady=10)

        columns = ("fullname", "email", "role", "created_at")
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=12)
        tree.heading("fullname", text="Họ tên")
        tree.heading("email", text="Email")
        tree.heading("role", text="Role")
        tree.heading("created_at", text="Ngày tạo")

        tree.column("fullname", width=220)
        tree.column("email", width=200)
        tree.column("role", width=80, anchor=tk.CENTER)
        tree.column("created_at", width=140, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.users_tree = tree
        self.selected_user_id = None
        tree.bind("<<TreeviewSelect>>", self._on_user_select)
        self._load_user_list()

        control_frame = ttk.LabelFrame(frame, text="Thao tác tài khoản", padding=15)
        control_frame.pack(fill="x", pady=15)

        ttk.Label(control_frame, text="Quyền truy cập mới:").grid(row=0, column=0, sticky="w")
        self.admin_role_var = tk.StringVar(value="user")
        role_combo = ttk.Combobox(
            control_frame,
            textvariable=self.admin_role_var,
            values=["user", "admin"],
            state="readonly",
            width=12
        )
        role_combo.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ttk.Button(control_frame, text="Cập nhật quyền",
                   command=self.update_selected_user_role).grid(row=0, column=2, padx=10, pady=5)

        ttk.Button(control_frame, text="Xóa tài khoản",
                   command=self.delete_selected_user).grid(row=0, column=3, padx=10, pady=5)

        ttk.Button(control_frame, text="Tạo tài khoản mới",
                   command=self.open_admin_signup_window).grid(row=0, column=4, padx=10, pady=5)

        ttk.Label(frame,
                  text="* Chỉ quản trị viên mới truy cập được trang này.",
                  font=('Arial', 9, 'italic'),
                  foreground='#6c757d').pack(pady=5)

    def _load_user_list(self):
        """Nạp danh sách user vào Treeview"""
        if not self.users_tree:
            return

        for item in self.users_tree.get_children():
            self.users_tree.delete(item)

        users = backend.get_all_users()
        if not users:
            return

        for uid, info in sorted(users.items(), key=lambda item: item[1].get("email", "")):
            self.users_tree.insert(
                "",
                tk.END,
                iid=uid,
                values=(
                    info.get("fullname", "Chưa cập nhật"),
                    info.get("email", ""),
                    info.get("role", "user"),
                    info.get("created_at", "")
                )
            )

    def _on_user_select(self, _event):
        """Lưu lại user đang được chọn trong bảng"""
        if not self.users_tree:
            return
        selection = self.users_tree.selection()
        if not selection:
            self.selected_user_id = None
            return

        self.selected_user_id = selection[0]
        current_role = self.users_tree.set(self.selected_user_id, "role")
        if self.admin_role_var:
            self.admin_role_var.set(current_role)

    def update_selected_user_role(self):
        """Cập nhật role cho user được chọn"""
        if not self.selected_user_id:
            messagebox.showwarning("Thông báo", "Vui lòng chọn tài khoản cần cập nhật.")
            return

        new_role = self.admin_role_var.get()
        if self.selected_user_id == self.current_uid and new_role != "admin":
            confirm = messagebox.askyesno(
                "Xác nhận",
                "Bạn đang hạ quyền của chính mình. Tiếp tục?"
            )
            if not confirm:
                return

        success = backend.update_user_role(self.selected_user_id, new_role)
        if success:
            messagebox.showinfo("Thành công", "Đã cập nhật quyền truy cập.")
            self._load_user_list()
        else:
            messagebox.showerror("Lỗi", "Không thể cập nhật quyền. Thử lại sau.")

    def delete_selected_user(self):
        """Xóa user được chọn khỏi hệ thống"""
        if not self.selected_user_id:
            messagebox.showwarning("Thông báo", "Vui lòng chọn tài khoản để xóa.")
            return
        if self.selected_user_id == self.current_uid:
            messagebox.showwarning("Cảnh báo", "Không thể xóa tài khoản đang đăng nhập.")
            return
        if not messagebox.askyesno("Xác nhận", "Bạn chắc chắn muốn xóa tài khoản này?"):
            return

        success = backend.delete_user_account(self.selected_user_id)
        if success:
            messagebox.showinfo("Thành công", "Đã xóa tài khoản.")
            self.selected_user_id = None
            self._load_user_list()
        else:
            messagebox.showerror("Lỗi", "Không thể xóa tài khoản. Thử lại sau.")

    def open_admin_signup_window(self):
        """Cho phép admin tạo nhanh tài khoản mới"""
        signup_win = tk.Toplevel(self.master)
        signup_win.title("Tạo tài khoản mới")
        signup_win.geometry("420x520")

        ttk.Label(signup_win, text="TẠO TÀI KHOẢN", font=('Arial', 16, 'bold')).pack(pady=10)

        fields = {
            "Họ tên": tk.StringVar(),
            "Ngày sinh (YYYY-MM-DD)": tk.StringVar(),
            "Quê quán": tk.StringVar(),
            "Nghề nghiệp": tk.StringVar(),
            "Email": tk.StringVar(),
            "Mật khẩu": tk.StringVar()
        }

        for label, var in fields.items():
            ttk.Label(signup_win, text=label + ":").pack(pady=3)
            show = "*" if "Mật khẩu" in label else None
            ttk.Entry(signup_win, textvariable=var, width=35, show=show).pack(pady=3)

        ttk.Label(signup_win, text="Role:").pack(pady=(10, 3))
        new_role_var = tk.StringVar(value="user")
        ttk.Combobox(signup_win, textvariable=new_role_var,
                     values=["user", "admin"], state="readonly", width=15).pack(pady=3)

        def handle_create():
            data = {k: v.get().strip() for k, v in fields.items()}
            if not all(data.values()):
                messagebox.showwarning("Thiếu thông tin", "Điền đầy đủ các trường bắt buộc.")
                return

            created = signup_user(
                data["Email"],
                data["Mật khẩu"],
                data["Họ tên"],
                data["Ngày sinh (YYYY-MM-DD)"],
                data["Quê quán"],
                data["Nghề nghiệp"]
            )

            if created:
                desired_role = new_role_var.get()
                if desired_role != "user":
                    backend.update_user_role(created["uid"], desired_role)
                messagebox.showinfo("Thành công", "Đã tạo tài khoản mới.")
                signup_win.destroy()
                self._load_user_list()
            else:
                messagebox.showerror("Lỗi", "Không thể tạo tài khoản. Kiểm tra lại email.")

        ttk.Button(signup_win, text="Tạo tài khoản", command=handle_create).pack(pady=20)

def open_signup_window(self):
    signup_win = tk.Toplevel(self.master)
    signup_win.title("Đăng ký tài khoản mới")
    signup_win.geometry("400x500")

    ttk.Label(signup_win, text="TẠO TÀI KHOẢN MỚI", font=('Arial', 16, 'bold')).pack(pady=10)

    fields = {
        "Họ tên": tk.StringVar(),
        "Ngày sinh (YYYY-MM-DD)": tk.StringVar(),
        "Quê quán": tk.StringVar(),
        "Nghề nghiệp": tk.StringVar(),
        "Email": tk.StringVar(),
        "Mật khẩu": tk.StringVar()
    }

    entries = {}
    for label, var in fields.items():
        ttk.Label(signup_win, text=label + ":").pack(pady=3)
        show = "*" if "Mật khẩu" in label else None
        entry = ttk.Entry(signup_win, width=35, textvariable=var, show=show)
        entry.pack(pady=3)
        entries[label] = entry

    def handle_signup():
        data = {k: v.get().strip() for k, v in fields.items()}
        if not all(data.values()):
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đầy đủ tất cả các trường.")
            return

        result = signup_user(
            data["Email"], data["Mật khẩu"],
            data["Họ tên"], data["Ngày sinh (YYYY-MM-DD)"],
            data["Quê quán"], data["Nghề nghiệp"]
        )
        if result:
            messagebox.showinfo("Thành công", "Tài khoản đã được tạo thành công!")
            signup_win.destroy()
        else:
            messagebox.showerror("Lỗi", "Không thể tạo tài khoản. Email có thể đã tồn tại.")

    ttk.Button(signup_win, text="Đăng ký", command=handle_signup).pack(pady=20)

def open_main_app(uid, role):
    """Mở giao diện chính sau khi đăng nhập"""
    main_root = tk.Tk()
    ExpenseApp(main_root, current_uid=uid, role=role)
    main_root.mainloop()

class LoginWindow:
    """Cửa sổ Đăng nhập - liên kết với backend Firebase"""
    def __init__(self, master):
        self.master = master
        master.title("Đăng nhập - Quản lý chi tiêu")
        master.geometry("400x350")

        ttk.Label(master, text="🔐 ĐĂNG NHẬP HỆ THỐNG", font=('Arial', 16, 'bold')).pack(pady=20)

        ttk.Label(master, text="Email:").pack(pady=5)
        self.email_entry = ttk.Entry(master, width=35)
        self.email_entry.pack(pady=5)

        ttk.Label(master, text="Mật khẩu:").pack(pady=5)
        self.password_entry = ttk.Entry(master, width=35, show="*")
        self.password_entry.pack(pady=5)

        ttk.Button(master, text="Đăng nhập", command=self.login).pack(pady=10)
        ttk.Button(master, text="Tạo tài khoản mới", command=lambda: open_signup_window(self)).pack(pady=5)

        self.status_label = ttk.Label(master, text="", foreground="red")
        self.status_label.pack(pady=10)

    def login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email or not password:
            self.status_label.config(text="Vui lòng nhập đủ thông tin!")
            return

        user_data = login_user(email, password)
        if user_data:
            self.status_label.config(text="Đăng nhập thành công!", foreground="green")
            role = user_data.get("role", "user")
            print(f"Người dùng với vai trò: {role}")
            self.master.destroy()
            open_main_app(user_data["uid"], role)
        else:
            self.status_label.config(text="Sai thông tin đăng nhập!", foreground="red")

if __name__ == '__main__':
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()
