# 📘 Tutorial Lengkap Setup Galera Cluster 3 Nodes Ubuntu
## Production-Ready High Availability Database

---

## 📋 Prasyarat

### Hardware
- **3 Laptop/PC** dengan Ubuntu 20.04+ / 22.04+ / 24.04+
- RAM minimal: 2GB per laptop
- Storage: 10GB free space per laptop
- Network: WiFi/LAN yang sama (bisa saling ping)

### Software
- Ubuntu Desktop/Server (versi sama lebih baik)
- Koneksi internet untuk download package

---

## ⚠️ PENTING: Versi Harus Sama!

Sebelum install, **pastikan versi MariaDB dan Galera SAMA** di semua laptop!

### Kenapa Harus Sama?
- **MariaDB**: Versi berbeda bisa menyebabkan incompatibility fitur
- **Galera**: Versi berbeda bisa gagal membentuk cluster (error wsrep)

### Versi yang Direkomendasikan (Tested ✅)
- **MariaDB**: 10.11.x, 10.6.x, atau 11.x
- **Galera**: 26.4.x (misalnya 26.4.16, 26.4.18, 26.4.20)

---

## 🔍 STEP 0: Cek & Samakan Versi

**Lakukan di SEMUA 3 LAPTOP:**

### 0.1 Update Repository
```bash
sudo apt update
```

### 0.2 Cek Versi yang Tersedia
```bash
# Cek versi MariaDB
apt-cache policy mariadb-server

# Cek versi Galera
apt-cache policy galera-4
```

**Catat versi yang muncul!** Pastikan sama di semua laptop.

### 0.3 Jika Versi Berbeda Antar Laptop

**Opsi 1: Install versi yang sama dari repository default**
```bash
# Cek laptop mana yang punya versi paling rendah
# Install versi yang sama di semua laptop

sudo apt install mariadb-server=<versi> galera-4=<versi>
```

**Opsi 2: Gunakan MariaDB Official Repository (Recommended)**
```bash
# Di SEMUA 3 laptop, jalankan:
sudo apt install software-properties-common
curl -LsS https://r.mariadb.com/downloads/mariadb_repo_setup | sudo bash
sudo apt update
```

Lalu install:
```bash
sudo apt install mariadb-server galera-4
```

Ini akan install versi terbaru yang sama di semua laptop.

---

## 📝 STEP 1: Catat Informasi Network

**Sebelum mulai, catat IP dan hostname SEMUA 3 laptop.**

### 1.1 Di Laptop 1
```bash
# Cek IP
hostname -I | awk '{print $1}'

# Cek hostname
hostname
```

**Contoh output:**
- IP: `192.168.1.10`
- Hostname: `ubuntu-node1`

**CATAT sebagai:**
- IP_LAPTOP1 = `192.168.1.10`
- HOSTNAME_LAPTOP1 = `ubuntu-node1`

### 1.2 Di Laptop 2
```bash
hostname -I | awk '{print $1}'
hostname
```

**Contoh output:**
- IP: `192.168.1.11`
- Hostname: `ubuntu-node2`

**CATAT sebagai:**
- IP_LAPTOP2 = `192.168.1.11`
- HOSTNAME_LAPTOP2 = `ubuntu-node2`

### 1.3 Di Laptop 3
```bash
hostname -I | awk '{print $1}'
hostname
```

**Contoh output:**
- IP: `192.168.1.12`
- Hostname: `ubuntu-node3`

**CATAT sebagai:**
- IP_LAPTOP3 = `192.168.1.12`
- HOSTNAME_LAPTOP3 = `ubuntu-node3`

### 1.4 Test Koneksi Antar Laptop

**Dari Laptop 1:**
```bash
ping 192.168.1.11 -c 3  # Ping ke Laptop 2
ping 192.168.1.12 -c 3  # Ping ke Laptop 3
```

**Dari Laptop 2:**
```bash
ping 192.168.1.10 -c 3  # Ping ke Laptop 1
ping 192.168.1.12 -c 3  # Ping ke Laptop 3
```

**Dari Laptop 3:**
```bash
ping 192.168.1.10 -c 3  # Ping ke Laptop 1
ping 192.168.1.11 -c 3  # Ping ke Laptop 2
```

**Semua harus bisa ping!** ✅

