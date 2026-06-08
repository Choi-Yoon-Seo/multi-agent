from pathlib import Path
import os
import json
import random
import spotipy
import pickle

from groq import Groq
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

load_dotenv()

# 설정
USE_LLM = True
USE_LLM_REVIEW = True

GROQ_REVIEW_MODEL = "llama-3.1-8b-instant"
OPENAI_REVIEW_MODEL = "gpt-5-mini"

# SAMPLE INPUT
SAMPLE_INPUT = """
[입력]
- 상황: 드라이브
- 장르: k-pop
- 아티스트: NCT WISH, RIIZE
"""

# 입력 분석 에이전트 (규칙 기반)
def analyze_with_rules(text):
    results = []
    blocks = text.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        fact = {}
        for line in lines:
            line = line.strip()
            if line.startswith("["):
                fact["input_id"] = line
            elif line.startswith("- 상황:"):
                fact["situation"] = (line.replace("- 상황:", "").strip())
            elif line.startswith("- 장르:"):
                fact["genre"] = [g.strip() for g in line.replace("- 장르:", "").split(",")]
            elif line.startswith("- 아티스트:"):
                fact["artist"] = [a.strip() for a in line.replace("- 아티스트:", "").split(",")]
        if fact:
            results.append(fact)
    return results

# 입력 분석 에이전트 (Groq)
def analyze_with_groq(text):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY 환경변수 없음")
    client = Groq(api_key=api_key)
    prompt = f"""
사용자 입력에서 정보를 추출해줘.

반드시 JSON list만 반환해.

형식:
[
  {{
    "input_id": "...",
    "situation": "...",
    "genre": [...],
    "artist": [...]
  }}
]

규칙:
- artist는 아티스트 이름 목록이다.
- 아티스트 이름은 절대로 단어별로 분리하지 마라.
- 입력된 아티스트명을 그대로 유지하라.
- 쉼표(,)로 구분된 경우에만 여러 아티스트로 나눈다.
- 예시:
  "NCT WISH" → ["NCT WISH"]
  "Red Velvet" → ["Red Velvet"]
  "NCT WISH, RIIZE" → ["NCT WISH", "RIIZE"]

입력:
{text}
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    result = response.choices[0].message.content
    return json.loads(result)

# 입력 분석 통합
def extract_facts(text):
    if USE_LLM:
        try:
            print("[LLM] 입력 분석 실행")
            return analyze_with_groq(text)
        except Exception as e:
            print(f"[LLM] 실패: {e}")
            print("[LLM] 규칙 기반 분석으로 fallback")
    print("[Rules] 규칙 기반 분석 실행")
    return analyze_with_rules(text)

# 상황 분석 에이전트
def classify_items(facts):
    mapping = {
        "드라이브": {"mood": "drive", "energy": "high"},
        "운동": {"mood": "workout", "energy": "very_high"},
        "집중": {"mood": "focus", "energy": "low"},
        "슬플 때": {"mood": "sad", "energy": "low"},
        "신날 때": {"mood": "excited", "energy": "very_high"},
        "씻을 때": {"mood": "shower", "energy": "medium"},
        "공부할 때": {"mood": "study", "energy": "low"},
        "잠들기 전": {"mood": "sleep", "energy": "very_low"},
        "산책할 때": {"mood": "walk", "energy": "medium"},
        "비 오는 날": {"mood": "rainy", "energy": "low"}
    }
    classified = []
    for fact in facts:
        situation = fact.get("situation", "")
        music_props = mapping.get(situation, {"mood": "default", "energy": "medium"})
        # Determine playlist structure and judgment reason
        energy = music_props["energy"]
        if energy == "very_high":
            playlist_structure = "도입부 → 전개부 → 정점부 2곡 → 마무리"
            judgment_reason = "energy가 매우 높아 정점부를 2곡으로 구성"
        elif energy == "low":
            playlist_structure = "도입부 → 마무리"
            judgment_reason = "energy가 낮아 정점 없이 마무리로 연결"
        else:
            playlist_structure = "도입부 → 전개부 → 정점부 → 마무리"
            judgment_reason = "기본 구성"
        classified.append({
            "input_id": fact.get("input_id"),
            "원래_입력": fact,
            "음악_속성": music_props,
            "검색_파라미터": {"장르": fact.get("genre", []), "아티스트": fact.get("artist", [])},
            "playlist_structure": playlist_structure,
            "judgment_reason": judgment_reason
        })
    return classified

# Spotify OAuth
def get_spotify_client():
    try:
        from spotipy.oauth2 import SpotifyClientCredentials
        sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
            )
        )
        print("[Spotify] Client Credentials 로그인 성공")
        return sp
    except Exception as e:
        print(f"[Spotify] 실패: {e}")
        return None

# Spotify 후보곡 수집
def search_candidate_tracks(search_params, sp, mood):
    if not sp:
        print("[Spotify] fallback 곡 사용")
        return []
    collected_tracks = []
    genre_map = {
        "KPop": "k-pop", "k-pop": "k-pop", "JPop": "j-pop", "j-pop": "j-pop",
        "Pop": "pop", "pop": "pop", "알앤비": "r-n-b", "r&b": "r-n-b",
        "애니메이션": "anime", "anime": "anime", "힙합": "hip-hop", "hip-hop": "hip-hop",
        "랩": "rap", "rap": "rap", "인디": "indie", "indie": "indie"
    }
    mood_keywords = {
        "drive": ["drive", "night drive", "upbeat"],
        "workout": ["workout", "gym", "power"],
        "focus": ["focus", "study", "chill"],
        "sad": ["sad", "emotional", "ballad"],
        "excited": ["excited", "party", "dance", "energetic"],
        "shower": ["shower", "sing along", "feel good", "happy"],
        "study": ["study", "focus", "calm", "instrumental"],
        "sleep": ["sleep", "lullaby", "calm", "relax", "night"],
        "walk": ["walk", "stroll", "light", "breezy", "casual"],
        "rainy": ["rainy", "rain", "melancholy", "cozy", "grey"]
    }
    keywords = mood_keywords.get(mood, ["music"])
    # 아티스트 기반 검색
    for artist in search_params.get("아티스트", []):
        search_queries = [f"artist:{artist}", f"{artist} {random.choice(keywords)}", f"{artist} playlist", f"{artist} mix"]
        for query in search_queries:
            try:
                results = sp.search(q=query, type="track", limit=10)
                items = results["tracks"]["items"]
                for item in items:
                    collected_tracks.append({"id": item["id"], "name": item["name"], "artist": item["artists"][0]["name"], "popularity": item.get("popularity", 50)})
            except Exception as e:
                print(f"[Spotify] 아티스트 검색 실패: {e}")
                # Reraise any spotify search exceptions so caller can fallback to LLM
                raise
    # 장르 기반 검색
    for genre in search_params.get("장르", []):
        spotify_genre = genre_map.get(genre, genre.lower())
        genre_queries = [f"genre:{spotify_genre}", f"genre:{spotify_genre} {random.choice(keywords)}", f"{spotify_genre} playlist", f"{spotify_genre} mix"]
        for query in genre_queries:
            try:
                results = sp.search(q=query, type="track", limit=10)
                items = results["tracks"]["items"]
                for item in items:
                    collected_tracks.append({"id": item["id"], "name": item["name"], "artist": item["artists"][0]["name"], "popularity": item.get("popularity", 50)})
            except Exception as e:
                print(f"[Spotify] 장르 검색 실패: {e}")
                # Reraise any spotify search exceptions so caller can fallback to LLM
                raise
    # 중복 제거
    unique_tracks = {}
    for track in collected_tracks:
        unique_tracks[track["id"]] = track
    result_tracks = list(unique_tracks.values())
    print(f"[Spotify] 후보곡 수집 완료: {len(result_tracks)}곡")
    return result_tracks

# 외부 컨텍스트 수집
def fetch_external_context(search_params, music_props):
    sp = get_spotify_client()
    if not sp:
        print("[External] fallback 모드")
        return {"tracks": [], "status": "fallback", "sp": None}
    tracks = search_candidate_tracks(search_params, sp, music_props["mood"])
    print("[External] Spotify 데이터 수집 완료")
    return {"tracks": tracks, "status": "success", "sp": sp}

# 필터 병합 에이전트
def filter_tracks_by_situation(tracks, music_props, search_params):
    filtered = []
    for track in tracks:
        score = 0
        artist_text = (track["artist"].lower())
        track_name = (track["name"].lower())
        # 아티스트 우선
        for artist in search_params["아티스트"]:
            if artist.lower() in artist_text:
                score += 70
        # popularity 반영
        score += track.get("popularity", 50)
        # 상황별 키워드 반영
        if music_props["mood"] == "drive":
            drive_keywords = ["drive", "night", "highway"]
            for keyword in drive_keywords:
                if keyword in track_name:
                    score += 25
        elif music_props["mood"] == "workout":
            workout_keywords = ["power", "run", "fire"]
            for keyword in workout_keywords:
                if keyword in track_name:
                    score += 25
        # 랜덤성 강화
        score += random.randint(0, 50)
        track["score"] = score
        filtered.append(track)
    filtered.sort(key=lambda x: x["score"], reverse=True)
    top_tracks = filtered[:30]
    random.shuffle(top_tracks)
    return top_tracks

# 추천 이유 생성
def generate_reason(track, music_props, search_params):
    reasons = []
    artist_text = (track["artist"].lower())
    track_name = (track["name"].lower())
    # 아티스트 기반 추천
    for artist in search_params["아티스트"]:
        if artist.lower() in artist_text:
            artist_reasons = [f"{artist} 기반 추천", f"{artist} 스타일과 유사한 곡", f"{artist} 팬들이 자주 듣는 곡", f"{artist}와 분위기가 잘 어울리는 곡"]
            reasons.append(random.choice(artist_reasons))
    # popularity 기반 추천
    popularity = track.get("popularity", 50)
    if popularity >= 85:
        popularity_reasons = ["매우 인기 있는 곡", "최근 많이 재생되는 곡", "대중 반응이 좋은 곡"]
        reasons.append(random.choice(popularity_reasons))
    elif popularity >= 70:
        popularity_reasons = ["많이 재생된 인기곡", "플레이리스트에서 자주 추천되는 곡", "드라이브용으로 많이 선택되는 곡"]
        reasons.append(random.choice(popularity_reasons))
    elif popularity >= 50:
        popularity_reasons = ["대중적으로 자주 추천되는 곡", "안정적으로 분위기를 이어주는 곡", "무난하게 듣기 좋은 곡"]
        reasons.append(random.choice(popularity_reasons))
    # 드라이브 상황
    if music_props["mood"] == "drive":
        drive_reason_map = {
            "drive": ["드라이브 분위기와 잘 어울림", "차 안에서 듣기 좋은 분위기"],
            "night": ["야간 드라이브 감성과 어울림", "밤 분위기에 잘 맞는 곡"],
            "highway": ["속도감 있는 분위기의 곡", "고속도로 드라이브 느낌과 어울림"],
            "beat": ["리듬감 있는 드라이브 분위기", "비트감이 살아있는 곡"],
            "fire": ["에너지 넘치는 곡", "텐션을 끌어올리는 분위기"],
            "dance": ["신나는 분위기와 잘 어울림", "흥을 올려주는 스타일의 곡"],
            "up": ["텐션을 올려주는 곡", "활기찬 흐름을 만들어주는 곡"]
        }
        matched = False
        for keyword, reason_list in drive_reason_map.items():
            if keyword in track_name:
                reasons.append(random.choice(reason_list))
                matched = True
        if not matched:
            default_drive_reasons = ["드라이브 중 분위기를 이어주는 곡", "이동하면서 듣기 좋은 곡", "차 안 분위기와 잘 어울리는 곡", "주행 중 편하게 듣기 좋은 곡"]
            reasons.append(random.choice(default_drive_reasons))
    # 운동 상황
    elif music_props["mood"] == "workout":
        workout_reason_map = {"power": ["운동 텐션을 높여주는 곡", "강한 에너지가 느껴지는 곡"], "run": ["러닝과 잘 어울리는 곡", "박자감이 살아있는 곡"], "fire": ["에너지 넘치는 분위기", "운동 집중도를 올려주는 곡"]}
        matched = False
        for keyword, reason_list in workout_reason_map.items():
            if keyword in track_name:
                reasons.append(random.choice(reason_list))
                matched = True
        if not matched:
            default_workout_reasons = ["운동 분위기와 잘 어울리는 곡", "집중력을 올려주는 스타일의 곡", "활동적인 분위기에 적합한 곡"]
            reasons.append(random.choice(default_workout_reasons))
    # 집중 상황
    elif music_props["mood"] == "focus":
        focus_reasons = ["집중할 때 듣기 좋은 분위기", "잔잔하게 흐름을 유지해주는 곡", "공부할 때 부담 없이 듣기 좋은 곡"]
        reasons.append(random.choice(focus_reasons))
    # 슬픈 분위기
    elif music_props["mood"] == "sad":
        sad_reasons = ["감성적인 분위기와 잘 어울림", "잔잔한 감정을 이어주는 곡", "감정선과 어울리는 스타일의 곡"]
        reasons.append(random.choice(sad_reasons))
    # 신날 때
    if music_props["mood"] == "excited":
        excited_reasons = ["신나는 분위기와 잘 어울리는 곡", "텐션을 올려주는 곡"]
        reasons.append(random.choice(excited_reasons))
    # 씻을 때
    elif music_props["mood"] == "shower":
        shower_reasons = ["따라 부르기 좋은 곡", "기분 좋게 시작하는 곡"]
        reasons.append(random.choice(shower_reasons))
    # 공부할 때
    elif music_props["mood"] == "study":
        sleep_reasons = ["공부할 때 집중을 도와주는 곡", "잔잔하게 흐르는 곡"]
        reasons.append(random.choice(sleep_reasons))
    # 잠들기 전
    elif music_props["mood"] == "sleep":
        sleep_reasons = ["잠들기 좋은 잔잔한 곡", "편안하게 쉬게 해주는 곡"]
        reasons.append(random.choice(sleep_reasons))
    # 산책할 때
    elif music_props["mood"] == "walk":
        walk_reasons = ["산책 템포와 잘 맞는 곡", "걸으면서 듣기 좋은 곡"]
        reasons.append(random.choice(walk_reasons))
    # 비 오는 날
    elif music_props["mood"] == "rainy":
        rainy_reasons = ["비 오는 날 감성과 어울리는 곡", "창밖을 바라보며 듣기 좋은 곡"]
        reasons.append(random.choice(rainy_reasons))
    # 중복 제거
    reasons = list(dict.fromkeys(reasons))
    # fallback
    if not reasons:
        reasons.append("현재 분위기와 어울리는 곡")
    return " / ".join(reasons[:2])

# 플레이리스트 흐름 구성
def build_playlist_flow(tracks):
    if not tracks:
        return []
    random.shuffle(tracks)
    # Select up to 20 tracks initially
    selected_tracks = random.sample(tracks, min(20, len(tracks)))
    # Count tracks per artist
    artist_count = {}
    for track in selected_tracks:
        artist = track["artist"]
        artist_count[artist] = artist_count.get(artist, 0) + 1
    # Calculate maximum allowed tracks per artist
    max_tracks = len(selected_tracks) * 0.3
    # Filter tracks to ensure no artist exceeds 30%
    filtered_tracks = []
    artist_filtered_count = {}
    for track in selected_tracks:
        artist = track["artist"]
        if artist_filtered_count.get(artist, 0) < max_tracks:
            filtered_tracks.append(track)
            artist_filtered_count[artist] = artist_filtered_count.get(artist, 0) + 1
    # Ensure at least 5 tracks remain
    if len(filtered_tracks) < 5:
        filtered_tracks = selected_tracks[:5]
    # Print artist track counts
    print("[Playlist] 아티스트별 곡 수:")
    for artist, count in artist_filtered_count.items():
        print(f"{artist}: {count}곡")
    print(f"[Playlist] 최종 플레이리스트: {len(filtered_tracks)}곡")
    return filtered_tracks

# 출력 생성
def write_output(classified_items):
    outputs = []
    for item in classified_items:
        fact = item["원래_입력"]
        situation = fact.get("situation")
        outputs.append("\n===============================")
        outputs.append(f"{item['input_id']} 플레이리스트")
        outputs.append(f"상황: {situation}")
        outputs.append("===============================\n")
        candidate_tracks = item.get(
            "tracks",
            []
        )
        filtered_tracks = (filter_tracks_by_situation(candidate_tracks, item["음악_속성"], item["검색_파라미터"]))
        playlist = build_playlist_flow(filtered_tracks)
        for idx, track in enumerate(playlist, start=1):
            reason = generate_reason(track, item["음악_속성"], item["검색_파라미터"])
            outputs.append(f"{idx}. {track['artist']} - {track['name']}")
            outputs.append(f"   이유: {reason}\n")
    return "\n".join(outputs)

# 저장
def save_draft(text):
    file_path = Path("draft.md")
    file_path.write_text(text, encoding="utf-8")
    print(f"[Save] 저장 완료: {file_path}")

YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
YOUTUBE_TOKEN_PATH = "youtube_token.pickle"

def get_youtube_client():
    """YouTube OAuth 클라이언트를 반환합니다. 토큰 캐싱 지원."""
    creds = None
    # 기존 토큰 로드
    if os.path.exists(YOUTUBE_TOKEN_PATH):
        with open(YOUTUBE_TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)
    # 토큰 만료 시 갱신
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        secret_path = os.getenv("YOUTUBE_CLIENT_SECRET_PATH", "client_secret.json")
        if not os.path.exists(secret_path):
            print("[YouTube] client_secret.json 파일이 없습니다.")
            return None
        flow = InstalledAppFlow.from_client_secrets_file(secret_path, YOUTUBE_SCOPES)
        creds = flow.run_local_server(port=0)
        with open(YOUTUBE_TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)
    return build("youtube", "v3", credentials=creds)


def search_youtube_video(youtube, query):
    """곡명+아티스트로 YouTube 검색 후 첫 번째 video ID 반환. 없으면 None."""
    try:
        response = youtube.search().list(
            q=query,
            part="id",
            type="video",
            maxResults=1,
            videoCategoryId="10"  # Music 카테고리
        ).execute()
        items = response.get("items", [])
        if items:
            return items[0]["id"]["videoId"]
    except Exception as e:
        print(f"[YouTube] 검색 실패 ({query}): {e}")
    return None


def create_youtube_playlist(youtube, title, description=""):
    """YouTube 재생목록 생성 후 playlist ID 반환."""
    try:
        response = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description
                },
                "status": {"privacyStatus": "public"}  # "private"으로 바꿀 수도 있음
            }
        ).execute()
        playlist_id = response["id"]
        print(f"[YouTube] 재생목록 생성 완료: {title} (ID: {playlist_id})")
        return playlist_id
    except Exception as e:
        print(f"[YouTube] 재생목록 생성 실패: {e}")
        return None


def add_video_to_playlist(youtube, playlist_id, video_id):
    """video_id를 재생목록에 추가합니다."""
    try:
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        ).execute()
    except Exception as e:
        print(f"[YouTube] 영상 추가 실패 (video_id={video_id}): {e}")


def export_playlist_to_youtube(classified_items, playlist_title=None):
    """
    classified_items의 최종 추천곡들을 YouTube 재생목록으로 내보냅니다.
    재생목록 URL을 반환합니다.
    """
    youtube = get_youtube_client()
    if not youtube:
        print("[YouTube] 인증 실패로 내보내기를 건너뜁니다.")
        return None

    # 전체 곡 목록 수집
    all_tracks = []
    for item in classified_items:
        situation = item.get("원래_입력", {}).get("situation", "")
        tracks = item.get("tracks", [])
        music_props = item.get("음악_속성", {})
        params = item.get("검색_파라미터", {})
        filtered = filter_tracks_by_situation(tracks, music_props, params)
        playlist = build_playlist_flow(filtered)
        for track in playlist:
            all_tracks.append({
                "name": track.get("name", ""),
                "artist": track.get("artist", ""),
                "situation": situation
            })

    if not all_tracks:
        print("[YouTube] 내보낼 곡이 없습니다.")
        return None

    # 재생목록 생성
    if not playlist_title:
        situations = list({t["situation"] for t in all_tracks})
        playlist_title = f"AI 추천 플레이리스트 - {', '.join(situations)}"

    playlist_id = create_youtube_playlist(
        youtube,
        title=playlist_title,
        description="my_agent.py가 생성한 AI 추천 플레이리스트입니다."
    )
    if not playlist_id:
        return None

    # 각 곡 검색 후 추가
    added = 0
    for track in all_tracks:
        query = f"{track['artist']} {track['name']}"
        print(f"[YouTube] 검색 중: {query}")
        video_id = search_youtube_video(youtube, query)
        if video_id:
            add_video_to_playlist(youtube, playlist_id, video_id)
            added += 1
            print(f"[YouTube] 추가 완료: {track['artist']} - {track['name']}")
        else:
            print(f"[YouTube] 영상 없음 (건너뜀): {query}")

    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    print(f"\n[YouTube] 총 {added}곡 추가 완료")
    print(f"[YouTube] 재생목록 URL: {url}")
    return url

def write_playlist_guides(classified_items):
    """
    classified_items를 받아 상황별 Markdown 문자열을 생성하여 반환합니다.
    각 상황별로 다음을 포함합니다:
      - 상황 제목 (input_id — situation)
      - 추천 플레이리스트 (곡 목록 + 각 곡 이유 한 줄)
      - 구성 계획과 판단 근거
      - 주의할 점
    """
    sections = []
    if not classified_items:
        return "# 사용자 가이드\n\n입력된 상황 정보가 없습니다."
    for item in classified_items:
        fact = item.get("원래_입력", {})
        input_id = item.get("input_id", "[입력]")
        situation = fact.get("situation", "알 수 없음")
        header = f"## {input_id} — {situation}\n"
        # 구성 계획 및 판단 근거
        playlist_structure = item.get("playlist_structure", "")
        judgment_reason = item.get("judgment_reason", "")
        # 외부 데이터 수집 및 플레이리스트 생성
        tracks = item.get(
            "tracks",
            []
        )
        # 기본 섹션 시작
        section_lines = [header]
        section_lines.append("### 추천 플레이리스트\n")
        if not tracks:
            section_lines.append("외부 데이터 없음\n")
        else:
            filtered_tracks = filter_tracks_by_situation(tracks, item.get("음악_속성", {}), item.get("검색_파라미터", {}))
            playlist = build_playlist_flow(filtered_tracks)
            if not playlist:
                section_lines.append("외부 데이터 없음\n")
            else:
                for idx, track in enumerate(playlist, start=1):
                    reason = generate_reason(track, item.get("음악_속성", {}), item.get("검색_파라미터", {}))
                    title = track.get("name", "제목 미상")
                    artist = track.get("artist", "아티스트 미상")
                    section_lines.append(f"{idx}. {artist} - {title}  \n   이유: {reason}  \n")
                # 곡 수 부족 안내
                if len(playlist) < 5:
                    section_lines.append(f"\n> 안내: 추천된 곡 수가 적습니다. 현재 {len(playlist)}곡입니다. 장르나 아티스트를 추가하면 더 많은 추천을 받을 수 있습니다.\n")
        # 구성 계획 및 판단 근거 표시
        section_lines.append("\n### 구성 계획")
        section_lines.append(f"- {playlist_structure}  \n- 판단 근거: {judgment_reason}\n")
        # 주의할 점
        section_lines.append("\n### 주의할 점\n")
        section_lines.append("- 입력 자료에 없는 정보(예: 사용자 연령, 세부 취향, 지역 제한 등)는 단정하지 않습니다.\n")
        section_lines.append("- 추천은 외부 메타데이터(예: Spotify) 기반이며 지역/권한에 따라 일부 곡이 재생되지 않을 수 있습니다.\n")
        section_lines.append("- 플레이리스트는 제안이며 실제 선호도에 따라 조정이 필요할 수 있습니다.\n")
        sections.append("\n".join(section_lines))
    return "\n\n".join(sections)

def save_user_guides(guides, path="output_user_guide.md"):
    """
    guides 문자열을 UTF-8로 파일에 저장합니다. 저장 성공 시 경로를 출력합니다.
    """
    if isinstance(guides, list):
        content = "\n\n".join(guides)
    else:
        content = guides or ""
    try:
        p = Path(path)
        p.write_text(content, encoding="utf-8")
        print(f"[Save] 사용자 가이드 저장 완료: {p}")
        return str(p)
    except Exception as e:
        print(f"[Save] 사용자 가이드 저장 실패: {e}")
        raise


def spotify_recommend_agent(item):
    """Spotify로 후보곡을 수집합니다. 성공 시 tracks 리스트를 반환합니다."""
    try:
        sp = get_spotify_client()
        if not sp:
            raise RuntimeError("Spotify client not available")
        params = item.get("검색_파라미터", {})
        music_props = item.get("음악_속성", {})
        tracks = search_candidate_tracks(params, sp, music_props.get("mood"))
        return {"tracks": tracks, "status": "spotify", "sp": sp}
    except Exception as e:
        print(f"[Recommend][Spotify] 실패: {e}")
        # Raise so recommend_agent can fall back to LLM
        raise


def llm_recommend_agent(item):
    """Groq LLM으로 곡 추천을 시도합니다. 실패 시 예외를 던집니다."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY 없음")
    try:
        client = Groq(api_key=api_key)
        prompt = f"""
당신은 플레이리스트 곡 추천 도우미입니다. 아래 입력 정보를 바탕으로 최대 10개의 트랙을 JSON 리스트로 반환하세요.
- 각 항목은 {{"id":"...", "name":"...", "artist":"...", "popularity": 50}} 형태여야 합니다.
- 절대로 새로운 상황을 생성하지 마십시오. 오직 주어진 입력(장르/아티스트/상황)에 근거해 추천만 하세요.

입력 항목:\n{item}
"""
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content
        # 기대: content는 JSON 리스트
        tracks = json.loads(content)
        return {"tracks": tracks, "status": "groq"}
    except Exception as e:
        print(f"[Recommend][Groq] 실패: {e}")
        raise


