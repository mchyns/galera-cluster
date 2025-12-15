# Beauty Products - Distributed Database System

Project Sistem Terdistribusi menggunakan MariaDB Galera Cluster + HAProxy Load Balancer.

## 📋 Arsitektur

```
┌─────────────────┐
│  Flask App      │ ──┐
│  (Port 5000)    │   │
└─────────────────┘   │
                      │ Connect to 127.0.0.1:3300
                      ▼
              ┌───────────────┐
              │   HAProxy     │
              │  (Port 3300)  │
              └───────────────┘
                 /      |      \
                /       |       \
               /        |        \
    ┌─────────┐  ┌─────────┐  ┌─────────┐
    │ MariaDB │  │ MariaDB │  │ MariaDB │
    │  Node 1 │  │  Node 2 │  │  Node 3 │
    └─────────┘  └─────────┘  └─────────┘
         Galera Cluster (Multi-Master)
```

## 🚀 Phase 1: Development dengan Docker

### Prerequisites
- Docker & Docker Compose installed
- Python 3.8+ installed
- Port 3300 dan 5000 tersedia

### Langkah-langkah:

#### 1. Install Dependencies Python
```bash
pip install -r requirements.txt
```

#### 2. Start Docker Cluster
```bash
docker compose up -d
```

Tunggu ~30 detik hingga cluster terbentuk. Check status:
```bash
docker compose ps
```

#### 3. Verify Cluster Status
```bash
# Check HAProxy stats page
curl http://localhost:8404/stats

# Check cluster size (should show 3)
docker exec mariadb-node1 mysql -uroot -p030105 -e "SHOW STATUS LIKE 'wsrep_cluster_size';"
```

#### 4. Run Flask App
```bash
python app.py
```

Akses: http://localhost:5000

#### 5. Test Load Balancing
Refresh halaman beberapa kali dan perhatikan badge "Current Node" - akan berganti antara mariadb-node1, node2, dan node3.

### Troubleshooting Docker

**Jika cluster tidak terbentuk:**
```bash
# Reset semua
docker compose down -v
docker compose up -d

# Check logs
docker compose logs mariadb-node1
```

## 🖥️ Phase 2: Production pada 3 Laptop Fisik

### Setup pada SETIAP Laptop:

#### 1. Install MariaDB Server
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mariadb-server mariadb-backup

# Enable Galera
sudo apt install galera-4 galera-arbitrator-4
```

#### 2. Configure Galera Cluster

Edit `/etc/mysql/mariadb.conf.d/60-galera.cnf`:

**Laptop 1 (IP: 192.168.1.10):**
```ini
[mysqld]
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

# Galera Node Configuration
wsrep_node_address="192.168.1.10"
wsrep_node_name="node1"
wsrep_sst_method=rsync
```

**Laptop 2 & 3:** Sama seperti di atas, tapi ganti:
- `wsrep_node_address` sesuai IP masing-masing
- `wsrep_node_name` ke "node2" atau "node3"

#### 3. Initialize Cluster

**Hanya pada Laptop 1 (bootstrap node):**
```bash
sudo galera_new_cluster
```

**Pada Laptop 2 & 3:**
```bash
sudo systemctl start mariadb
```

#### 4. Setup Database & User

**Pada salah satu laptop (akan sync otomatis):**
```bash
sudo mysql -u root

# Set root password
ALTER USER 'root'@'localhost' IDENTIFIED BY '030105';

# Create remote root
CREATE USER 'root'@'%' IDENTIFIED BY '030105';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;

# Create database
CREATE DATABASE beauty;

# Create HAProxy health check user
CREATE USER 'haproxy_check'@'%';