Jika gagal:
- Cek apakah semua di jaringan WiFi/LAN yang sama
- Matikan firewall sementara untuk testing: `sudo ufw disable`

---

## 🔧 STEP 2: Install MariaDB & Galera (SEMUA LAPTOP)

**Lakukan di LAPTOP 1, 2, DAN 3:**

### 2.1 Install Package
```bash
sudo apt update
sudo apt install -y mariadb-server galera-4 rsync
```

### 2.2 Verifikasi Instalasi
```bash
# Cek versi MariaDB
mysql --version

# Cek versi Galera
dpkg -l | grep galera
```

**Output contoh:**
```
mysql  Ver 15.1 Distrib 10.11.8-MariaDB
galera-4       26.4.18-0ubuntu1
```

**PASTIKAN VERSI SAMA DI SEMUA 3 LAPTOP!**

### 2.3 Cek Path Library Galera
```bash
find /usr -name "*galera*.so" 2>/dev/null
```

**Output biasanya:**
```
/usr/lib/galera/libgalera_smm.so
```

**Catat path ini!** Akan dipakai di konfigurasi.

### 2.4 Stop MariaDB (Jangan Start Dulu!)
```bash
sudo systemctl stop mariadb
```

---

## ⚙️ STEP 3: Konfigurasi Galera

### 3.1 Di Laptop 1

```bash
sudo nano /etc/mysql/mariadb.conf.d/60-galera.cnf
```

**Paste konfigurasi ini** (GANTI IP dan hostname sesuai laptop kamu):

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
# GANTI dengan IP ketiga laptop kamu!
wsrep_cluster_address="gcomm://192.168.1.10,192.168.1.11,192.168.1.12"

# Galera Node Configuration - LAPTOP 1
# GANTI dengan IP laptop ini!
wsrep_node_address="192.168.1.10"
# GANTI dengan hostname laptop ini!
wsrep_node_name="ubuntu-node1"
wsrep_sst_method=rsync

# Performance
wsrep_slave_threads=4
```

**Simpan:** Ctrl+O → Enter → Ctrl+X

### 3.2 Di Laptop 2

```bash
sudo nano /etc/mysql/mariadb.conf.d/60-galera.cnf
```

**Paste konfigurasi ini** (GANTI IP dan hostname sesuai laptop kamu):

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
# GANTI dengan IP ketiga laptop kamu!
wsrep_cluster_address="gcomm://192.168.1.10,192.168.1.11,192.168.1.12"

# Galera Node Configuration - LAPTOP 2
# GANTI dengan IP laptop ini!
wsrep_node_address="192.168.1.11"
# GANTI dengan hostname laptop ini!
wsrep_node_name="ubuntu-node2"
wsrep_sst_method=rsync

# Performance
wsrep_slave_threads=4
```

**Simpan:** Ctrl+O → Enter → Ctrl+X

### 3.3 Di Laptop 3

```bash
sudo nano /etc/mysql/mariadb.conf.d/60-galera.cnf
```

**Paste konfigurasi ini** (GANTI IP dan hostname sesuai laptop kamu):

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
# GANTI dengan IP ketiga laptop kamu!
wsrep_cluster_address="gcomm://192.168.1.10,192.168.1.11,192.168.1.12"

# Galera Node Configuration - LAPTOP 3
# GANTI dengan IP laptop ini!
wsrep_node_address="192.168.1.12"
# GANTI dengan hostname laptop ini!
wsrep_node_name="ubuntu-node3"
wsrep_sst_method=rsync

# Performance
wsrep_slave_threads=4
```

**Simpan:** Ctrl+O → Enter → Ctrl+X

### 3.4 Perbedaan Konfigurasi Antar Laptop

**Yang SAMA di semua laptop:**
- `wsrep_cluster_name`
- `wsrep_cluster_address` (isi IP semua laptop)
- `wsrep_provider`

**Yang BEDA di setiap laptop:**
- `wsrep_node_address` (IP laptop itu sendiri)
- `wsrep_node_name` (hostname laptop itu sendiri)

---

## 🔓 STEP 4: Buka Firewall (SEMUA LAPTOP)

**Di LAPTOP 1, 2, DAN 3:**

```bash
# Cek status firewall
sudo ufw status

