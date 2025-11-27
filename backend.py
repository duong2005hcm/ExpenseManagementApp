import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import auth as admin_auth
import pyrebase
import threading
import datetime
import os
import unicodedata

# ===============================
# 🔧 CẤU HÌNH FIREBASE
# ===============================
firebaseConfig = {
    "apiKey": "AIzaSyAVZ9vi3SGOfJ2lAKYxHpduMqtRfnqvftc",
    "authDomain": "pythonproject-70909.firebaseapp.com",
    "projectId": "pythonproject-70909",
    "storageBucket": "pythonproject-70909.appspot.com",
    "messagingSenderId": "858597298973",
    "appId": "1:858597298973:web:7f2da00bbcf72983fa47f4",
    "measurementId": "G-34YJT4GCWC",
    "databaseURL": "https://pythonproject-70909-default-rtdb.firebaseio.com"
}

# --- Khởi tạo Auth (Pyrebase) ---
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
storage = firebase.storage()

# --- Khởi tạo Firestore ---
if not firebase_admin._apps:
    cred = credentials.Certificate("D:\Python\myprojectApp\src\serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# ===============================
# 🔐 CÁC HÀM AUTHENTICATION
# ===============================

def signup_user(email, password, fullname, birthdate, hometown, job):
    """Đăng ký tài khoản + lưu thông tin vào Firestore"""
    try:
        print("🔸 Bắt đầu đăng ký user...")
        
        # Tạo tài khoản Auth
        user = auth.create_user_with_email_and_password(email, password)
        info = auth.get_account_info(user['idToken'])
        uid = info['users'][0]['localId']
        print(f"✅ Đã tạo Auth user: {uid}")

        # Tạo dữ liệu người dùng
        user_data = {
            "uid": uid,
            "email": email,
            "fullname": fullname,
            "birthdate": birthdate,
            "hometown": hometown,
            "job": job,
            "role": "user",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Lưu vào Firestore
        try:
            print("🔸 Đang ghi vào Firestore...")
            db.collection("Users").document(uid).set(user_data)
            print(f"✅ Đã lưu thông tin vào Firestore thành công!")
        except Exception as firestore_error:
            print(f"❌ Lỗi Firestore: {firestore_error}")
            return None

        return user_data
        
    except Exception as e:
        print(f"❌ Lỗi tổng quát khi đăng ký: {e}")
        import traceback
        traceback.print_exc()
        return None

def login_user(email, password):
    """Đăng nhập và trả về UID"""
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        info = auth.get_account_info(user['idToken'])
        uid = info['users'][0]['localId']
        print(f"✅ Đăng nhập thành công: {email}")
        profile = get_user_data(uid)
        role = profile.get("role", "user") if profile else "user"
        return {"user": user, "uid": uid, "role": role, "profile": profile}
    except Exception as e:
        print("❌ Lỗi khi đăng nhập:", e)
        return None

def get_user_data(uid):
    """Lấy thông tin user từ Firestore"""
    try:
        doc_ref = db.collection("Users").document(uid)
        doc = doc_ref.get()
        
        if doc.exists:
            user_data = doc.to_dict()
            print(f"✅ Đã lấy thông tin user từ Firestore: {user_data.get('email', 'Unknown')}")
            return user_data
        else:
            print(f"⚠️ Không tìm thấy user data trong Firestore cho UID: {uid}")
            return None
    except Exception as e:
        print(f"❌ Lỗi lấy user data từ Firestore: {e}")
        return None

def update_user_profile(uid, user_data):
    """Cập nhật thông tin người dùng trong Firestore"""
    try:
        db.collection("Users").document(uid).update(user_data)
        print(f"✅ Đã cập nhật profile user trong Firestore: {user_data}")
        return True
    except Exception as e:
        print(f"❌ Lỗi update profile trong Firestore: {e}")
        return False

def add_plan(uid, date, desc, amount):
    """Thêm kế hoạch chi tiêu vào Firestore"""
    try:
        plan_data = {
            "date": date,
            "desc": desc,
            "amount": amount,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": uid
        }
        
        # Thêm vào collection "Planning"
        doc_ref = db.collection("Planning").document()
        doc_ref.set(plan_data)
        
        print(f"✅ Đã thêm kế hoạch: {date} - {desc} - {amount:,} VNĐ")
        return True
    except Exception as e:
        print(f"❌ Lỗi thêm kế hoạch: {e}")
        return False

def get_plans(uid):
    """Lấy tất cả kế hoạch của user từ Firestore"""
    try:
        plans_ref = db.collection("Planning").where("user_id", "==", uid)
        docs = plans_ref.stream()
        
        plans = {}
        for doc in docs:
            plans[doc.id] = doc.to_dict()
        
        print(f"✅ Đã lấy {len(plans)} kế hoạch từ Firestore")
        return plans
    except Exception as e:
        print(f"❌ Lỗi lấy kế hoạch: {e}")
        return {}

def delete_plan(uid, plan_id):
    """Xóa kế hoạch từ Firestore"""
    try:
        # Kiểm tra xem kế hoạch có thuộc về user này không
        doc_ref = db.collection("Planning").document(plan_id)
        doc = doc_ref.get()
        
        if doc.exists and doc.to_dict().get('user_id') == uid:
            doc_ref.delete()
            print(f"✅ Đã xóa kế hoạch: {plan_id}")
            return True
        else:
            print("❌ Không tìm thấy kế hoạch hoặc không có quyền xóa")
            return False
    except Exception as e:
        print(f"❌ Lỗi xóa kế hoạch: {e}")
        return False

# Trong file backend.py - Thêm vào class Backend

class Backend:
    """Làm việc với Firestore cho các giao dịch Thu/Chi/Chuyển khoản."""

    TRANSACTION_COLLECTIONS = {
        "Chi": "Expenses",
        "Thu": "Income",
        "Chuyển khoản": "Transfers"
    }

    TRANSACTION_ALIASES = {
        "chi": "Chi",
        "thu": "Thu",
        "chuyenkhoan": "Chuyển khoản",
        "chuyểnkhoản": "Chuyển khoản",
        "chuyển khoản": "Chuyển khoản",
        "chuyen khoan": "Chuyển khoản",
    }

    def _strip_accents(self, text):
        normalized = unicodedata.normalize("NFKD", text)
        return "".join(ch for ch in normalized if not unicodedata.combining(ch))

    def _normalize_transaction_type(self, transaction_type):
        raw = str(transaction_type or "").strip()
        if not raw:
            return "Chi"

        lowered = raw.lower()
        if lowered in self.TRANSACTION_ALIASES:
            return self.TRANSACTION_ALIASES[lowered]

        ascii_lower = self._strip_accents(lowered).replace(" ", "")
        return self.TRANSACTION_ALIASES.get(ascii_lower, "Chi")

    def _get_collection_name(self, transaction_type):
        normalized_type = self._normalize_transaction_type(transaction_type)
        collection_name = self.TRANSACTION_COLLECTIONS.get(normalized_type, "Expenses")
        return normalized_type, collection_name

    def _resolve_transaction_types(self, transaction_type):
        """Chuẩn hóa danh sách transaction_type cần lấy."""
        if transaction_type is None:
            return list(self.TRANSACTION_COLLECTIONS.keys())

        if isinstance(transaction_type, (list, tuple, set)):
            types = [self._normalize_transaction_type(t) for t in transaction_type]
            return [t for t in types if t in self.TRANSACTION_COLLECTIONS]

        lowered = str(transaction_type).strip().lower()
        if lowered in {"all", "*"}:
            return list(self.TRANSACTION_COLLECTIONS.keys())

        normalized = self._normalize_transaction_type(transaction_type)
        return [normalized]

    def _build_transaction_payload(self, uid, date, category, amount, note, transaction_type, created_at=None):
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "date": date,
            "category": category,
            "amount": amount,
            "note": note,
            "transaction_type": transaction_type,
            "user_id": uid,
            "updated_at": now_str
        }
        payload["created_at"] = created_at or now_str
        return payload

    def add_expense(self, uid, date, category, amount, note="", transaction_type="Chi"):
        """Thêm giao dịch vào Firestore theo đúng loại."""
        try:
            transaction_type, collection_name = self._get_collection_name(transaction_type)
            expense_data = self._build_transaction_payload(
                uid, date, category, amount, note, transaction_type
            )

            doc_ref = db.collection(collection_name).document()
            doc_ref.set(expense_data)

            print(f"✅ Đã thêm giao dịch {transaction_type}: {date} - {category} - {amount:,} VNĐ")
            return True
        except Exception as e:
            print(f"❌ Lỗi thêm giao dịch: {e}")
            return False

    def get_expenses(self, uid, transaction_type="Chi"):
        """
        Lấy giao dịch từ Firestore.
        transaction_type: "Chi" (default) hoặc "Thu"/"Chuyển khoản"/"all"/None.
        """
        try:
            types_to_fetch = self._resolve_transaction_types(transaction_type)
            multi_type = len(types_to_fetch) > 1

            expenses = {}
            for tx_type in types_to_fetch:
                collection_name = self.TRANSACTION_COLLECTIONS[tx_type]
                docs = db.collection(collection_name).where("user_id", "==", uid).stream()

                for doc in docs:
                    data = doc.to_dict()
                    data.setdefault("transaction_type", tx_type)
                    key = doc.id if not multi_type else f"{collection_name}:{doc.id}"
                    expenses[key] = data

            print(f"✅ Đã lấy {len(expenses)} giao dịch ({', '.join(types_to_fetch)}) từ Firestore")
            return expenses
        except Exception as e:
            print(f"❌ Lỗi lấy giao dịch: {e}")
            return {}

    def update_expense(
        self,
        uid,
        expense_id,
        date,
        category,
        amount,
        note="",
        transaction_type="Chi",
        original_transaction_type=None
    ):
        """Cập nhật giao dịch trong Firestore và chuyển collection nếu đổi loại."""
        try:
            new_type = self._normalize_transaction_type(transaction_type)
            original_type = self._normalize_transaction_type(original_transaction_type or transaction_type)

            new_collection = self.TRANSACTION_COLLECTIONS[new_type]
            original_collection = self.TRANSACTION_COLLECTIONS[original_type]
            origin_ref = db.collection(original_collection).document(expense_id)
            origin_doc = origin_ref.get()

            if not (origin_doc.exists and origin_doc.to_dict().get('user_id') == uid):
                print("❌ Không tìm thấy giao dịch hoặc không có quyền sửa")
                return False

            existing_data = origin_doc.to_dict()
            payload = self._build_transaction_payload(
                uid,
                date,
                category,
                amount,
                note,
                new_type,
                created_at=existing_data.get("created_at")
            )

            if new_type == original_type:
                origin_ref.update(payload)
                print(f"✅ Đã cập nhật giao dịch: {expense_id}")
                return True

            # Chuyển document sang collection mới khi đổi loại giao dịch.
            new_ref = db.collection(new_collection).document(expense_id)
            new_ref.set(payload)
            origin_ref.delete()
            print(f"✅ Đã chuyển giao dịch sang loại {new_type}: {expense_id}")
            return True
        except Exception as e:
            print(f"❌ Lỗi cập nhật giao dịch: {e}")
            return False

    def delete_expense(self, uid, expense_id, transaction_type="Chi"):
        """Xóa giao dịch từ Firestore theo loại."""
        try:
            transaction_type = self._normalize_transaction_type(transaction_type)
            collection_name = self.TRANSACTION_COLLECTIONS[transaction_type]
            doc_ref = db.collection(collection_name).document(expense_id)
            doc = doc_ref.get()

            if doc.exists and doc.to_dict().get('user_id') == uid:
                doc_ref.delete()
                print(f"✅ Đã xóa giao dịch {transaction_type}: {expense_id}")
                return True
            else:
                print("❌ Không tìm thấy giao dịch hoặc không có quyền xóa")
                return False
        except Exception as e:
            print(f"❌ Lỗi xóa giao dịch: {e}")
            return False

    def get_all_users(self):
        """Lấy toàn bộ tài khoản để hiển thị trên trang admin"""
        try:
            docs = db.collection("Users").stream()
            users = {}
            for doc in docs:
                users[doc.id] = doc.to_dict()
            print(f"✅ Lấy {len(users)} tài khoản từ Firestore")
            return users
        except Exception as e:
            print(f"❌ Lỗi lấy danh sách user: {e}")
            return {}

    def update_user_role(self, uid, new_role):
        """Cập nhật quyền hạn của user"""
        try:
            db.collection("Users").document(uid).update({"role": new_role})
            print(f"✅ Đã cập nhật role {new_role} cho user {uid}")
            return True
        except Exception as e:
            print(f"❌ Lỗi cập nhật role: {e}")
            return False

    def delete_user_account(self, uid):
        """Xóa tài khoản khỏi Firestore + Firebase Auth"""
        try:
            db.collection("Users").document(uid).delete()
            try:
                admin_auth.delete_user(uid)
            except Exception as auth_error:
                # Có thể tài khoản Auth đã bị xóa trước đó, log rồi tiếp tục
                print(f"⚠️ Không thể xóa auth user {uid}: {auth_error}")
            print(f"✅ Đã xóa tài khoản {uid}")
            return True
        except Exception as e:
            print(f"❌ Lỗi xóa tài khoản: {e}")
            return False
