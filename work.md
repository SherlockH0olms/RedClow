# 🚀 RedClaw Daily Startup Guide

Her bilgisayarı açtığında bu adımları takip et.

---

## 1️⃣ Kaggle Phi-4 API'yi Başlat

**Kaggle'a git ve notebook'u çalıştır:**

1. https://www.kaggle.com adresine git
2. Phi-4 notebook'unu aç
3. "Run All" butonuna bas
4. ngrok URL'ini kopyala (örn: `https://xxxx-xx-xx-xx-xx.ngrok-free.app`)

---

## 2️⃣ Kali VM'de URL'i Güncelle

```bash
# 1. Config dosyasını aç
nano /opt/redclaw/config.env

# 2. LLM_API_URL satırını yeni ngrok URL ile değiştir:
LLM_API_URL=https://YENI-NGROK-URL.ngrok-free.app

# 3. Kaydet: Ctrl+O, Enter, Ctrl+X
```

---

## 3️⃣ Bağlantıyı Test Et

```bash
# Hızlı test
redclaw test

# Veya curl ile
curl -s https://NGROK-URL.ngrok-free.app/health
```

**Başarılı çıktı:**
```
✓ LLM Connected
```

---

## 4️⃣ RedClaw CLI'yi Başlat

```bash
redclaw
```

---

## 🔧 Hızlı Komutlar

| Komut | Açıklama |
|-------|----------|
| `redclaw` | CLI'yi başlat |
| `redclaw test` | LLM bağlantısını test et |
| `redclaw recon example.com` | Hedefte recon yap |
| `redclaw help` | Yardım göster |

---

## ⚠️ Yaygın Sorunlar

### "Connection refused" Hatası
- Kaggle notebook çalışmıyor
- ngrok URL eski/yanlış
- **Çözüm:** Kaggle'da notebook'u yeniden başlat, yeni URL al

### "LLM connection: unknown"
- API'ye bağlanamıyor
- **Çözüm:** config.env'deki URL'i kontrol et

---

## 📋 Günlük Checklist

- [ ] Kaggle notebook başlat
- [ ] ngrok URL'i kopyala
- [ ] config.env'i güncelle
- [ ] `redclaw test` ile bağlantıyı doğrula
- [ ] `redclaw` ile başla
