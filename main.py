import argparse
import re
from pathlib import Path

from dotenv import load_dotenv

from src.orchestrator import run_album_pipeline

load_dotenv()


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9ğüşıöç\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    return text or "album"


def print_progress(event: str, **kwargs) -> None:
    if event == "director_start":
        print(f"[Kreatif Direktör] Tema alındı: '{kwargs['theme']}' — {kwargs['n_tracks']} parçalık tracklist oluşturuluyor...")
    elif event == "director_done":
        print(f"[Kreatif Direktör] Albüm başlığı: {kwargs['album_title']}")
    elif event == "track_start":
        track = kwargs["track"]
        print(f"\n--- Parça {kwargs['index']}/{kwargs['total']}: {track.title} (mood: {track.mood}) ---")
    elif event == "track_iteration":
        verdict = kwargs["verdict"]
        durum = "ONAYLANDI" if verdict["approved"] else "REVİZYON İSTENDİ"
        print(
            f"[Söz Yazarı -> Eleştirmen] İterasyon {kwargs['iteration']}/{kwargs['max_iterations']}: {durum}"
        )
        if not verdict["approved"]:
            print(f"  Geri bildirim: {verdict['feedback']}")
    elif event == "track_done":
        track = kwargs["track"]
        print(f"[Parça {kwargs['index']}] Durum: {track.status} ({track.iterations_used} iterasyon)")
    elif event == "visual_start":
        print("\n[Görsel Stil Ajanı] Albüm kapağı prompt'u üretiliyor...")
    elif event == "visual_done":
        print("[Görsel Stil Ajanı] Tamamlandı.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Müzik Albümü Konsept & Söz Yazarı Multi-Agent Orkestrasyonu")
    parser.add_argument("--theme", required=True, help="Albüm teması (örn. 'Cyberpunk Melankoli')")
    parser.add_argument("--tracks", type=int, default=4, help="Parça sayısı (varsayılan: 4)")
    parser.add_argument("--max-iterations", type=int, default=3, help="Parça başına maksimum revizyon döngüsü (varsayılan: 3)")
    parser.add_argument("--provider", choices=["ollama", "gemini", "anthropic"], default=None, help="LLM sağlayıcısı (varsayılan: LLM_PROVIDER env ya da 'ollama')")
    parser.add_argument("--model", default=None, help="Kullanılacak model adı (sağlayıcıya göre: Ollama/Gemini model adı ya da Claude model ID)")
    parser.add_argument("--output-dir", default="output", help="Çıktı klasörü (varsayılan: ./output)")
    args = parser.parse_args()

    import os
    if args.provider:
        os.environ["LLM_PROVIDER"] = args.provider
    if args.model:
        provider = os.environ.get("LLM_PROVIDER", "ollama").strip().lower()
        if provider == "ollama":
            os.environ["OLLAMA_MODEL"] = args.model
        elif provider == "gemini":
            os.environ["GEMINI_MODEL"] = args.model
        else:
            os.environ["ANTHROPIC_MODEL"] = args.model

    album = run_album_pipeline(
        theme=args.theme,
        n_tracks=args.tracks,
        max_iterations=args.max_iterations,
        on_progress=print_progress,
    )

    slug = slugify(album.album_title or args.theme)
    output_dir = Path(args.output_dir)
    md_path = output_dir / f"{slug}.md"
    json_path = output_dir / f"{slug}.json"

    album.save_markdown(str(md_path))
    album.save_json(str(json_path))

    print(f"\nAlbüm tamamlandı: {album.album_title}")
    print(f"  Markdown: {md_path}")
    print(f"  JSON:     {json_path}")


if __name__ == "__main__":
    main()
