# 🖥️ Panduan Install di 3 Laptop Fisik (Ubuntu)

Panduan ini untuk **Phase 2: Production Deployment** pada 3 laptop fisik tanpa Docker.

---

## 📋 Prerequisites

### Hardware Requirements:
- **3 Laptop** dengan Ubuntu 20.04+ atau Debian-based Linux
- **Koneksi jaringan** yang sama (WiFi/LAN)
- **Minimal RAM**: 2GB per laptop
- **Minimal Storage**: 10GB free space per laptop

### Network Setup:
Pastikan semua laptop bisa saling ping. Contoh IP:
- **Laptop 1 (Bootstrap Node)**: 192.168.1.10
- **Laptop 2**: 192.168.1.11
- **Laptop 3**: 192.168.1.12

> **PENTING:** Ganti IP di atas dengan IP real laptop kamu. Cek dengan: `ip a` atau `hostname -I`

---

## 🔧 STEP 1: Setup di SEMUA 3 Laptop

Lakukan langkah ini di **Laptop 1, 2, dan 3**.

### 1.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Install MariaDB Server + Galera

**Untuk Ubuntu/Debian:**
```bash
sudo apt install -y mariadb-server mariadb-backup galera-4 rsync
```

**Untuk Fedora/RHEL:**
```bash
sudo dnf install -y mariadb-server galera rsync
```

### 1.3 Stop MariaDB (biar nggak bentrok saat config)
```bash
sudo systemctl stop mariadb
```

### 1.4 Cek IP Address Laptop Ini
```bash
hostname -I
# Catat IP-nya! Contoh: 192.168.1.10
```

---

## ⚙️ STEP 2: Konfigurasi Galera di SETIAP Laptop

### 2.1 Buka File Konfigurasi

**Untuk Ubuntu/Debian:**
```bash
sudo nano /etc/mysql/mariadb.conf.d/60-galera.cnf
```

**Untuk Fedora/RHEL:**
```bash
sudo nano /etc/my.cnf.d/galera.cnf
```

### 2.2 Isi Konfigurasi

**Untuk LAPTOP 1 (IP: 192.168.1.10):**
```ini
[mysqld]
# Galera Settings
binlog_format=ROW
default_storage_engine=InnoDB
innodb_autoinc_lock_mode=2
bind-address=0.0.0.0

# Galera Provider Configuration
wsrep_on=ON
wsrep_provider=/usr/lib/galera/libgalera_smm.so

# Galera Cluster Configuration
wsrep_cluster_name="galera_cluster"
wsrep_cluster_address="gcomm://192.168.1.10,192.168.1.11,192.168.1.12"

# Galera Node Configuration (GANTI UNTUK SETIAP LAPTOP!)
wsrep_node_address="192.168.1.10"
wsrep_node_name="laptop1"
wsrep_sst_method=rsync

# Performance
wsrep_slave_threads=4
```

**Untuk LAPTOP 2 (IP: 192.168.1.11):**
```ini
[mysqld]
# Galera Settings
binlog_format=ROW
default_storage_engine=InnoDB
innodb_autoinc_lock_mode=2
bind-address=0.0.0.0

# Galera Provider Configuration
wsrep_on=ON
wsrep_provider=/usr/lib/galera/libgalera_smm.so

# Galera Cluster Configuration
wsrep_cluster_name="galera_cluster"
wsrep_cluster_address="gcomm://192.168.1.10,192.168.1.11,192.168.1.12"

# Galera Node Configuration (BEDA DARI LAPTOP 1!)
wsrep_node_address="192.168.1.11"
wsrep_node_name="laptop2"
wsrep_sst_method=rsync

# Performance
wsrep_slave_threads=4
```

**Untuk LAPTOP 3 (IP: 192.168.1.12):**
```ini
[mysqld]
# Galera Settings
binlog_format=ROW
default_storage_engine=InnoDB
innodb_autoinc_lock_mode=2
bind-address=0.0.0.0

# Galera Provider Configuration
wsrep_on=ON
wsrep_provider=/usr/lib/galera/libgalera_smm.so

# Galera Cluster Configuration
wsrep_cluster_name="galera_cluster"
wsrep_cluster_address="gcomm://192.168.1.10,192.168.1.11,192.168.1.12"

# Galera Node Configuration (BEDA DARI LAPTOP 1 & 2!)
wsrep_node_address="192.168.1.12"
wsrep_node_name="laptop3"
wsrep_sst_method=rsync

# Performance
wsrep_slave_threads=4
```

> **PENTING:** Yang BEDA hanya `wsrep_node_address` dan `wsrep_node_name`. Sisanya sama!

### 2.3 Simpan File
```bash
# Tekan Ctrl+O (Save)
# Tekan Enter
# Tekan Ctrl+X (Exit)
```