# Jika aktif, buka port yang dibutuhkan
sudo ufw allow 3306/tcp   # MySQL
sudo ufw allow 4567/tcp   # Galera Cluster replication
sudo ufw allow 4568/tcp   # IST (Incremental State Transfer)
sudo ufw allow 4444/tcp   # SST (State Snapshot Transfer)

# Jika mau install HAProxy nanti
sudo ufw allow 8404/tcp   # HAProxy Stats

# Reload firewall
sudo ufw reload
```

**Atau matikan firewall untuk testing:**
```bash
sudo ufw disable
```

---

## 🚀 STEP 5: Start Cluster

### 5.1 Bootstrap di Laptop 1 (Node Pertama)

**HANYA DI LAPTOP 1:**

```bash
sudo galera_new_cluster
```

#### Jika Error: "safe_to_bootstrap"
```bash
# Edit grastate.dat
sudo sed -i 's/safe_to_bootstrap: 0/safe_to_bootstrap: 1/' /var/lib/mysql/grastate.dat

# Coba lagi
sudo galera_new_cluster
```

### 5.2 Verifikasi di Laptop 1

```bash
# Cek status service
sudo systemctl status mariadb
```

Output harus: `active (running)` ✅

```bash
# Cek cluster size
sudo mysql -e "SHOW STATUS LIKE 'wsrep_cluster_size';"
```

Output harus:
```
+--------------------+-------+
| Variable_name      | Value |
+--------------------+-------+
| wsrep_cluster_size | 1     |  <-- Baru Laptop 1 yang aktif
+--------------------+-------+
```

### 5.3 Start MariaDB di Laptop 2

**DI LAPTOP 2:**

```bash
sudo systemctl start mariadb
```

**Cek status:**
```bash
sudo systemctl status mariadb
sudo mysql -e "SHOW STATUS LIKE 'wsrep_cluster_size';"
```

Output harus:
```
wsrep_cluster_size | 2
```

### 5.4 Start MariaDB di Laptop 3

**DI LAPTOP 3:**

```bash
sudo systemctl start mariadb
```

**Cek status:**
```bash
sudo systemctl status mariadb
sudo mysql -e "SHOW STATUS LIKE 'wsrep_cluster_size';"
```

Output harus:
```
wsrep_cluster_size | 3  <-- SEMUA NODE SUDAH TERHUBUNG!
```

### 5.5 Verifikasi Final (Di Laptop Mana Saja)

```bash
sudo mysql -e "SHOW STATUS LIKE 'wsrep%';" | grep -E "(cluster_size|local_state_comment|ready|incoming_addresses)"
```

Output yang benar:
```
wsrep_cluster_size              | 3
wsrep_local_state_comment       | Synced
wsrep_ready                     | ON
wsrep_incoming_addresses        | 192.168.1.10:3306,192.168.1.11:3306,192.168.1.12:3306
```

🎉 **CLUSTER 3 NODES BERHASIL!**

---

## 🔐 STEP 6: Setup Database & User

**Jalankan HANYA DI 1 LAPTOP** (data akan sync otomatis ke semua laptop).

### 6.1 Login ke MySQL

```bash
sudo mysql -u root
```

### 6.2 Set Password & Create User

```sql
-- Set password root
ALTER USER 'root'@'localhost' IDENTIFIED BY '030105';

-- Create remote root (agar bisa diakses dari laptop lain)
CREATE USER 'root'@'%' IDENTIFIED BY '030105';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;

FLUSH PRIVILEGES;
```

### 6.3 Create Database & Table

```sql
-- Create database
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

-- User untuk HAProxy health check
CREATE USER 'haproxy_check'@'%';
FLUSH PRIVILEGES;

-- Exit
EXIT;
```

### 6.4 Test Replication

**Di Laptop 1:**
```bash
mysql -uroot -p030105 beauty -e "INSERT INTO products (name, price, stock) VALUES ('Produk Laptop 1', 100000, 10);"
```

**Di Laptop 2:**
```bash
mysql -uroot -p030105 beauty -e "SELECT * FROM products;"
```

**Di Laptop 3:**
```bash
mysql -uroot -p030105 beauty -e "SELECT * FROM products;"
```

**Semua harus muncul data yang sama!** ✅

**Test insert dari laptop berbeda:**
```bash
# Di Laptop 2
mysql -uroot -p030105 beauty -e "INSERT INTO products (name, price, stock) VALUES ('Produk Laptop 2', 50000, 5);"