def rule_recommend_agent(item):
    """간단한 규칙 기반 샘플 트랙을 반환합니다."""
    # 하드코딩된 샘플 (최소한의 메타데이터)
    sample = [
        {"id": "rule-1", "name": "Sample Song 1", "artist": "Sample Artist", "popularity": 50},
        {"id": "rule-2", "name": "Sample Song 2", "artist": "Sample Artist", "popularity": 45},
        {"id": "rule-3", "name": "Sample Song 3", "artist": "Another Artist", "popularity": 40},
        {"id": "rule-4", "name": "Sample Song 4", "artist": "Another Artist", "popularity": 35},
        {"id": "rule-5", "name": "Sample Song 5", "artist": "Various", "popularity": 30}
    ]
    return {"tracks": sample, "status": "rule"}


def recommend_agent(item):
    """통합 추천 엔트리: spotify -> groq -> rule 폴백 체인.
    항상 {'tracks': [...], 'status': 'spotify'|'groq'|'rule'} 형태를 반환합니다.
    """
    # 1) Spotify
    try:
        res_sp = spotify_recommend_agent(item)
        if res_sp.get("tracks"):
            return res_sp
    except Exception:
        pass
    # 2) Groq LLM
    try:
        res_groq = llm_recommend_agent(item)
        if res_groq.get("tracks"):
            return res_groq
    except Exception:
        pass
    # 3) 규칙 기반
    return rule_recommend_agent(item)



