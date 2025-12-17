# Setup Galera Cluster 2 Nodes (Fedora + Ubuntu)

## 📋 Info Laptop
- **Laptop 1 (Fedora)**: 192.168.100.120
- **Laptop 2 (Ubuntu)**: 192.168.100.116

---

## 🔧 STEP 1: Setup di Laptop Fedora (192.168.100.120)

### 1.1 Install MariaDB + Galera
```bash
sudo dnf install -y mariadb-server galera rsync
```

### 1.2 Cek path library Galera
```bash
find /usr -name "*galera*.so" 2>/dev/null
# Harusnya: /usr/lib64/galera-4/libgalera_smm.so
```

### 1.3 Copy konfigurasi Galera
```bash
sudo cp galera_fedora.cnf /etc/my.cnf.d/galera.cnf
```

Atau buat manual:
```bash
sudo nano /etc/my.cnf.d/galera.cnf
```

Paste isi dari file `galera_fedora.cnf`

### 1.4 Stop MariaDB dulu
```bash
sudo systemctl stop mariadb
```

### 1.5 Open Firewall
```bash
sudo firewall-cmd --permanent --add-port=3306/tcp
sudo firewall-cmd --permanent --add-port=4567/tcp
sudo firewall-cmd --permanent --add-port=4568/tcp
sudo firewall-cmd --permanent --add-port=4444/tcp
sudo firewall-cmd --permanent --add-port=8404/tcp
sudo firewall-cmd --reload
```

---

## 🔧 STEP 2: Setup di Laptop Ubuntu (192.168.100.116)

### 2.1 Install MariaDB + Galera
```bash
sudo apt update
sudo apt install -y mariadb-server galera-4 rsync
```

### 2.2 Copy konfigurasi Galera
```bash
sudo nano /etc/mysql/mariadb.conf.d/60-galera.cnf
```

Paste isi dari file `galera_ubuntu.cnf`

### 2.3 Stop MariaDB dulu
```bash
sudo systemctl stop mariadb
```

### 2.4 Open Firewall (jika aktif)
```bash
sudo ufw allow 3306/tcp
sudo ufw allow 4567/tcp
sudo ufw allow 4568/tcp
sudo ufw allow 4444/tcp
```

---

## 🚀 STEP 3: Start Cluster

### 3.1 Bootstrap di Fedora (Node Pertama)
```bash
sudo galera_new_cluster
```

### 3.2 Cek status di Fedora
```bash
sudo systemctl status mariadb
sudo mysql -e "SHOW STATUS LIKE 'wsrep_cluster_size';"
```

Harus keluar: `wsrep_cluster_size | 1`

### 3.3 Start MariaDB di Ubuntu
```bash
sudo systemctl start mariadb
sudo systemctl status mariadb
```

### 3.4 Verify Cluster (di Fedora atau Ubuntu)
```bash
sudo mysql -e "SHOW STATUS LIKE 'wsrep_cluster_size';"
```

Harus keluar: `wsrep_cluster_size | 2` ✅

### 3.5 Cek semua node
```bash
sudo mysql -e "SHOW STATUS LIKE 'wsrep%';" | grep -E "(cluster_size|local_state_comment|ready|node_name)"
```

Output:
```
wsrep_cluster_size           | 2
wsrep_local_state_comment    | Synced
wsrep_ready                  | ON
```

---

## 🔐 STEP 4: Setup Database (Jalankan di 1 laptop saja)

### Di Fedora atau Ubuntu:
```bash
sudo mysql -u root
```

```sql
-- Set password root
ALTER USER 'root'@'localhost' IDENTIFIED BY '030105';
CREATE USER 'root'@'%' IDENTIFIED BY '030105';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;

-- Create database
CREATE DATABASE beauty;
USE beauty;

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

EXIT;
```

### Test replication
```bash
# Di Fedora
mysql -uroot -p030105 beauty -e "INSERT INTO products (name, price, stock) VALUES ('Test Fedora', 100000, 10);"

# Di Ubuntu
mysql -uroot -p030105 beauty -e "SELECT * FROM products;"
```

Data harus muncul di Ubuntu! ✅

---

## 🔀 STEP 5: Setup HAProxy (di Fedora)

### 5.1 Install HAProxy
```bash
sudo dnf install -y haproxy
```

### 5.2 Backup config original
```bash
sudo cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.backup
```

### 5.3 Copy config baru
```bash
sudo cp haproxy_2nodes.cfg /etc/haproxy/haproxy.cfg
```

Atau edit manual:
```bash
sudo nano /etc/haproxy/haproxy.cfg
```

Paste isi dari file `haproxy_2nodes.cfg`

### 5.4 Set SELinux (Fedora)
```bash
sudo setsebool -P haproxy_connect_any 1
```

### 5.5 Restart HAProxy
```bash
sudo systemctl restart haproxy
sudo systemctl enable haproxy
sudo systemctl status haproxy
```

### 5.6 Test HAProxy
```bash
# Cek port 3307 (HAProxy MySQL)
sudo ss -tlnp | grep 3307

# Test koneksi
for i in {1..5}; do
  mysql -h 127.0.0.1 -P 3307 -uroot -p030105 -e "SELECT @@hostname;" 2>/dev/null | grep -v hostname
done
```

Output harus berganti: `fedora`, `ubuntu` ✅

### 5.7 Akses HAProxy Stats
Buka browser:
```
http://192.168.100.120:8404/stats
Username: admin
Password: admin123
```

---

## ✅ Verification

### Test dari Fedora
```bash
# Konek via HAProxy (port 3307)
mysql -h 192.168.100.120 -P 3307 -uroot -p030105 -e "SELECT @@hostname;"

# Refresh beberapa kali, harus berganti fedora/ubuntu
```

### Test dari Ubuntu
```bash
# Konek ke HAProxy di Fedora
mysql -h 192.168.100.120 -P 3307 -uroot -p030105 beauty -e "SELECT * FROM products;"
```

### Test High Availability
```bash
# Di Ubuntu, stop MariaDB
sudo systemctl stop mariadb

# Di Fedora, cek cluster size
mysql -uroot -p030105 -e "SHOW STATUS LIKE 'wsrep_cluster_size';"
# Harus: 1

# Aplikasi masih bisa konek via HAProxy!
mysql -h 127.0.0.1 -P 3307 -uroot -p030105 -e "SELECT 1;"
```

---

## 🐍 Setup Flask App

Edit `app.py`, ubah DB_CONFIG:
```python
DB_CONFIG = {
    'host': '192.168.100.120',  # IP Fedora (HAProxy)
    'port': 3307,                # Port HAProxy
    'user': 'root',
    'password': '030105',
    'database': 'beauty'
}
```

Run:
```bash
python3 app.py
```

Akses: `http://192.168.100.120:5000`

---

## 📊 Troubleshooting

### Cluster size masih 1
```bash
# Cek firewall
sudo firewall-cmd --list-ports  # Fedora
sudo ufw status                 # Ubuntu

# Cek log
sudo journalctl -u mariadb -f

# Test ping antar laptop
ping 192.168.100.116  # dari Fedora
ping 192.168.100.120  # dari Ubuntu
```

### HAProxy tidak konek
```bash
# Test manual
mysql -h 192.168.100.120 -P 3306 -uroot -p030105  # Langsung ke Fedora
mysql -h 192.168.100.116 -P 3306 -uroot -p030105  # Langsung ke Ubuntu

# Cek HAProxy log
sudo journalctl -u haproxy -f
```

---

**Setup selesai! Kamu punya 2-node Galera Cluster yang production-ready!** 🚀
