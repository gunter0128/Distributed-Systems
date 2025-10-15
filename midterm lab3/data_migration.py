import os
import time
import hashlib
import socket
import msgpackrpc
from ec2_metadata import ec2_metadata  # AWS EC2 Metadata 模組 (可用於獲取節點 IP)

# === 參數設定 ===
files_directory = "/home/ec2-user/path/to/files"  # 本地檔案目錄
port = 5067  # RPC 伺服器的 Port

# === 工具函數 ===
def get_file_hash(filename):
    """計算檔案名稱的哈希值（MD5）"""
    return int(hashlib.md5(filename.encode()).hexdigest(), 16) % (1 << 32)

def should_keep_file(file_hash, my_id, predecessor_id):
    """判斷檔案是否應該保留在當前節點"""
    if predecessor_id < my_id:
        return predecessor_id < file_hash <= my_id
    else:  # 跨越 Hash 環的邊界
        return file_hash > predecessor_id or file_hash <= my_id

def is_port_in_use(port):
    """檢查 Port 是否已經被佔用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("0.0.0.0", port)) == 0

# === RPC 調度器類別 ===
class Dispatcher:
    def __init__(self, node_id, ip):
        self.node_id = node_id
        self.ip = ip

    def get_info(self):
        """回傳節點的基本資訊"""
        return {"id": self.node_id, "ip": self.ip}

    def join(self, node_info):
        """處理節點加入邏輯"""
        print(f"[DEBUG] 收到加入請求，節點資訊: {node_info}")
        return "Join Successful"

    def migrate(self):
        """觸發資料遷移"""
        print("[DEBUG] 觸發資料遷移...")
        migrate_data()

# === 加入 Chord 網路邏輯 ===
def join_ring(first_node_ip=None):
    global current_node
    try:
        print(f"[DEBUG] 嘗試連接第一個節點 IP: {first_node_ip}")
        if not first_node_ip:
            print("[DEBUG] 初始化第一個節點...")
            return  # 第一個節點直接啟動

        # 連接第一個節點
        first_node = msgpackrpc.Client(msgpackrpc.Address(first_node_ip, port))
        current_node_info = {"id": node_id, "ip": node_ip}
        print(f"[DEBUG] 發送加入請求，節點資訊: {current_node_info}")

        response = first_node.call("join", current_node_info)
        print(f"[DEBUG] 第一個節點回應: {response}")

    except Exception as e:
        print(f"[ERROR] 無法加入第一個節點: {e}")

# === 資料遷移邏輯 ===
def migrate_data():
    try:
        print("[DEBUG] 開始執行資料遷移...")
        # 獲取 Predecessor 節點資訊
        predecessor_info = current_node.call("get_predecessor")
        if not predecessor_info:
            print("[DEBUG] 未找到 Predecessor，無需遷移資料")
            return

        predecessor_id = predecessor_info["id"]
        print(f"[DEBUG] Predecessor ID: {predecessor_id}, My ID: {node_id}")

        # 檢查本地檔案，判斷是否需要遷移
        local_files = os.listdir(files_directory)
        print(f"[DEBUG] 本地檔案列表: {local_files}")

        for filename in local_files:
            file_hash = get_file_hash(filename)
            if should_keep_file(file_hash, node_id, predecessor_id):
                print(f"[DEBUG] 檔案 {filename} 屬於當前節點，保留")
                continue

            # 找到負責節點並遷移檔案
            correct_node = current_node.call("find_successor", file_hash)
            print(f"[DEBUG] 檔案 {filename} 應由節點 {correct_node} 負責，進行遷移...")
    except Exception as e:
        print(f"[ERROR] 資料遷移失敗: {e}")

# === 主執行邏輯 ===
if __name__ == "__main__":
    # 取得節點的私有 IP 和 Node ID
    try:
        node_ip = ec2_metadata.private_ipv4
    except Exception:
        node_ip = "127.0.0.1"  # 若無法獲取，預設本地 IP

    node_id = int(hashlib.md5(node_ip.encode()).hexdigest(), 16) % (1 << 32)
    dispatcher = Dispatcher(node_id, node_ip)

    # 啟動 RPC 伺服器
    if is_port_in_use(port):
        print(f"[ERROR] Port {port} 已被佔用，請先釋放該 Port。")
        exit(1)

    server = msgpackrpc.Server(dispatcher)
    server.listen(msgpackrpc.Address("0.0.0.0", port))
    print(f"[INFO] RPC 伺服器已啟動 (IP: {node_ip}, Port: {port})，正在等待請求...")

    # 判斷是否為新加入節點
    import sys
    first_node_ip = sys.argv[1] if len(sys.argv) > 1 else None
    join_ring(first_node_ip)

    server.start()