def review_guides_with_rules(guides_md: str) -> str:
    """
    기존 규칙 기반 검토를 수행하고 Markdown 형식의 review_report 문자열을 반환합니다.
    """
    import re
    issues = []
    if not guides_md or not isinstance(guides_md, str):
        return "# 가이드 검토 결과\n\n**요약:** 검토 불가\n\n- 이유: 가이드 내용이 비어있습니다.\n"

    text = guides_md
    # 1) 주의할 점 섹션 존재 여부
    if "주의할 점" not in text:
        issues.append("'주의할 점' 섹션이 없습니다.")
    sections = re.split(r"^##\s+", text, flags=re.MULTILINE)
    low_count_sections = []
    for sec in sections[1:]:
        title_line = sec.splitlines()[0] if sec.splitlines() else "(제목 없음)"
        track_lines = re.findall(r"^\s*\d+\.\s", sec, flags=re.MULTILINE)
        if len(track_lines) < 5:
            low_count_sections.append((title_line.strip(), len(track_lines)))
    if low_count_sections:
        for title, cnt in low_count_sections:
            issues.append(f"섹션 '{title}'의 추천 곡 수가 적습니다: {cnt}곡 (권장 5곡 이상)")

    # 3) 단정적 표현 검사
    strong_words = ["반드시", "확실히", "항상", "절대", "반드시는"]
    found_strong = [w for w in strong_words if w in text]
    if found_strong:
        issues.append(f"단정적 표현 발견: {', '.join(found_strong)}")

    # 추가 검사: 추천 이유 존재 여부, 추천곡 확인 가능 여부, 상황 반영 여부, 주의사항 포함 여부
    # (간단 체크: 키워드 존재/문장 길이 기반의 약한 검사)
    if "이유:" not in text and "이유" not in text:
        issues.append("추천 이유가 충분히 제공되지 않았을 수 있습니다.")
    # 추천곡 확인 가능 여부: 숫자 목록 존재여부
    total_tracks = len(re.findall(r"^\s*\d+\.\s", text, flags=re.MULTILINE))
    if total_tracks == 0:
        issues.append("추천된 곡 목록을 확인할 수 없습니다.")
    # 상황 반영 여부: 간단히 '상황' 또는 known moods 확인
    known_moods = ["드라이브", "운동", "집중", "슬플 때", "신날 때", "씻을 때", "공부할 때", "잠들기 전", "산책할 때", "비 오는 날"]
    if not any(m in text for m in known_moods):
        issues.append("상황(예: 드라이브, 공부 등)이 가이드에 명확히 반영되지 않았을 수 있습니다.")

    passed = len(issues) == 0
    # Build markdown report
    lines = ["# 가이드 검토 결과", ""]
    lines.append(f"**요약:** {'통과' if passed else '검토 필요'}")
    lines.append("")
    if issues:
        lines.append("## 발견된 이슈")
        for it in issues:
            lines.append(f"- {it}")
        lines.append("")
    else:
        lines.append("- 없음")
        lines.append("")
    return "\n".join(lines)


