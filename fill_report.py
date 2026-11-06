# -*- coding: utf-8 -*-
"""SENG 456 teslim formunu STUDIOBASE proje içeriğiyle doldurur."""

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject

SRC = r"C:\Users\efeha\Downloads\proje-teslim-sablonu.pdf"
DST = r"C:\Users\efeha\Downloads\proje-teslim-sablonu-DOLU.pdf"

text_fields = {
    "projectTitle": "STUDIOBASE — Müzik Albümü Konsept ve Şarkı Sözü Multi-Agent Orkestrasyon Sistemi",

    # Kapak - kişisel bilgiler
    "field2": "220206023",
    "field3": "Bilgisayar Mühendisliği",
    "field4": "220206023@ostimteknik.edu.tr",
    "field5": "https://www.myskillos.com/project/5384f0a7-8ecc-4d5e-a3e7-e0bbaa106d3b",

    # 1. Proje Özeti
    "field8": (
        "Müzik albümü konsepti ve şarkı sözü üretimi; konsept geliştirme, söz yazımı, "
        "metrik/kafiye denetimi ve görsel yönlendirme gibi birbirini tamamlayan uzmanlık "
        "alanları gerektirir. Tek bir LLM çağrısıyla üretilen içerik genellikle tutarsız "
        "kalite ve dilde savrulma (örn. İngilizce'ye kayma) gösterir; öz-eleştiri mekanizması "
        "yoktur."
    ),
    "field9": (
        "Amaç, statik if-else akışları yerine LLM ajanlarının birbirini eleştirip "
        "yapılandırılmış kararlarla dinamik olarak yönlendirdiği bir orkestrasyon mimarisi "
        "tasarlamak ve bunu çalışan bir uygulamada göstermektir. Hedef kullanıcı, tutarlı bir "
        "albüm konsepti taslağı isteyen içerik üreticileri ve bu dersin değerlendiricileridir."
    ),
    "field10": (
        "Kullanıcı bir albüm teması girer; Kreatif Direktör ajanı albüm başlığı ve N parçalık "
        "bir tracklist (başlık+mood) üretir. Her parça için Söz Yazarı bir taslak yazar, Ritim/"
        "Metrik Eleştirmeni bunu yapılandırılmış JSON çıktı (approved/issues/feedback) ile "
        "değerlendirir; onaylanmazsa Söz Yazarı geri bildirimle sözü revize eder — bu döngü "
        "onaylanana veya maks. iterasyona kadar sürer. Tüm parçalar bitince Görsel Stil Ajanı "
        "albüm kapağı için bir görsel üretim prompt'u yazar. Sonuç Markdown/JSON rapor olarak "
        "ve retro bir Streamlit arayüzünde (canlı ajan pipeline diyagramı ile) sunulur."
    ),
    "field11": "Yaratıcı içerik üretimi — müzik albümü konsepti ve söz yazımı",
    "field12": "Python 3.14, Streamlit, özel JS Streamlit bileşeni (knob), python-dotenv",
    "field13": "Anthropic Claude (claude-sonnet-5), Ollama (qwen2.5:7b, yerel), Google Gemini",
    "field14": "Çalışır durumda; CLI ve web arayüzüyle uçtan uca test edildi",

    # 2. Girdi, Çıktı ve Kullanım
    "field15": (
        "Albüm teması (serbest metin), parça sayısı (1-8), parça başına maksimum revizyon "
        "sayısı (1-5), LLM sağlayıcısı (Ollama/Anthropic/Gemini) ve model seçimi — tümü "
        "arayüzdeki döner knob kontrolleriyle girilir."
    ),
    "field16": (
        "Albüm başlığı, her parça için başlık/mood/şarkı sözü/revizyon geçmişi, albüm kapağı "
        "için görsel üretim prompt'u; bunlar hem Markdown/JSON dosyası olarak (indirilebilir) "
        "hem de arayüzde canlı olarak sunulur."
    ),
    "field17": (
        "Kullanıcı LCD ekrana albüm temasını yazar, knob'larla parça sayısı/revizyon/"
        "sağlayıcı/model ayarlarını yapar ve PLAY butonuna basar. Ajan Pipeline diyagramı "
        "hangi ajanın aktif olduğunu canlı gösterirken, ajan konuşma günlüğü her kararı "
        "(özellikle Eleştirmen'in JSON verdict'ini) renkli kartlarla listeler. Üretim bitince "
        "parça kartları, kapak prompt'u ve indirilebilir rapor görüntülenir."
    ),
    "field18": (
        "Girdi: tema='Cyberpunk Melankoli', 3 parça, maks. 3 revizyon. Çıktı: albüm başlığı "
        "'Yasak Şehrin Anıları', 3 parçanın tutarlı Türkçe şarkı sözleri (kafiye/hece uyumlu), "
        "her parça için Eleştirmen'in somut geri bildirimi ve bir albüm kapağı görsel prompt'u."
    ),

    # 3. Sistem Tasarımı
    "field19": (
        "Görev, yaratıcı üretim + eleştirel denetim + revizyon döngüleri gerektiriyor; bu, "
        "sabit bir iş akışından çok, ajanların birbirinin çıktısını değerlendirip dinamik "
        "karar verdiği bir mimariye uygundur. Yönlendirme kararı (revize et / finalize et) "
        "kodda sabit bir kural değil, Eleştirmen ajanının ürettiği yapılandırılmış JSON "
        "çıktısına (approved alanı) dayanmaktadır."
    ),
    "field20": (
        "Kreatif Direktör: tema -> albüm başlığı + tracklist. Söz Yazarı: başlık/mood "
        "(+geri bildirim) -> şarkı sözü taslağı. Ritim/Metrik Eleştirmeni: söz -> yapılandırılmış "
        "verdict (approved/issues/feedback). Görsel Stil Ajanı: tema+başlık+mood'lar -> kapak "
        "sanatı prompt'u. Orkestratör (run_album_pipeline): bu ajanları sırayla/döngüsel çağırır "
        "ve AlbumState/TrackState durumunu yönetir."
    ),
    "field21": (
        "Direktör -> (tracklist JSON) -> her parça için Söz Yazarı <-> Eleştirmen (şarkı sözü "
        "metni / yapılandırılmış JSON verdict) döngüsü -> tüm parçalar bitince -> Görsel Ajan "
        "(mood listesi -> prompt metni). Orkestratör her adımda on_progress(event, **kwargs) "
        "callback'iyle olayları dışarıya yayınlar; bu hem CLI çıktısını hem Streamlit'teki "
        "canlı Ajan Pipeline diyagramını besler."
    ),

    # 4. Ajanlar, Araçlar ve Entegrasyonlar
    "field22": "Kreatif Direktör",
    "field23": "Albüm başlığı ve tracklist oluşturma",
    "field24": "Alır: tema, parça sayısı. Üretir: albüm başlığı + (başlık,mood) listesi (JSON)",
    "field25": "Söz Yazarı",
    "field26": "Şarkı sözü yazma / revize etme",
    "field27": "Alır: başlık, mood, (varsa) Eleştirmen geri bildirimi. Üretir: şarkı sözü metni",
    "field28": "Ritim/Metrik Eleştirmeni",
    "field29": "Söz kalite denetimi, onay/revizyon kararı",
    "field30": "Alır: şarkı sözü. Üretir: yapılandırılmış JSON (approved, issues, feedback)",
    "field31": "Görsel Stil Ajanı",
    "field32": "Albüm kapağı görsel prompt'u üretme",
    "field33": "Alır: tema, başlık, tüm parça mood'ları. Üretir: görsel üretim prompt metni",
    "field34": (
        "Anthropic Claude API (yapılandırılmış JSON çıktı için output_config.format), Ollama "
        "yerel API (ollama.chat, JSON schema ile yapılandırılmış çıktı), Google Gemini API "
        "(REST, responseSchema ile yapılandırılmış çıktı) — üç sağlayıcı da aynı call_agent() "
        "arayüzü arkasında soyutlanmış, LLM_PROVIDER env değişkeniyle tek satırda "
        "değiştiriliyor. Ayrıca özel yazılmış bir Streamlit bileşeni (vanilla JS, postMessage "
        "protokolü) döner knob kontrolleri için kullanıldı."
    ),
    "field35": (
        "Eleştirmen'in onay/red kararı insan onayı gerektirmez, tamamen modelin "
        "yapılandırılmış çıktısına bırakılmıştır — ancak max_iterations ile döngü bir üst "
        "sınıra bağlanarak sonsuz döngü riski engellenmiştir. API anahtarları .env dosyasında "
        "tutulur, koda gömülmez."
    ),

    # 5. Uygulama ve Çalıştırma
    "field36": "https://www.myskillos.com/project/5384f0a7-8ecc-4d5e-a3e7-e0bbaa106d3b",
    "field37": 'streamlit run app.py  (CLI: python main.py --theme "..." --tracks 4)',
    "field38": "anthropic, streamlit, ollama, python-dotenv, pywebview (bkz. requirements.txt)",
    "field39": "app.py (arayüz), main.py (CLI), src/ (ajanlar, orkestratör, state, LLM istemcisi), components/knob/ (özel bileşen), output/ (üretilen albümler)",
    "field40": "Python 3.14, Windows 11; pip install -r requirements.txt sonrası yerel çalışır",
    "field41": (
        "1) pip install -r requirements.txt. 2) .env.example dosyasını .env olarak kopyalayıp "
        "LLM_PROVIDER ve ilgili API anahtarını girin. 3) streamlit run app.py ile arayüzü "
        "başlatın (http://localhost:8501). 4) Tema girip knob'larla ayarları yapıp PLAY'e "
        "basın. Alternatif olarak CLI'dan python main.py --theme \"...\" ile çalıştırılabilir."
    ),
    "field42": (
        "Özel knob bileşeni tarayıcıda hiç tepki vermiyordu; Streamlit'in kurulu sürümünün "
        "(1.60.0) frontend JS kaynak kodu incelenerek mesajların isStreamlitMessage:true "
        "işareti taşımadan sessizce yok sayıldığı tespit edildi ve bileşenin postMessage "
        "çağrılarına bu alan eklenerek çözüldü."
    ),

    # 6. Testler ve Sonuçlar
    "field43": "Ollama qwen2.5-coder:3b ile uçtan uca üretim",
    "field44": "Mimari sorunsuz çalıştı; içerik kalitesi düşüktü (bozuk Türkçe / İngilizce'ye kayma)",
    "field45": "Kısmen başarılı",
    "field46": "Ollama qwen2.5:7b ile aynı test (prompt sıkılaştırma sonrası)",
    "field47": "3 parça, tamamen tutarlı Türkçe söz; Eleştirmen somut geri bildirim üretti",
    "field48": "Başarılı",
    "field49": "Çok sağlayıcılı call_agent() (Ollama/Anthropic/Gemini) geçiş testi",
    "field50": "Tek env değişkeniyle (LLM_PROVIDER) sorunsuz sağlayıcı değişimi doğrulandı",
    "field51": "Başarılı",
    "field52": "Özel knob bileşeni (sürükle/tekerlek) tarayıcı testi",
    "field53": "Kullanıcı ekran görüntüsüyle döndürme/değer güncellemesi doğrulandı",
    "field54": "Başarılı",
    "field55": (
        "Proje, dersin istediği dinamik/çoklu ajan orkestrasyonunu (durum yönetimi, geri "
        "bildirim döngüsü, dinamik yönlendirme) somut ve çalışan bir uygulamada gösterdi. "
        "Eleştirmen ajanının yapılandırılmış JSON kararı, orkestratörün akışını statik kod "
        "değil model çıktısı belirleyerek yönlendiriyor; bu hem CLI hem arayüzde (canlı "
        "Pipeline diyagramı) gözlemlenebiliyor."
    ),
    "field56": (
        "Eleştirmen'in gerçek bir revizyon istediği (approved=false) senaryo canlı olarak "
        "henüz gözlemlenmedi — küçük test setlerinde tüm parçalar ilk denemede onaylandı; "
        "mekanizma kodda mevcut ve max_iterations ile sınırlı. pywebview masaüstü penceresi "
        "(launcher.py) yazıldı ama henüz uçtan uca test edilmedi."
    ),

    # 7. Güvenlik
    "field61": (
        "API anahtarları yalnızca .env dosyasında tutulur ve versiyon kontrolüne dahil "
        "edilmez. Üretilen içerik (şarkı sözü, görsel prompt) tamamen sentetik olup gerçek "
        "kişisel veri işlenmez. Yerel model (Ollama) kullanımı, verinin cihaz dışına "
        "çıkmadığı gizlilik-dostu bir alternatif olarak sunulur."
    ),

    # 8. Sonuç ve Gelecek Çalışmalar
    "field62": (
        "Statik if-else akışı yerine, bir ajanın (Eleştirmen) yapılandırılmış çıktısının "
        "doğrudan başka bir ajana (Söz Yazarı) dönüşü tetiklediği gerçek bir dinamik "
        "yönlendirme mekanizması uçtan uca kuruldu ve görselleştirildi. Ayrıca aynı "
        "orkestrasyon mantığının üç farklı LLM sağlayıcısı (yerel/ücretsiz ve bulut/ücretli) "
        "üzerinde değişmeden çalıştığı gösterildi."
    ),
    "field63": (
        "Parça bazlı (albüm kapağına ek olarak) görsel prompt üretimi; Eleştirmen'in "
        "revizyon istediği senaryoları vurgulayan bir demo/test seti; pywebview ile tam "
        "masaüstü paketleme; çoklu-ajan (multiagent) delegasyon desenlerinin denenmesi."
    ),
    "field64": (
        "Durum yönetimi (state management), geri bildirim döngüleri (reflection & feedback "
        "loops), dinamik ajan yönlendirmesi (yapılandırılmış çıktıya dayalı routing), çok "
        "ajanlı orkestrasyon mimarisi."
    ),

    # 10. Öğrenci Beyanı
    "field73": "220206023",

    # 9. Kaynaklar
    "field65": (
        "Anthropic Claude API dokümantasyonu (platform.claude.com), Ollama resmi "
        "dokümantasyonu ve Python istemci kütüphanesi, Google Gemini API dokümantasyonu, "
        "Streamlit resmi dokümantasyonu ve Custom Components protokolü (streamlit.io/"
        "components), qwen2.5 model ailesi (Alibaba/Qwen, Ollama üzerinden). Kod geliştirme "
        "sürecinde Claude (Anthropic) ile birlikte çalışılmıştır."
    ),
}