# Di Laptop 3
mysql -uroot -p030105 beauty -e "INSERT INTO products (name, price, stock) VALUES ('Produk Laptop 3', 75000, 8);"

# Cek di Laptop 1
mysql -uroot -p030105 beauty -e "SELECT * FROM products;"
```

Harus ada **3 produk** dari ketiga laptop! ✅

---

## 🔀 STEP 7: Setup HAProxy Load Balancer

Pilih **1 laptop** untuk install HAProxy (biasanya yang paling powerful).  
**Untuk tutorial ini, kita install di Laptop 1.**

### 7.1 Install HAProxy (di Laptop 1)

```bash
sudo apt install -y haproxy
```

### 7.2 Backup Konfigurasi Original

```bash
sudo cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.backup
```

### 7.3 Buat Konfigurasi HAProxy

```bash
sudo nano /etc/haproxy/haproxy.cfg
```

**HAPUS SEMUA ISI** dan paste ini (GANTI IP sesuai laptop kamu):

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

# MySQL/MariaDB Load Balancer (3 Nodes)
listen mysql-cluster
    bind *:3306
    mode tcp
    balance roundrobin
    option mysql-check user haproxy_check
    
    # GANTI IP dengan IP ketiga laptop kamu!
    server node1 192.168.1.10:3306 check weight 1
    server node2 192.168.1.11:3306 check weight 1
    server node3 192.168.1.12:3306 check weight 1
```

**Simpan:** Ctrl+O → Enter → Ctrl+X

### 7.4 Restart HAProxy

```bash
sudo systemctl restart haproxy
sudo systemctl enable haproxy
sudo systemctl status haproxy
```

Output harus: `active (running)` ✅

### 7.5 Verifikasi HAProxy

```bash
# Cek port 3306 (HAProxy MySQL) dan 8404 (stats)
sudo ss -tlnp | grep -E "(3306|8404)"
```

Output:
```
LISTEN ... 0.0.0.0:3306 ... haproxy
LISTEN ... 0.0.0.0:8404 ... haproxy
```

### 7.6 Test Load Balancing

```bash
# Di Laptop 1
for i in {1..15}; do
  mysql -h 127.0.0.1 -P 3306 -uroot -p030105 -e "SELECT @@hostname;" 2>/dev/null | grep -v hostname
done
```

**Output harus bergantian:**
```
ubuntu-node1
ubuntu-node2
ubuntu-node3
ubuntu-node1
ubuntu-node2
ubuntu-node3
...
```

✅ **Load Balancing Berhasil!**

### 7.7 Akses HAProxy Stats Page

Buka browser di laptop manapun:
```
http://192.168.1.10:8404/stats
```

**Login:**
- Username: `admin`
- Password: `admin123`

Akan muncul dashboard dengan:
- **Backend:** mysql-cluster
- **Servers:** node1 (UP/GREEN), node2 (UP/GREEN), node3 (UP/GREEN)

---

## 🐍 STEP 8: Setup Aplikasi Flask

### 8.1 Install Dependencies (SEMUA LAPTOP)

**Di Laptop 1, 2, dan 3:**

```bash
sudo apt install -y python3 python3-pip git
pip3 install flask mysql-connector-python
```

### 8.2 Clone/Copy Project

Jika sudah ada project di GitHub:
```bash
cd ~
git clone https://github.com/username/galera-cluster.git
cd galera-cluster
```

Atau copy folder project ke semua laptop.

### 8.3 Edit Konfigurasi Database

Edit file `app.py`:
```bash
nano app.py
```

Cari bagian `DB_CONFIG` dan ubah:
```python
DB_CONFIG = {
    'host': '192.168.1.10',  # IP Laptop 1 (HAProxy)
    'port': 3306,             # Port HAProxy
    'user': 'root',
    'password': '030105',
    'database': 'beauty'
}
```

**Simpan:** Ctrl+O → Enter → Ctrl+X

### 8.4 Run Aplikasi di SEMUA Laptop

**Di Laptop 1:**
```bash
python3 app.py
```

**Di Laptop 2 (terminal baru):**
```bash
python3 app.py
```

**Di Laptop 3 (terminal baru):**
```bash
python3 app.py
```

Output di semua laptop:
```
 * Running on http://0.0.0.0:5000
```

### 8.5 Akses Aplikasi