def review_guides_with_groq(guides_md: str) -> str:
    """
    Groq API를 사용한 보조 검토자. 실패 시 예외를 던집니다.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY 없음")
    client = Groq(api_key=api_key)
    prompt = f"""
당신은 플레이리스트 가이드의 검토자입니다. 다음 조건을 준수하세요:
- 절대로 입력에 없는 새로운 추천곡이나 새로운 상황을 생성하지 마십시오.
- 오직 주어진 가이드 문서의 품질(명확성, 이유의 충분성, 상황 반영 등)을 평가하세요.
- 아래의 검토 기준(1~7)을 모두 다루어 간결한 Markdown 보고서를 작성하세요.

검토 기준:
1. 플레이리스트 추천 결과에 입력 자료에 없는 내용을 단정했는가
2. 추천 이유가 부족하거나 모호한가
3. 사용자가 어떤 곡을 추천받았는지 확인 가능한가
4. 상황(드라이브, 공부, 운동 등)이 명확하게 반영되었는가
5. "반드시", "항상", "절대", "확실히" 같은 단정 표현이 있는가
6. 플레이리스트 곡 수가 너무 적지는 않은가
7. 주의사항 또는 참고사항이 포함되어 있는가

가이드 문서:
"""
    prompt += """\n""" + guides_md + """\n"""
    try:
        response = client.chat.completions.create(
            model=GROQ_REVIEW_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("Groq 응답이 비어있음")
        return content
    except Exception as e:
        raise


def review_guides_with_openai(guides_md: str) -> str:
    """
    OpenAI를 사용한 보조 검토자. 실패 시 예외를 던집니다.
    """
    try:
        import openai
    except Exception:
        raise RuntimeError("openai 패키지가 설치되어 있지 않음")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 없음")
    openai.api_key = api_key
    prompt = f"""
