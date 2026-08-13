import json
import os
from dataclasses import asdict, dataclass, field


@dataclass
class CriticFeedbackEntry:
    iteration: int
    approved: bool
    issues: list[str]
    feedback: str


@dataclass
class TrackState:
    title: str
    mood: str
    lyrics_versions: list[str] = field(default_factory=list)
    critic_feedback_history: list[CriticFeedbackEntry] = field(default_factory=list)
    status: str = "draft"  # draft | approved | max_iterations_reached
    iterations_used: int = 0

    @property
    def current_lyrics(self) -> str:
        return self.lyrics_versions[-1] if self.lyrics_versions else ""

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class AlbumState:
    theme: str
    album_title: str = ""
    tracks: list[TrackState] = field(default_factory=list)
    cover_art_prompt: str = ""

    def to_dict(self) -> dict:
        return {
            "theme": self.theme,
            "album_title": self.album_title,
            "cover_art_prompt": self.cover_art_prompt,
            "tracks": [t.to_dict() for t in self.tracks],
        }

    def save_json(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    def markdown_report(self) -> str:
        lines = [f"# {self.album_title or self.theme}", "", f"**Tema:** {self.theme}", ""]
        if self.cover_art_prompt:
            lines += ["## Albüm Kapağı Görsel Prompt'u", "", self.cover_art_prompt, ""]
        for i, track in enumerate(self.tracks, start=1):
            lines += [f"## {i}. {track.title}", "", f"*Mood: {track.mood}*", ""]
            formatted_lyrics = track.current_lyrics.replace("\n", "  \n")
            lines += ["### Şarkı Sözü", "", formatted_lyrics, ""]
            if track.critic_feedback_history:
                lines.append("### Revizyon Geçmişi")
                for entry in track.critic_feedback_history:
                    verdict = "Onaylandı" if entry.approved else "Revizyon istendi"
                    lines.append(f"- İterasyon {entry.iteration}: {verdict} — {entry.feedback}")
                lines.append("")
            lines.append(f"_Durum: {track.status} ({track.iterations_used} iterasyon)_")
            lines.append("")
        return "\n".join(lines)

    def save_markdown(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.markdown_report())
