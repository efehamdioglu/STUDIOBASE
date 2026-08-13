from .agents import (
    critic_review,
    director_create_tracklist,
    lyricist_write,
    visual_agent_cover_prompt,
)
from .state import AlbumState, CriticFeedbackEntry, TrackState


def _process_track(
    track: TrackState, max_iterations: int, index: int, total: int, on_progress
) -> None:
    """Söz Yazarı <-> Eleştirmen geri bildirim döngüsü.

    Yönlendirme kararı (revize et / finalize et) statik if-else zinciriyle
    değil, Eleştirmenin ürettiği yapılandırılmış `approved` alanına göre
    alınır — dinamik ajan yönlendirmesi burada gerçekleşir.
    """
    feedback = None
    for iteration in range(1, max_iterations + 1):
        on_progress(
            "lyricist_start", index=index, total=total, track=track,
            iteration=iteration, max_iterations=max_iterations,
        )
        lyrics = lyricist_write(track, feedback)
        track.lyrics_versions.append(lyrics)
        track.iterations_used = iteration
        on_progress(
            "lyricist_done", index=index, total=total, track=track,
            iteration=iteration, max_iterations=max_iterations,
        )

        on_progress(
            "critic_start", index=index, total=total, track=track,
            iteration=iteration, max_iterations=max_iterations,
        )
        verdict = critic_review(track)
        track.critic_feedback_history.append(
            CriticFeedbackEntry(
                iteration=iteration,
                approved=verdict["approved"],
                issues=verdict["issues"],
                feedback=verdict["feedback"],
            )
        )
        on_progress(
            "track_iteration", index=index, total=total, track=track,
            iteration=iteration, max_iterations=max_iterations, verdict=verdict,
        )

        if verdict["approved"]:
            track.status = "approved"
            return
        feedback = verdict["feedback"]

    track.status = "max_iterations_reached"


def run_album_pipeline(
    theme: str,
    n_tracks: int = 4,
    max_iterations: int = 3,
    on_progress=lambda *args, **kwargs: None,
) -> AlbumState:
    on_progress("director_start", theme=theme, n_tracks=n_tracks)
    tracklist = director_create_tracklist(theme, n_tracks)

    album = AlbumState(theme=theme, album_title=tracklist["album_title"])
    on_progress("director_done", album_title=album.album_title)

    total = len(tracklist["tracks"])
    for i, item in enumerate(tracklist["tracks"], start=1):
        track = TrackState(title=item["title"], mood=item["mood"])
        album.tracks.append(track)
        on_progress("track_start", index=i, total=total, track=track)
        _process_track(track, max_iterations, i, total, on_progress)
        on_progress("track_done", index=i, track=track)

    on_progress("visual_start")
    album.cover_art_prompt = visual_agent_cover_prompt(
        theme, album.album_title, [t.mood for t in album.tracks]
    )
    on_progress("visual_done", prompt=album.cover_art_prompt)

    return album
