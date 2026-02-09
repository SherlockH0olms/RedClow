# 🔴 RedClaw Kullanım Kılavuzu

> **Bu dosya RedClaw'ın tüm özelliklerini A'dan Z'ye anlatır.**

---

## 📦 Kurulum (Zaten Yapıldı)

RedClaw `/home/kali/Desktop/RedClow` dizinine kuruldu ve kullanıma hazır.

---

## 🚀 Başlatma

Terminal aç ve şunu yaz:

```bash
cd ~/Desktop/RedClow
python3 -m redclaw.cli.app
```

Alternatif olarak:
```bash
cd ~/Desktop/RedClow && python3 -m redclaw.cli.app
```

---

## 🎯 İlk Adımlar (Başladıktan Sonra)

RedClaw açıldığında şöyle bir ekran göreceksin:

```
██████╗ ███████╗██████╗  ██████╗██╗      █████╗ ██╗    ██╗
██╔══██╗██╔════╝██╔══██╗██╔════╝██║     ██╔══██╗██║    ██║
██████╔╝█████╗  ██║  ██║██║     ██║     ███████║██║ █╗ ██║
██╔══██╗██╔══╝  ██║  ██║██║     ██║     ██╔══██║██║███╗██║
██║  ██║███████╗██████╔╝╚██████╗███████╗██║  ██║╚███╔███╔╝
╚═╝  ╚═╝╚══════╝╚═════╝  ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝ 

v2.0 | Autonomous Red Team AI Agent

RedClaw › _
```

---

## 📝 Temel Komutlar

### 1. Hedef Belirleme
```
target 10.10.138.70
```
Ya da slash command:
```
/target 10.10.138.70
```

### 2. Tarama Başlatma
```
scan
```
Ya da:
```
/scan
```

### 3. Yardım Görme
```
help
```
Slash komutları için:
```
/help
```

### 4. Durumu Görme
```
status
```
Ya da:
```
/status
```

### 5. Çıkış
```
exit
```
Ya da `Ctrl+D`

---

## ⌨️ Klavye Kısayolları

| Tuş | Ne Yapar |
|-----|----------|
| `Tab` | Komutu tamamla (autocomplete) |
| `Tab Tab` | Tüm komutları listele |
| `↑` (Yukarı Ok) | Önceki komutu getir |
| `↓` (Aşağı Ok) | Sonraki komutu getir |
| `Ctrl+C` | Mevcut işlemi iptal et |
| `Ctrl+D` | Çıkış yap |
| `Ctrl+L` | Ekranı temizle |

---

## 🔧 Slash Komutları (/ ile başlar)

| Komut | Açıklama | Örnek |
|-------|----------|-------|
| `/clear` | Ekranı temizle | `/clear` |
| `/config` | Ayarları göster | `/config` |
| `/status` | Oturum durumu | `/status` |
| `/help` | Slash komut listesi | `/help` |
| `/model` | LLM model bilgisi | `/model` |
| `/session` | Oturumları yönet | `/session list` |
| `/export` | JSON'a aktar | `/export rapor.json` |
| `/target` | Hedef ayarla | `/target 10.10.138.70` |
| `/scan` | Hedefi tara | `/scan` |
| `/theme` | Tema değiştir | `/theme` |

---

## 💻 Bash Modu (! ile başlar)

Doğrudan shell komutları çalıştır:

```bash
!whoami
```

```bash
!nmap -sV 10.10.138.70
```

```bash
!cat /etc/passwd
```

```bash
!ls -la
```

---

## 🎯 Normal Komutlar

| Komut | Açıklama | Örnek |
|-------|----------|-------|
| `target` | Hedef IP/domain | `target 10.10.138.70` |
| `scan` | Tarama başlat | `scan` |
| `recon` | Pasif keşif | `recon example.com` |
| `exploit` | Zafiyet sömür | `exploit` |
| `privesc` | Yetki yükseltme | `privesc` |
| `report` | Rapor oluştur | `report` |
| `findings` | Bulguları göster | `findings` |
| `history` | Komut geçmişi | `history` |
| `config` | Ayarlar | `config` |
| `status` | Durum | `status` |
| `clear` | Ekran temizle | `clear` |
| `help` | Yardım | `help scan` |
| `exit` | Çıkış | `exit` |

---

## 🔍 Özel Tool Komutları

### Nmap
```
nmap 10.10.138.70
```
RedClaw sana uygun nmap komutu önerir.

### Nikto
```
nikto 10.10.138.70
```
Web güvenlik taraması.

### Gobuster
```
gobuster 10.10.138.70
```
Dizin brute-force.

---

## 📋 Adım Adım Örnek Senaryo

### 1. RedClaw'ı Başlat
```bash
cd ~/Desktop/RedClow
python3 -m redclaw.cli.app
```

### 2. Hedef Ayarla
```
target 10.10.138.70
```
Çıktı: `✓ Target set: 10.10.138.70`

### 3. Tab ile Komut Tamamla
- `sc` yaz ve `Tab` bas → `scan` tamamlanır
- `tar` yaz ve `Tab` bas → `target` tamamlanır

### 4. Tarama Başlat
```
scan
```
RedClaw hedefi otomatik tarar.

### 5. Bash ile Manuel Nmap
```
!nmap -sV -sC -p- 10.10.138.70
```
Doğrudan nmap çalıştırır.

### 6. Durumu Kontrol Et
```
/status
```

### 7. Bulguları Gör
```
findings
```

### 8. Rapor Oluştur
```
report
```

### 9. Çıkış
```
exit
```

---

## ⚠️ Önemli Notlar

1. **TryHackMe VPN**: Hedef taramadan önce TryHackMe VPN'e bağlı olduğundan emin ol:
   ```bash
   !ip a | grep tun0
   ```

2. **API URL**: LLM bağlantısı için (opsiyonel):
   ```bash
   export LLM_API_URL="https://0682-34-60-89-157.ngrok-free.app"
   ```

3. **Yardım**: Herhangi bir komut hakkında:
   ```
   help scan
   help exploit
   help target
   ```

---

## 🚨 Hata Çözümleri

### "No target set" Hatası
```
target 10.10.138.70
```
Önce hedef belirle.

### "Command not found" Hatası
Tab'a bas ve mevcut komutları gör.

### Ekran Karıştıysa
```
/clear
```
veya `Ctrl+L`

---

## 📞 Hızlı Referans Kartı

```
┌─────────────────────────────────────────────────────────┐
│  REDCLAW HIZLI REFERANS                                │
├─────────────────────────────────────────────────────────┤
│  BAŞLAT: python3 -m redclaw.cli.app                    │
│                                                         │
│  HEDEF:  target <IP>        veya  /target <IP>         │
│  TARA:   scan               veya  /scan                │
│  DURUM:  status             veya  /status              │
│  YARDIM: help               veya  /help                │
│  ÇIKIŞ:  exit               veya  Ctrl+D               │
│                                                         │
│  BASH:   !<komut>           örn:  !nmap -sV <IP>       │
│  TAB:    Komutu tamamla                                 │
│  ↑↓:     Geçmiş komutlar                               │
└─────────────────────────────────────────────────────────┘
```

---

**Hazır! Şimdi test etmeye başlayabilirsin!** 🎯