---

## 🚀 STEP 3: Start Galera Cluster

### 3.1 Bootstrap Cluster di LAPTOP 1 (Yang Pertama!)

**HANYA DI LAPTOP 1:**
```bash
sudo galera_new_cluster
```

### 3.2 Cek Status di Laptop 1
```bash
sudo systemctl status mariadb
```

Harus keluar: **active (running)** ✅

### 3.3 Verify Cluster Size di Laptop 1
```bash
sudo mysql -e "SHOW STATUS LIKE 'wsrep_cluster_size';"
```

Output harus:
```
+--------------------+-------+
| Variable_name      | Value |
+--------------------+-------+
| wsrep_cluster_size | 1     |
+--------------------+-------+
```

### 3.4 Start MariaDB di LAPTOP 2 & 3

**DI LAPTOP 2:**
```bash
sudo systemctl start mariadb
sudo systemctl status mariadb
```

**DI LAPTOP 3:**
```bash
sudo systemctl start mariadb
sudo systemctl status mariadb
```

### 3.5 Verify Cluster Size (Di Laptop Mana Saja)
```bash
sudo mysql -e "SHOW STATUS LIKE 'wsrep_cluster_size';"
```

Output harus:
```
+--------------------+-------+
| Variable_name      | Value |
+--------------------+-------+
| wsrep_cluster_size | 3     |  <-- HARUS 3!
+--------------------+-------+
```

✅ **KALAU SUDAH 3 = CLUSTER BERHASIL!**

---

## 🔐 STEP 4: Setup Database & User

**Jalankan HANYA DI 1 LAPTOP** (data akan sync otomatis ke semua laptop).

### 4.1 Login ke MySQL
```bash
sudo mysql -u root
```

### 4.2 Set Password Root
```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY '030105';

-- Create remote root (biar bisa diakses dari laptop lain)
CREATE USER 'root'@'%' IDENTIFIED BY '030105';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;

FLUSH PRIVILEGES;
```

### 4.3 Create Database
```sql
CREATE DATABASE beauty;
USE beauty;

-- Create table products
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user untuk HAProxy health check
CREATE USER 'haproxy_check'@'%';
FLUSH PRIVILEGES;

EXIT;
```

### 4.4 Test dari Laptop Lain
Di **Laptop 2 atau 3**, test login:
```bash
mysql -uroot -p030105 -e "SHOW DATABASES; SELECT * FROM beauty.products;"
```

Kalau bisa lihat database `beauty` = **Replication SUKSES!** ✅

---

## 🔀 STEP 5: Setup HAProxy Load Balancer

Pilih **1 LAPTOP** untuk jadi HAProxy server (atau bisa laptop ke-4 kalau ada).

Misal dipilih **LAPTOP 1** (IP: 192.168.1.10)

### 5.1 Install HAProxy
```bash
sudo apt install -y haproxy
```

### 5.2 Backup Config Original
```bash
sudo cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.backup
```

### 5.3 Edit Config HAProxy
```bash
sudo nano /etc/haproxy/haproxy.cfg
```

### 5.4 Ganti Isinya dengan:
```haproxy
global
    log /dev/log local0
    log /dev/log local1 notice
    maxconn 4096
    user haproxy
    group haproxy
    daemon

defaults
    log     global
    mode    tcp
    option  tcplog
    option  dontlognull
    retries 3
    timeout connect 5000ms
    timeout client  50000ms
    timeout server  50000ms

# HAProxy Statistics Page
listen stats
    bind *:8404
    mode http
    stats enable
    stats uri /stats
    stats refresh 10s
    stats admin if TRUE
    stats auth admin:admin123

# MySQL/MariaDB Load Balancer
listen mysql-cluster
    bind *:3306
    mode tcp
    balance roundrobin
    option mysql-check user haproxy_check
    
    # GANTI IP DENGAN IP REAL LAPTOP KAMU!
    server laptop1 192.168.1.10:3306 check weight 1
    server laptop2 192.168.1.11:3306 check weight 1
    server laptop3 192.168.1.12:3306 check weight 1
```

**PENTING:** Ganti IP `192.168.1.x` dengan IP real laptop kamu!

### 5.5 Restart HAProxy
```bash
sudo systemctl restart haproxy
sudo systemctl enable haproxy
sudo systemctl status haproxy
```

### 5.6 Verify HAProxy
```bash
# Cek apakah listen di port 3306
sudo netstat -tlnp | grep 3306

# Test koneksi
mysql -h 127.0.0.1 -P 3306 -uroot -p030105 -e "SELECT @@hostname;"
```

Refresh beberapa kali, hostname harus berganti: `laptop1`, `laptop2`, `laptop3` ✅