당신은 플레이리스트 가이드의 검토자입니다. 다음 조건을 준수하세요:
- 절대로 입력에 없는 새로운 추천곡이나 새로운 상황을 생성하지 마십시오.
- 오직 주어진 가이드 문서의 품질(명확성, 이유의 충분성, 상황 반영 등)을 평가하세요.
- 아래의 검토 기준(1~7)을 모두 다루어 간결한 Markdown 보고서를 작성하세요.

검토 기준:
1. 플레이리스트 추천 결과에 입력 자료에 없는 내용을 단정했는가
2. 추천 이유가 부족하거나 모호한가
3. 사용자가 어떤 곡을 추천받았는지 확인 가능한가
4. 상황(드라이브, 공부, 운동 등)이 명확하게 반영되었는가
5. "반드시", "항상", "절대", "확실히" 같은 단정 표현이 있는가
6. 플레이리스트 곡 수가 너무 적지는 않은가
7. 주의사항 또는 참고사항이 포함되어 있는가

가이드 문서:
"""
    prompt += """\n""" + guides_md + """\n"""
    try:
        resp = openai.ChatCompletion.create(
            model=OPENAI_REVIEW_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800
        )
        content = resp.choices[0].message.content
        if not content:
            raise RuntimeError("OpenAI 응답이 비어있음")
        return content
    except Exception as e:
        raise


def review_guides(guides_md: str) -> str:
    """
    검토 엔트리: USE_LLM_REVIEW 플래그에 따라 Groq -> OpenAI -> Rules 폴백 체인을 실행하고
    항상 Markdown 문자열(report)만 반환합니다.
    """
    if not guides_md or not isinstance(guides_md, str):
        return "# 가이드 검토 결과\n\n**요약:** 검토 불가\n\n- 이유: 가이드 내용이 비어있습니다.\n"

    if USE_LLM_REVIEW:
        # 1) Groq
        try:
            return review_guides_with_groq(guides_md)
        except Exception:
            # fallback to OpenAI
            try:
                return review_guides_with_openai(guides_md)
            except Exception:
                # final fallback to rules
                return review_guides_with_rules(guides_md)
    else:
        return review_guides_with_rules(guides_md)


def save_review_report(review_report: str, path="review_report.md"):
    """
    review_report 문자열(Markdown)을 파일에 저장하고 경로를 반환합니다.
    """
    try:
        p = Path(path)
        p.write_text(review_report or "", encoding="utf-8")
        print(f"[Save] 검토 리포트 저장: {p}")
        return str(p)
    except Exception as e:
        print(f"[Save] 검토 리포트 저장 실패: {e}")
        raise

# MAIN
def main():
    # 간단 입력: 상황, 장르, 아티스트를 바로 입력받습니다.
    user_situation = input("상황 입력: ")
    user_genres = input("장르 입력 (쉼표 구분): ")
    user_artists = input("아티스트 입력 (쉼표 구분): ")
    # 사용자 입력이 비어있어도 그대로 진행합니다 (SAMPLE_INPUT으로 대체하지 않음)
    local_sample_input = f"""