checkbox_on = [
    "field57", "field58", "field59", "field60",  # Güvenlik: hepsi geçerli
    "field66",  # Bu formun doldurulmuş PDF sürümü eklendi
    "field67",  # Kaynak kod / proje dosyaları erişilebilir (myskillos linki)
    "field68",  # Kurulum ve çalıştırma bilgileri eklendi
    "field69",  # Test veya örnek kullanım sonucu eklendi
    "field70",  # Gizli anahtar / parola yok
]

reader = PdfReader(SRC)
writer = PdfWriter()
writer.append(reader)

# Şablonun AcroForm /DR kaynağında önceden kayıtlı bir "/Helv" font nesnesi var.
# pypdf, bir alanın fontunu çözerken önce bu HAZIR kaynağı kullanmaya çalışıyor;
# bu yol üzerinden yapılan "bu metni kodlayabilir miyim?" kontrolü bazı alanlarda
# hatalı biçimde "evet" dönüyor ve Türkçe karaktersiz düz Helvetica ile devam
# ediyor (karakterler kaybolup tırnak işaretine benzer bir şeye dönüşüyor).
# Bu hazır kaynağı kaldırarak HER alanın fontunu sıfırdan (ve dolayısıyla doğru
# kodlama tespitiyle) kurmasını zorluyoruz.
acro_form = writer._root_object["/AcroForm"]
dr_fonts = acro_form.get("/DR", {}).get("/Font")
if dr_fonts is not None and "/Helv" in dr_fonts:
    del dr_fonts[NameObject("/Helv")]