Buka browser:
- Dari Laptop 1: `http://localhost:5000` atau `http://192.168.1.10:5000`
- Dari Laptop 2: `http://localhost:5000` atau `http://192.168.1.11:5000`
- Dari Laptop 3: `http://localhost:5000` atau `http://192.168.1.12:5000`

Atau akses dari laptop lain ke IP tertentu.

**Fitur yang bisa ditest:**
- Badge "Current Node" harus berganti: **node1** ↔ **node2** ↔ **node3**
- Insert produk dari Laptop 1 → muncul di browser Laptop 2 & 3
- Real-time update (jika ada auto-refresh)

---

## ✅ STEP 9: Testing & Verification

### Test 1: Cluster Status

**Di semua laptop:**
```bash
mysql -uroot -p030105 -e "
SHOW STATUS LIKE 'wsrep_cluster_size';
SHOW STATUS LIKE 'wsrep_local_state_comment';
SHOW STATUS LIKE 'wsrep_ready';
"
```

Output yang benar:
```
wsrep_cluster_size           | 3
wsrep_local_state_comment    | Synced
wsrep_ready                  | ON
```

### Test 2: Load Balancing

```bash
# Di Laptop 1 (via HAProxy)
for i in {1..20}; do
  mysql -h 192.168.1.10 -P 3306 -uroot -p030105 -e "SELECT @@hostname;" 2>/dev/null | grep -v hostname
done
```

Harus ada **node1**, **node2**, dan **node3** bergantian.

### Test 3: Data Replication

```bash
# Insert di Laptop 1
mysql -h 192.168.1.10 -P 3306 -uroot -p030105 beauty -e "INSERT INTO products (name, price, stock) VALUES ('Test Replication', 200000, 20);"

# Cek langsung di Laptop 2 (tanpa HAProxy)
mysql -h 192.168.1.11 -P 3306 -uroot -p030105 beauty -e "SELECT * FROM products WHERE name='Test Replication';"

# Cek langsung di Laptop 3
mysql -h 192.168.1.12 -P 3306 -uroot -p030105 beauty -e "SELECT * FROM products WHERE name='Test Replication';"
```

Data harus sama di semua laptop!

### Test 4: High Availability

**Matikan 1 node:**
```bash
# Di Laptop 3
sudo systemctl stop mariadb
```

**Cek cluster size di Laptop 1 atau 2:**
```bash
mysql -uroot -p030105 -e "SHOW STATUS LIKE 'wsrep_cluster_size';"
```

Harus: `wsrep_cluster_size | 2` (tinggal 2 node)

**Test aplikasi:**
```bash
# Insert produk baru
mysql -h 192.168.1.10 -P 3306 -uroot -p030105 beauty -e "INSERT INTO products (name, price, stock) VALUES ('Test HA', 99000, 9);"
```

Aplikasi **MASIH JALAN** karena masih ada 2 node UP! ✅

**Cek HAProxy Stats:**
- node1: **UP (GREEN)**
- node2: **UP (GREEN)**
- node3: **DOWN (RED)**

**Nyalakan kembali Laptop 3:**
```bash
# Di Laptop 3
sudo systemctl start mariadb
```

Tunggu 5-10 detik, Laptop 3 akan **rejoin cluster** otomatis.

**Cek cluster size lagi:**
```bash
mysql -uroot -p030105 -e "SHOW STATUS LIKE 'wsrep_cluster_size';"
```

Harus kembali: `wsrep_cluster_size | 3` ✅

**Cek data di Laptop 3:**
```bash
# Di Laptop 3
mysql -uroot -p030105 beauty -e "SELECT * FROM products WHERE name='Test HA';"
```

Data yang diinsert saat node3 mati **SUDAH ADA** karena auto-sync! ✅

### Test 5: Multi-Node Failure

**Matikan 2 node sekaligus:**
```bash
# Di Laptop 2
sudo systemctl stop mariadb

# Di Laptop 3
sudo systemctl stop mariadb
```

**Sistem masih jalan dari Laptop 1:**
```bash
mysql -h 192.168.1.10 -P 3306 -uroot -p030105 -e "SELECT 1;"
```

**Nyalakan kembali:**
```bash
# Di Laptop 2
sudo systemctl start mariadb

# Di Laptop 3
sudo systemctl start mariadb
```

Semua rejoin otomatis! ✅

---

## 🔥 Troubleshooting