[입력]
- 상황: {user_situation}
- 장르: {user_genres}
- 아티스트: {user_artists}
"""
    print("\n--- 입력 분석 에이전트 ---")
    facts = extract_facts(local_sample_input)
    for fact in facts:
        print(fact)
    print("\n--- 상황 분석 에이전트 ---")
    classified_items = classify_items(facts)
    for item in classified_items:
        # 후보곡 수집: recommend_agent를 사용
        rec = recommend_agent(item)
        item["tracks"] = rec.get("tracks", [])
    for item in classified_items:
        print(item)
        print(f"구성 계획: {item['playlist_structure']}")
        print(f"판단 근거: {item['judgment_reason']}")
    approval = input("\n플레이리스트를 생성할까요? (y/n): ")
    if approval.strip().lower() != "y":
        print("생성을 취소했습니다.")
        return
    print("\n--- 플레이리스트 생성 ---")
    output = write_output(classified_items)
    print(output)
    # 추가: 상황별 Markdown 가이드 생성 및 저장
    guides_md = write_playlist_guides(classified_items)
    save_user_guides(guides_md)
    # 가이드 검토 후 리포트 저장
    try:
        review_result = review_guides(guides_md)
        print("[Review] 검토 결과:", review_result)
        try:
            saved_report = save_review_report(review_result, path="review_report.md")
            print(f"[Review] 리포트 저장 완료: {saved_report}")
        except Exception as e:
            print(f"[Review] 리포트 저장 실패: {e}")
    except Exception as e:
        print(f"[Review] 검토 실행 실패: {e}")
    while True:
        print("\n--- 사용자 선택 ---")
        print("1. 저장 후 종료")
        print("2. 같은 조건으로 다시 생성")
        print("3. 장르/아티스트 수정")
        choice = input("선택 입력 (1/2/3): ").strip()
        if choice == "1":
            save_draft(output)
            # ✅ YouTube 내보내기 추가
            yt_choice = input("YouTube 재생목록으로 내보내시겠습니까? (y/n): ").strip().lower()
            if yt_choice == "y":
                yt_title = input("재생목록 이름 입력 (엔터 시 자동 생성): ").strip() or None
                export_playlist_to_youtube(classified_items, playlist_title=yt_title)
            print("프로그램 종료")
            return
        elif choice == "2":
            print("\n같은 조건으로 재생성")
            output = write_output(classified_items)
            print(output)
        elif choice == "3":
            print("\n장르/아티스트 수정")
            for fact in facts:
                new_genres = input(f"{fact['input_id']} 새 장르 입력 (쉼표 구분): ")
                new_artists = input(f"{fact['input_id']} 새 아티스트 입력 (쉼표 구분): ")
                fact["genre"] = [g.strip() for g in new_genres.split(",")]
                fact["artist"] = [a.strip() for a in new_artists.split(",")]
            classified_items = classify_items(facts)
            # Spotify 결과 다시 수집
            for item in classified_items:
                # 후보곡 수집: recommend_agent를 사용
                rec = recommend_agent(item)
                item["tracks"] = rec.get("tracks", [])
            output = write_output(classified_items)
            print(output)
            guides_md = write_playlist_guides(classified_items)
            save_user_guides(guides_md)

            review_result = review_guides(guides_md)
            print("[Review] 검토 결과:", review_result)

            save_review_report(review_result)
        else:
            print("잘못된 입력")

# 실행
if __name__ == "__main__":
    main()