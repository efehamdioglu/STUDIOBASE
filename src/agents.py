from .llm_client import call_agent
from .schemas import CRITIC_VERDICT_SCHEMA, TRACKLIST_SCHEMA
from .state import TrackState

_PREAMBLE_KEYWORDS = ("şarkı sözü", "sarki sozu", "lyrics")


def _strip_preamble(text: str) -> str:
    """Küçük yerel modeller bazen şarkı sözünden önce 'İşte şarkı sözü:' gibi
    kısa bir giriş cümlesi ekliyor; prompt talimatına güvenmek yerine bunu
    kodda kesin olarak temizliyoruz. Türkçe'nin İ/i - ı/I büyük/küçük harf
    kuralları regex IGNORECASE ile güvenilir eşleşmediği için, ilk satırı
    içerik bazlı (anahtar kelime + kısalık) kontrol ediyoruz."""
    text = text.strip()
    parts = text.split("\n", 1)
    if len(parts) != 2:
        return text
    first_line, rest = parts
    stripped_first = first_line.strip().lower()
    is_short_intro = len(stripped_first) < 60 and stripped_first.endswith(":")
    has_keyword = any(kw in stripped_first for kw in _PREAMBLE_KEYWORDS)
    if is_short_intro and has_keyword:
        return rest.lstrip("\n").strip()
    return text

DIRECTOR_SYSTEM_PROMPT = """Sen bir müzik albümünün Kreatif Direktörüsün. Kullanıcının verdiği
tema/konsepti alıp tutarlı bir albüm başlığı ve o temaya uygun bir tracklist üretirsin.
Her parça için kısa bir başlık ve o parçanın duygu durumunu/atmosferini (mood) belirle.
Parçalar birbirinden farklı ama albümün genel temasıyla tutarlı olmalı; bir albüm
içindeki çeşitliliği (tempo, duygu, bakış açısı) yansıt.
ÖNEMLİ: Albüm başlığı ve her parçanın mood açıklaması TAMAMEN TÜRKÇE olmalı — hiçbir
İngilizce kelime veya ifade kullanma."""

LYRICIST_SYSTEM_PROMPT = """Sen deneyimli bir söz yazarısın (lyricist). Sana verilen başlık ve
mood'a uygun bir şarkı sözü yazarsın. Ayet (verse), nakarat (chorus) yapısını kullan.
Hece ölçüsünü ve kafiye şemasını tutarlı tut, akıcı ve söylenebilir bir söz üret.
Eğer önceki bir taslak ve eleştiri geri bildirimi verilmişse, o geri bildirimi dikkate
alarak sözü revize et — eleştirilen sorunları düzelt, iyi olan kısımları koru.

KURALLAR (kesinlikle uy):
1. Şarkı sözü TAMAMEN TÜRKÇE olmalı — tek bir İngilizce kelime veya dize bile kullanma.
2. Yanıtın SADECE şarkı sözünün kendisinden oluşsun. Giriş cümlesi ("İşte şarkı sözü:"),
   kapanış açıklaması, yorum veya öz-değerlendirme EKLEME. İlk satırdan son satıra kadar
   yalnızca ayet/nakarat metni olsun."""

CRITIC_SYSTEM_PROMPT = """Sen bir Ritim/Metrik Eleştirmenisin. Sana verilen şarkı sözünü hece
ölçüsü tutarlılığı, kafiye şeması ve genel akıcılık açısından değerlendirirsin. Sadece
gerçekten önemli, somut sorunlar varsa onaylamayı reddet (approved=false); küçük kusurlar
için de onaylayabilirsin, mükemmeliyetçi olma. Verdiğin feedback somut ve uygulanabilir
olmalı ki söz yazarı doğrudan revizyon yapabilsin.
Eğer şarkı sözünde Türkçe olmayan (İngilizce vb.) dizeler varsa bunu SOMUT bir sorun olarak
işaretle ve onaylama (approved=false) — bu tek başına reddetme sebebidir."""

VISUAL_SYSTEM_PROMPT = """Sen bir Görsel Stil Ajanısın. Albümün teması, başlığı ve parçaların
mood'larına dayanarak albüm kapağı için görsel bir prompt (Midjourney/DALL-E tarzı)
üretirsin. Stil, renk paleti, kompozisyon ve atmosfer unsurlarını içeren, doğrudan bir
görsel üretim aracına verilebilecek tek bir paragraf prompt yaz."""


def director_create_tracklist(theme: str, n_tracks: int) -> dict:
    user_message = (
        f"Albüm teması: {theme}\n"
        f"Lütfen {n_tracks} parçalık bir tracklist oluştur. "
        f"Her parça için başlık ve mood belirle."
    )
    return call_agent(
        DIRECTOR_SYSTEM_PROMPT,
        user_message,
        output_schema=TRACKLIST_SCHEMA,
    )


def lyricist_write(track: TrackState, feedback: str | None = None) -> str:
    if feedback is None:
        user_message = (
            f"Parça başlığı: {track.title}\nMood: {track.mood}\n\n"
            f"Bu bilgilere uygun bir şarkı sözü yaz."
        )
    else:
        user_message = (
            f"Parça başlığı: {track.title}\nMood: {track.mood}\n\n"
            f"Önceki taslak:\n{track.current_lyrics}\n\n"
            f"Eleştirmenin geri bildirimi:\n{feedback}\n\n"
            f"Bu geri bildirimi dikkate alarak sözü revize et."
        )
    lyrics = call_agent(LYRICIST_SYSTEM_PROMPT, user_message)
    return _strip_preamble(lyrics)


def critic_review(track: TrackState) -> dict:
    user_message = (
        f"Parça başlığı: {track.title}\nMood: {track.mood}\n\n"
        f"Değerlendirilecek şarkı sözü:\n{track.current_lyrics}"
    )
    return call_agent(
        CRITIC_SYSTEM_PROMPT,
        user_message,
        output_schema=CRITIC_VERDICT_SCHEMA,
    )


def visual_agent_cover_prompt(theme: str, album_title: str, track_moods: list[str]) -> str:
    user_message = (
        f"Albüm teması: {theme}\nAlbüm başlığı: {album_title}\n"
        f"Parçaların mood'ları: {', '.join(track_moods)}\n\n"
        f"Bu albüm için bir kapak sanatı görsel prompt'u üret."
    )
    return call_agent(VISUAL_SYSTEM_PROMPT, user_message)