### Problem 1: Cluster Size Tetap 1 (Tidak Terhubung)

**Gejala:**
- Setelah start Laptop 2 & 3, cluster size masih 1

**Solusi:**

#### A. Cek Firewall
```bash
sudo ufw status
```

Pastikan port 3306, 4567, 4568, 4444 terbuka.

Atau matikan firewall:
```bash
sudo ufw disable
```

#### B. Test Koneksi
```bash
# Dari Laptop 1
telnet 192.168.1.11 3306
telnet 192.168.1.12 3306
```

Harus bisa konek.

#### C. Cek Log Error
```bash
sudo tail -50 /var/log/mysql/error.log | grep -i error
```

Cari error tentang `wsrep`, `gcomm`, atau `SST`.

#### D. Restart Cluster
```bash
# Stop di SEMUA laptop
sudo systemctl stop mariadb

# Bootstrap di Laptop 1
sudo galera_new_cluster

# Start di Laptop 2
sudo systemctl start mariadb

# Start di Laptop 3
sudo systemctl start mariadb
```

---

### Problem 2: Error "wsrep_provider: No such file"

**Gejala:**
```
ERROR WSREP: /usr/lib/galera/libgalera_smm.so: cannot open shared object file
```

**Solusi:**

Cari path library yang benar:
```bash
find /usr -name "*galera*.so" 2>/dev/null
```

Edit konfigurasi:
```bash
sudo nano /etc/mysql/mariadb.conf.d/60-galera.cnf
```

Ubah baris `wsrep_provider=` dengan path yang benar.

---

### Problem 3: Node Tidak Bisa Rejoin Setelah Restart

**Gejala:**
- Setelah restart laptop, MariaDB tidak bisa start
- Error: "It may not be safe to bootstrap"

**Solusi:**

```bash
# Di laptop yang bermasalah
sudo systemctl stop mariadb

# Hapus grastate.dat
sudo rm /var/lib/mysql/grastate.dat

# Start mariadb (akan rejoin cluster)
sudo systemctl start mariadb
```

---

### Problem 4: HAProxy Menunjukkan Node DOWN

**Gejala:**
- HAProxy stats page menunjukkan node merah (DOWN)
- Padahal MariaDB running

**Solusi:**

#### A. Test Manual
```bash
mysql -h 192.168.1.10 -P 3306 -uroot -p030105 -e "SELECT 1;"
mysql -h 192.168.1.11 -P 3306 -uroot -p030105 -e "SELECT 1;"
mysql -h 192.168.1.12 -P 3306 -uroot -p030105 -e "SELECT 1;"
```

Jika error, cek MariaDB running dan firewall.

#### B. Cek User haproxy_check
```bash
mysql -uroot -p030105 -e "SELECT User, Host FROM mysql.user WHERE User='haproxy_check';"
```

Harus ada. Jika tidak:
```sql
CREATE USER 'haproxy_check'@'%';
FLUSH PRIVILEGES;
```

#### C. Restart HAProxy
```bash
sudo systemctl restart haproxy
```

---

## 📊 Command Cheat Sheet

### Cluster Management
```bash
# Cek cluster size
mysql -uroot -p030105 -e "SHOW STATUS LIKE 'wsrep_cluster_size';"

# Cek status detail
mysql -uroot -p030105 -e "SHOW STATUS LIKE 'wsrep%';" | grep -E "(cluster_size|state_comment|ready)"

# Cek semua node di cluster
mysql -uroot -p030105 -e "SHOW STATUS LIKE 'wsrep_incoming_addresses';"
```

### Data Management
```bash
# View semua produk
mysql -uroot -p030105 beauty -e "SELECT * FROM products;"

# Insert data
mysql -uroot -p030105 beauty -e "INSERT INTO products (name, price, stock) VALUES ('Produk Baru', 150000, 15);"

# Delete data
mysql -uroot -p030105 beauty -e "DELETE FROM products WHERE id=1;"

# Truncate table (hapus semua data)
mysql -uroot -p030105 beauty -e "TRUNCATE TABLE products;"
```

### Service Management
```bash
# Restart MariaDB
sudo systemctl restart mariadb

# Restart HAProxy
sudo systemctl restart haproxy

# Cek status
sudo systemctl status mariadb
sudo systemctl status haproxy

# Enable auto-start
sudo systemctl enable mariadb
sudo systemctl enable haproxy
```