### 5.7 Akses HAProxy Stats
Buka browser:
```
http://192.168.1.10:8404/stats
Username: admin
Password: admin123
```

---

## 🐍 STEP 6: Setup Python Flask App di SEMUA 3 Laptop

Untuk demo real-time, kita akan **running Flask app di SEMUA 3 laptop** secara bersamaan.

### 6.1 Install Dependencies (Di Semua 3 Laptop)
```bash
sudo apt install -y python3 python3-pip python3-venv git
```

### 6.2 Copy Project Files (Di Semua 3 Laptop)

**Opsi A: Clone dari Git (jika sudah di-push)**
```bash
cd ~
git clone <repo-url> sister
cd sister
```

**Opsi B: Transfer via USB/SCP**
```bash
# Di Laptop 1 (sumber)
cd ~/sister
tar -czf sister-app.tar.gz app.py requirements.txt templates/

# Copy ke Laptop 2 & 3 via USB atau:
scp sister-app.tar.gz user@192.168.1.11:~
scp sister-app.tar.gz user@192.168.1.12:~

# Di Laptop 2 & 3 (ekstrak)
cd ~
tar -xzf sister-app.tar.gz
```

### 6.3 Install Python Packages (Di Semua 3 Laptop)
```bash
cd ~/sister
pip3 install -r requirements.txt
```

### 6.4 Edit app.py (Di Semua 3 Laptop)

Buka `app.py` dan update konfigurasi database:

```bash
nano app.py
```

**Ganti bagian `DB_CONFIG`:**
```python
# Database Configuration - Connect to HAProxy
DB_CONFIG = {
    'host': '192.168.1.10',  # IP laptop yang running HAProxy
    'port': 3306,            # Port HAProxy
    'user': 'root',
    'password': '030105',
    'database': 'beauty'
}
```

**PENTING:** Semua laptop harus connect ke **IP HAProxy yang sama** (misal: 192.168.1.10)

**Simpan:** Ctrl+O, Enter, Ctrl+X

### 6.5 Tambahkan Auto-Refresh ke Frontend

Agar data update real-time, edit `templates/index.html`:

```bash
nano templates/index.html
```

**Tambahkan script auto-refresh SEBELUM tag `</body>`:**

Cari baris:
```html
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
```

Ganti jadi:
```html
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- Auto-refresh setiap 3 detik untuk real-time update -->
    <script>
        // Auto-refresh product table setiap 3 detik
        setInterval(function() {
            // Hanya reload table, jangan reload seluruh halaman
            window.location.reload();
        }, 3000); // 3000ms = 3 detik
    </script>
</body>
```

**Simpan:** Ctrl+O, Enter, Ctrl+X

### 6.6 Run Flask App di SEMUA 3 Laptop

**Di Laptop 1:**
```bash
cd ~/sister
python3 app.py
```

**Di Laptop 2 (di terminal berbeda):**
```bash
cd ~/sister
python3 app.py
```

**Di Laptop 3 (di terminal berbeda):**
```bash
cd ~/sister
python3 app.py
```

Output di semua laptop:
```
 * Running on http://0.0.0.0:5000
```

### 6.7 Akses dari Browser di Setiap Laptop

**Di Laptop 1:** Buka browser → `http://localhost:5000`  
**Di Laptop 2:** Buka browser → `http://localhost:5000`  
**Di Laptop 3:** Buka browser → `http://localhost:5000`

Atau akses dari laptop lain:
- `http://192.168.1.10:5000` (Laptop 1)
- `http://192.168.1.11:5000` (Laptop 2)
- `http://192.168.1.12:5000` (Laptop 3)

### 6.8 Test Real-Time Update

**Demo skenario:**
1. Buka aplikasi di **browser Laptop 1, 2, dan 3** secara bersamaan
2. Di **Laptop 1**: Insert produk "Lipstick Red" 
3. **Dalam 3 detik**, produk akan muncul di browser Laptop 2 & 3 otomatis! ✅
4. Di **Laptop 2**: Insert produk "Foundation Glow"
5. Produk muncul di browser Laptop 1 & 3! ✅

**Ini yang namanya REAL-TIME DISTRIBUTED SYSTEM!** 🚀

---

## ✅ STEP 7: Verification & Testing

### 7.1 Test Cluster Status
Di **semua laptop**, run:
```bash
mysql -uroot -p030105 -e "
SHOW STATUS LIKE 'wsrep_cluster_size';
SHOW STATUS LIKE 'wsrep_local_state_comment';
SHOW STATUS LIKE 'wsrep_ready';
"
```

**Output yang benar:**
```
wsrep_cluster_size           | 3
wsrep_local_state_comment    | Synced
wsrep_ready                  | ON
```

