import re
from dataclasses import dataclass
from pathlib import Path

from .llm_client import call_agent
from .schemas import CRITIC_VERDICT_SCHEMA, TRACKLIST_SCHEMA
from .state import TrackState

_PREAMBLE_KEYWORDS = ("şarkı sözü", "sarki sozu", "lyrics")

_AGENTS_DIR = Path(__file__).resolve().parent.parent / ".claude" / "agents"
_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)


@dataclass(frozen=True)
class AgentSpec:
    """Her ajanın kimliği: 'name' + 'description' + 'prompt' ayrı ayrı alanlar
    olarak tutulur. Kaynak, dersteki .claude/agents/*.md konvansiyonuyla birebir
    aynı formatta yazılan dosyalar: frontmatter'da name+description, gövdede
    prompt. Bu sınıf o dosyaları parse edip runtime nesnesine çevirir — yani
    ajanlar kod içinde ikinci kez tanımlanmıyor, tek gerçek kaynak .md dosyaları."""

    name: str
    description: str
    prompt: str

    @classmethod
    def from_markdown(cls, path: Path) -> "AgentSpec":
        match = _FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
        if not match:
            raise ValueError(f"Ajan dosyası frontmatter formatına uymuyor: {path}")
        frontmatter, body = match.groups()
        meta: dict[str, str] = {}
        for line in frontmatter.splitlines():
            key, sep, value = line.partition(":")
            if sep:
                meta[key.strip()] = value.strip()
        return cls(
            name=meta.get("name", path.stem),
            description=meta.get("description", ""),
            prompt=body.strip(),
        )


def _load_agents() -> dict[str, AgentSpec]:
    return {md.stem: AgentSpec.from_markdown(md) for md in sorted(_AGENTS_DIR.glob("*.md"))}


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

_SPECS = _load_agents()

DIRECTOR = _SPECS["kreatif-direktor"]
LYRICIST = _SPECS["soz-yazari"]
CRITIC = _SPECS["ritim-metrik-elestirmeni"]
VISUAL = _SPECS["gorsel-stil-ajani"]

AGENTS: list[AgentSpec] = [DIRECTOR, LYRICIST, CRITIC, VISUAL]


def director_create_tracklist(theme: str, n_tracks: int) -> dict:
    user_message = (
        f"Albüm teması: {theme}\n"
        f"Lütfen {n_tracks} parçalık bir tracklist oluştur. "
        f"Her parça için başlık ve mood belirle."
    )
    return call_agent(
        DIRECTOR.prompt,
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
    lyrics = call_agent(LYRICIST.prompt, user_message)
    return _strip_preamble(lyrics)


def critic_review(track: TrackState) -> dict:
    user_message = (
        f"Parça başlığı: {track.title}\nMood: {track.mood}\n\n"
        f"Değerlendirilecek şarkı sözü:\n{track.current_lyrics}"
    )
    return call_agent(
        CRITIC.prompt,
        user_message,
        output_schema=CRITIC_VERDICT_SCHEMA,
    )


def visual_agent_cover_prompt(theme: str, album_title: str, track_moods: list[str]) -> str:
    user_message = (
        f"Albüm teması: {theme}\nAlbüm başlığı: {album_title}\n"
        f"Parçaların mood'ları: {', '.join(track_moods)}\n\n"
        f"Bu albüm için bir kapak sanatı görsel prompt'u üret."
    )
    return call_agent(VISUAL.prompt, user_message)