### Monitoring
```bash
# Monitor MariaDB logs
sudo tail -f /var/log/mysql/error.log

# Monitor HAProxy logs
sudo journalctl -u haproxy -f

# Monitor real-time connections
watch -n 1 'mysql -uroot -p030105 -e "SHOW STATUS LIKE \"wsrep_cluster_size\"; SHOW STATUS LIKE \"Threads_connected\";"'
```

---

## 🎯 Checklist Sebelum Demo

- [ ] Semua 3 laptop bisa saling ping
- [ ] Versi MariaDB sama di semua laptop
- [ ] Versi Galera sama di semua laptop
- [ ] `wsrep_cluster_size` = 3 di semua laptop
- [ ] Database `beauty` dan table `products` ada
- [ ] Test insert di Laptop 1 → muncul di Laptop 2 & 3
- [ ] Test insert di Laptop 2 → muncul di Laptop 1 & 3
- [ ] Test insert di Laptop 3 → muncul di Laptop 1 & 2
- [ ] HAProxy running dan port 3306 terbuka
- [ ] HAProxy stats page bisa diakses (http://IP:8404/stats)
- [ ] Test load balancing: hostname berganti node1 ↔ node2 ↔ node3
- [ ] Aplikasi Flask running di semua laptop
- [ ] Test HA: matikan 1 laptop → aplikasi tetap jalan
- [ ] Test rejoin: nyalakan laptop → otomatis join cluster
- [ ] Test HA ekstrem: matikan 2 laptop → 1 laptop masih jalan

---

## 🚀 Demo Script (Untuk Presentasi)

### 1. Opening (2 menit)
- Tunjukkan 3 laptop dengan IP berbeda
- Tunjukkan `hostname` di setiap laptop
- Buka HAProxy stats → tunjukkan 3 nodes UP (hijau)
- Jelaskan arsitektur: 3 nodes + HAProxy load balancer

### 2. Demo Cluster Status (2 menit)
```bash
# Di terminal, tunjukkan
mysql -uroot -p030105 -e "SHOW STATUS LIKE 'wsrep_cluster_size';"
mysql -uroot -p030105 -e "SHOW STATUS LIKE 'wsrep_incoming_addresses';"
```
- Tunjukkan cluster size = 3
- Tunjukkan semua IP node aktif

### 3. Demo Load Balancing (3 menit)
- Buka aplikasi Flask di browser
- Refresh 10-15 kali
- Tunjukkan badge "Current Node" berganti: **node1** → **node2** → **node3**
- Buka HAProxy stats → tunjukkan distribusi session
- Jelaskan: Request didistribusikan secara merata

### 4. Demo Replication (3 menit)
- Insert produk "Lipstick Red" dari aplikasi
- Buka terminal di Laptop 2
- Query: `SELECT * FROM products WHERE name='Lipstick Red';`
- **Data muncul!**
- Buka terminal di Laptop 3
- Query yang sama
- **Data sama persis!**
- Jelaskan: Multi-Master Replication - semua node bisa read & write

### 5. Demo High Availability (5 menit)
- Insert produk "Foundation Glow" (catat ID-nya)
- **Matikan Laptop 3** (shutdown atau `sudo systemctl stop mariadb`)
- Refresh HAProxy stats → node3 merah (DOWN), node1 & node2 hijau (UP)
- **Aplikasi masih bisa diakses!**
- Insert produk "Mascara Black" dari aplikasi
- Tunjukkan data tersimpan
- **Nyalakan kembali Laptop 3**
- Tunggu 10-15 detik
- Refresh HAProxy stats → node3 hijau lagi (UP)
- Query di Laptop 3: `SELECT * FROM products WHERE name='Mascara Black';`
- **Data yang diinsert saat node3 mati SUDAH ADA!**
- Jelaskan: Auto-sync saat node rejoin

### 6. Demo Extreme HA (3 menit - BONUS)
- **Matikan 2 laptop sekaligus** (Laptop 2 & 3)
- HAProxy stats → 2 node merah, 1 hijau
- **Aplikasi masih bisa insert data dari node1!**
- Insert produk "Serum Vitamin C"
- Nyalakan Laptop 2 & 3
- Cek data di Laptop 2 & 3 → data ada!
- Jelaskan: Cluster masih jalan selama ada 1 node aktif (quorum)

### 7. Closing (2 menit)
- Tunjukkan semua checklist sudah ✅
- Jelaskan benefit:
  - **Load Balancing**: Performance meningkat 3x
  - **High Availability**: 99.9% uptime, zero downtime
  - **Auto-Sync**: Data konsisten di semua node
  - **Fault Tolerance**: Tahan jika 2 dari 3 node mati
- Q&A

**Total waktu: ~20 menit**

---

## 📚 Referensi

- [MariaDB Galera Cluster Documentation](https://mariadb.com/kb/en/galera-cluster/)
- [HAProxy Documentation](http://www.haproxy.org/)
- [Galera Cluster Configuration Guide](https://galeracluster.com/library/documentation/)
- [Ubuntu Server Guide - MariaDB](https://ubuntu.com/server/docs/databases-mariadb)

---

## 💡 Tips & Best Practices

### 1. Backup Sebelum Demo
```bash
# Backup database
mysqldump -uroot -p030105 beauty > backup_beauty.sql

# Restore jika perlu
mysql -uroot -p030105 beauty < backup_beauty.sql
```

### 2. Auto-start Services
```bash
sudo systemctl enable mariadb
sudo systemctl enable haproxy
```

### 3. Monitoring Real-time
```bash
# Terminal 1: Monitor cluster
watch -n 2 'mysql -uroot -p030105 -e "SHOW STATUS LIKE \"wsrep_cluster_size\";"'

# Terminal 2: Monitor HAProxy
sudo journalctl -u haproxy -f
```

### 4. Cleanup Data (Untuk Testing)
```bash
mysql -uroot -p030105 beauty -e "TRUNCATE TABLE products;"
```

### 5. Reset Cluster (Jika Perlu)
```bash
# Stop di semua node
sudo systemctl stop mariadb

# Di SEMUA node, hapus grastate
sudo rm /var/lib/mysql/grastate.dat

# Bootstrap di Laptop 1
sudo galera_new_cluster

# Start di Laptop 2 & 3
sudo systemctl start mariadb
```

### 6. Performance Tuning
Edit `/etc/mysql/mariadb.conf.d/60-galera.cnf`:
```ini
# Tambahkan untuk performance lebih baik
innodb_buffer_pool_size=512M
innodb_log_file_size=128M
max_connections=200
wsrep_slave_threads=8  # 2x jumlah CPU core
```

### 7. Security Checklist
- [ ] Ganti password default
- [ ] Ganti password HAProxy stats (admin:admin123)
- [ ] Aktifkan firewall di production
- [ ] Batasi akses remote hanya dari IP tertentu
- [ ] Gunakan SSL/TLS untuk koneksi database

---

## 🎓 Penjelasan untuk Dosen/Penguji

### Teknologi yang Digunakan

1. **MariaDB Galera Cluster**
   - Multi-master replication
   - Synchronous replication (data consistency)
   - Automatic node provisioning
   - Write-anywhere, read-anywhere

2. **HAProxy**
   - Layer 4 (TCP) load balancing
   - Health checking
   - Round-robin distribution
   - High availability proxy

3. **Flask + Python**
   - Lightweight web framework
   - Database integration
   - Real-time data display

### Konsep Distributed Systems yang Diterapkan

1. **Replication** ✅
   - Multi-master replication
   - Synchronous data sync
   - Conflict resolution via certification

2. **Consistency** ✅
   - Strong consistency (tidak eventual)
   - ACID compliance
   - No data loss

3. **Availability** ✅
   - High availability (99.9%+)
   - Fault tolerance
   - Auto-recovery

4. **Partition Tolerance** ✅
   - Quorum-based
   - Split-brain prevention
   - Auto-rejoin setelah network partition

5. **Load Balancing** ✅
   - Request distribution
   - Resource optimization
   - Horizontal scaling

### Kelebihan Arsitektur Ini

✅ **Zero Downtime**: Maintenance tanpa henti layanan  
✅ **Scalability**: Horizontal scaling dengan tambah node  
✅ **Performance**: 3x throughput vs single server  
✅ **Consistency**: Data sama di semua node  
✅ **Reliability**: Tahan 2 dari 3 node mati  

---

**Dibuat dengan ❤️ untuk Final Project Distributed Systems**

**Good luck untuk demo & presentasi! Semoga nilai A!** 🎓🚀