### 7.2 Test Load Balancing
```bash
# Di laptop yang running HAProxy/Flask
for i in {1..5}; do
  mysql -h 127.0.0.1 -P 3306 -uroot -p030105 -e "SELECT @@hostname;" 2>/dev/null | grep -v hostname
done
```

Output harus berganti-ganti: `laptop1`, `laptop2`, `laptop3`

### 7.3 Test Replication
**Di Laptop 1:**
```bash
mysql -uroot -p030105 beauty -e "INSERT INTO products (name, price, stock) VALUES ('Test Laptop1', 100000, 10);"
```

**Di Laptop 2:**
```bash
mysql -uroot -p030105 beauty -e "SELECT * FROM products;"
```

Data harus muncul di semua laptop! ✅

### 7.4 Test High Availability
**Matikan 1 laptop** (atau stop MariaDB):
```bash
sudo systemctl stop mariadb
```

Aplikasi Flask **MASIH JALAN** dan bisa insert/read data! ✅

---

## 🔥 Troubleshooting

### Problem 1: Cluster Size = 0 atau 1
**Solusi:**
```bash
# Cek firewall
sudo ufw status
sudo ufw allow 3306/tcp
sudo ufw allow 4567/tcp
sudo ufw allow 4568/tcp
sudo ufw allow 4444/tcp

# Cek log
sudo journalctl -u mariadb -f
```

### Problem 2: Node tidak bisa join cluster
**Solusi:**
```bash
# Di node yang bermasalah
sudo systemctl stop mariadb
sudo rm -rf /var/lib/mysql/grastate.dat
sudo systemctl start mariadb

# Cek status
sudo mysql -e "SHOW STATUS LIKE 'wsrep%';"
```

### Problem 3: HAProxy tidak bisa konek ke nodes
**Solusi:**
```bash
# Test manual dari laptop HAProxy
mysql -h 192.168.1.10 -P 3306 -uroot -p030105
mysql -h 192.168.1.11 -P 3306 -uroot -p030105
mysql -h 192.168.1.12 -P 3306 -uroot -p030105

# Pastikan user haproxy_check ada
mysql -uroot -p030105 -e "SELECT User, Host FROM mysql.user WHERE User='haproxy_check';"
```

### Problem 4: Flask app tidak konek
**Solusi:**
```bash
# Test manual
mysql -h <IP_HAPROXY> -P 3306 -uroot -p030105 beauty -e "SELECT * FROM products;"

# Cek port
sudo netstat -tlnp | grep 3306
```

---

## 📊 Command Cheat Sheet

### Check Cluster Status
```bash
mysql -uroot -p030105 -e "SHOW STATUS LIKE 'wsrep%';"
```

### View All Products
```bash
mysql -uroot -p030105 beauty -e "SELECT * FROM products;"
```

### Restart Semua Services
```bash
# Di semua laptop MariaDB
sudo systemctl restart mariadb

# Di laptop HAProxy
sudo systemctl restart haproxy

# Flask App
python3 app.py
```

### Monitoring Logs
```bash
# MariaDB logs
sudo journalctl -u mariadb -f

# HAProxy logs
sudo tail -f /var/log/haproxy.log
```

---

## 🎯 Final Checklist

Sebelum demo, pastikan:

- [ ] Semua 3 laptop bisa saling ping
- [ ] `wsrep_cluster_size` = 3 di semua laptop
- [ ] Database `beauty` dan table `products` ada
- [ ] HAProxy stats page bisa diakses
- [ ] Flask app bisa akses database
- [ ] Badge "Current Node" berganti-ganti saat refresh
- [ ] Test matikan 1 laptop → sistem tetap jalan
- [ ] Data sync ke semua laptop

---

## 🚀 Demo Script (Untuk Presentasi)

### Opening:
1. Tunjukkan 3 laptop dengan IP berbeda
2. Buka HAProxy stats → tunjukkan 3 nodes UP (hijau)
3. Buka aplikasi Flask → tunjukkan badge "Current Node"

### Demo Load Balancing:
1. Refresh aplikasi 5-10 kali
2. Tunjukkan badge berganti: laptop1 → laptop2 → laptop3
3. Buka HAProxy stats → tunjukkan distribusi session

### Demo High Availability:
1. Insert data produk baru
2. Matikan 1 laptop (shutdown atau stop mariadb)
3. Refresh HAProxy stats → 1 node merah, 2 hijau
4. Aplikasi **MASIH BISA** insert & read data
5. Nyalakan laptop lagi → otomatis rejoin cluster

### Demo Replication:
1. Insert data di aplikasi
2. Buka terminal di Laptop 2 atau 3
3. Query `SELECT * FROM products;`
4. Data sama persis!

---

**Good luck untuk demo-nya! Kalau ada masalah, cek Troubleshooting section di atas.** 🚀

**Made with ❤️ for Final Project Distributed Systems**