FLUSH PRIVILEGES;
EXIT;
```

#### 5. Verify Cluster

Pada setiap laptop:
```bash
mysql -uroot -p030105 -e "SHOW STATUS LIKE 'wsrep_cluster_size';"
# Output should be: wsrep_cluster_size | 3
```

### Setup HAProxy (Pilih 1 Laptop atau Laptop Terpisah)

#### 1. Install HAProxy
```bash
sudo apt install haproxy
```

#### 2. Configure HAProxy
```bash
sudo cp haproxy_physical_template.cfg /etc/haproxy/haproxy.cfg
sudo nano /etc/haproxy/haproxy.cfg
```

**Ganti IP addresses dengan IP real laptops:**
```
server node1 192.168.1.10:3306 check weight 1
server node2 192.168.1.11:3306 check weight 1
server node3 192.168.1.12:3306 check weight 1
```

#### 3. Restart HAProxy
```bash
sudo systemctl restart haproxy
sudo systemctl status haproxy
```

### Setup Python App

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Run App
```bash
python app.py
```

**PENTING:** Jika HAProxy berjalan di laptop berbeda, update `app.py`:
```python
DB_CONFIG = {
    'host': '192.168.1.X',  # IP laptop yang running HAProxy
    'port': 3306,
    ...
}
```

## 🧪 Testing

### Test 1: Load Balancing
1. Buka aplikasi di browser
2. Refresh halaman beberapa kali
3. Perhatikan badge "Current Node" - harus berganti-ganti

### Test 2: High Availability
1. Tambahkan produk
2. Stop salah satu MariaDB node:
   ```bash
   # Docker:
   docker stop mariadb-node2
   
   # Physical:
   sudo systemctl stop mariadb
   ```
3. Aplikasi tetap berjalan
4. Data tetap accessible

### Test 3: Data Replication
1. Insert data dari aplikasi
2. Check di semua node:
   ```bash
   mysql -uroot -p030105 beauty -e "SELECT * FROM products;"
   ```
3. Data harus sama di semua node

## 📊 Monitoring

### HAProxy Stats Page
- Docker: http://localhost:8404/stats
- Physical: http://<haproxy-ip>:8404/stats
- Username: `admin`
- Password: `admin123`

### Check Cluster Status
```bash
mysql -uroot -p030105 -e "SHOW STATUS LIKE 'wsrep_%';"
```

Key metrics:
- `wsrep_cluster_size`: Jumlah node aktif (harus 3)
- `wsrep_local_state_comment`: Status node (harus "Synced")
- `wsrep_ready`: ON/OFF

## 🎯 Key Features

✅ Multi-Master Replication (Galera)
✅ Load Balancing (HAProxy Round Robin)
✅ High Availability (Node failure tolerance)
✅ Real-time Node Information Display
✅ **Real-time Data Sync** (Auto-refresh setiap 3 detik)
✅ **Multi-Client Support** (Bisa running di 3 laptop sekaligus)
✅ Clean & Professional UI
✅ Same codebase untuk Docker & Physical

## 📝 Database Schema

```sql
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔒 Security Notes (Production)

1. Ganti `app.secret_key` di `app.py`
2. Ganti password HAProxy stats (`admin:admin123`)
3. Setup firewall untuk port MariaDB (3306)
4. Gunakan SSL/TLS untuk HAProxy
5. Restrict remote access ke database

## 🆘 Common Issues

### Cluster tidak terbentuk
- Check firewall: Port 3306, 4567, 4568, 4444 harus open
- Verify IP addresses di config file
- Check logs: `journalctl -u mariadb -f`

### HAProxy tidak konek ke nodes
- Pastikan user `haproxy_check` exists
- Test manual: `mysql -h <node-ip> -uroot -p030105`
- Check HAProxy logs: `sudo tail -f /var/log/haproxy.log`

### App tidak konek ke database
- Verify HAProxy running: `sudo systemctl status haproxy`
- Check port 3300 listening: `sudo netstat -tlnp | grep 3300`
- Test connection: `mysql -h 127.0.0.1 -P 3300 -uroot -p030105`

## 👨‍💻 Tech Stack

- **Backend:** Python Flask
- **Database:** MariaDB 10.11 + Galera Cluster
- **Load Balancer:** HAProxy 2.8
- **Frontend:** Bootstrap 5 + Bootstrap Icons
- **Containerization:** Docker & Docker Compose

---

**Good luck dengan demo project-nya! 🚀**