# Şablondaki her metin alanının /DA'sında SABİT bir font boyutu (10pt) var.
# pypdf, font boyutu sabitse akıllı satır-kaydırma/otomatik-küçültme mantığını
# atlayıp metni TEK SATIRDA çiziyor ve kutu dışına taşanı görünmez şekilde
# kırpıyor — uzun cevaplarımızın kutunun ortasında kesilmesinin sebebi budur.
# Boyutu 0 (otomatik) yaparak pypdf'in doğru sarma/küçültme algoritmasını
# tetikliyoruz.
import re as _re

target_fields = set(text_fields) | set(checkbox_on)
for page in writer.pages:
    if "/Annots" not in page:
        continue
    for annot in page["/Annots"]:
        obj = annot.get_object()
        if obj.get("/FT") != "/Tx" and obj.get("/Subtype") != "/Widget":
            continue
        parent = obj.get("/Parent")
        name = obj.get("/T") or (parent.get_object().get("/T") if parent else None)
        if name not in target_fields:
            continue
        da = obj.get("/DA")
        if da is None:
            continue
        new_da = _re.sub(r"(?<=\s)[\d.]+(?=\s+Tf)", "0", str(da))
        obj[NameObject("/DA")] = TextStringObject(new_da)

for page in writer.pages:
    values = dict(text_fields)
    for cb in checkbox_on:
        values[cb] = "/Yes"
    # auto_regenerate=False: pypdf'in KENDİ ürettiği görünüm akışını (Türkçe
    # karakterler için otomatik cp1254 kodlama yedeğiyle) korur ve NeedAppearances
    # bayrağını KAPALI bırakır — bu bayrak açık olsaydı PDF görüntüleyici pypdf'in
    # ürettiği doğru görünümü yok sayıp kendi (Türkçe desteklemeyen) render'ını
    # yapardı; bu yüzden bilerek True yapmıyoruz.
    writer.update_page_form_field_values(page, values, auto_regenerate=False)

with open(DST, "wb") as f:
    writer.write(f)

print("Yazıldı:", DST)
