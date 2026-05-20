from pathlib import Path
import os
import json
import random
import spotipy

from groq import Groq
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

# =========================================================
# 설정
# =========================================================

USE_LLM = False

# =========================================================
# SAMPLE INPUT
# =========================================================

SAMPLE_INPUT = """
[입력 1]
- 상황: 드라이브
- 장르: k-pop
- 아티스트: NCT WISH, RIIZE
"""

# =========================================================
# 입력 분석 에이전트 (규칙 기반)
# =========================================================

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

                fact["situation"] = (
                    line.replace("- 상황:", "").strip()
                )

            elif line.startswith("- 장르:"):

                fact["genre"] = [

                    g.strip()

                    for g in line.replace(
                        "- 장르:",
                        ""
                    ).split(",")

                ]

            elif line.startswith("- 아티스트:"):

                fact["artist"] = [

                    a.strip()

                    for a in line.replace(
                        "- 아티스트:",
                        ""
                    ).split(",")

                ]

        if fact:
            results.append(fact)

    return results

# =========================================================
# 입력 분석 에이전트 (Groq)
# =========================================================

def analyze_with_groq(text):

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:

        raise ValueError(
            "GROQ_API_KEY 환경변수 없음"
        )

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

입력:
{text}
"""

    response = client.chat.completions.create(

        model="llama3-8b-8192",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    result = response.choices[0].message.content

    return json.loads(result)

# =========================================================
# 입력 분석 통합
# =========================================================

def extract_facts(text):

    if USE_LLM:

        try:

            print("[LLM] 입력 분석 실행")

            return analyze_with_groq(text)

        except Exception as e:

            print(f"[LLM] 실패: {e}")

            print(
                "[LLM] 규칙 기반 분석으로 fallback"
            )

    print("[Rules] 규칙 기반 분석 실행")

    return analyze_with_rules(text)

# =========================================================
# 상황 분석 에이전트
# =========================================================

def classify_items(facts):

    mapping = {

        "드라이브": {

            "mood": "drive",
            "energy": "high"
        },

        "운동": {

            "mood": "workout",
            "energy": "very_high"
        },

        "집중": {

            "mood": "focus",
            "energy": "low"
        },

        "슬플 때": {

            "mood": "sad",
            "energy": "low"
        },

        "신날 때": {

            "mood": "excited",
            "energy": "very_high"
        },

        "씻을 때": {

            "mood": "shower",
            "energy": "medium"
        },

        "공부할 때": {

            "mood": "study",
            "energy": "low"
        },

        "잠들기 전": {

            "mood": "sleep",
            "energy": "very_low"
        },

        "산책할 때": {

            "mood": "walk",
            "energy": "medium"
        },

        "비 오는 날": {

            "mood": "rainy",
            "energy": "low"
        }
    }

    classified = []

    for fact in facts:

        situation = fact.get("situation", "")

        music_props = mapping.get(

            situation,

            {
                "mood": "default",
                "energy": "medium"
            }
        )

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

            "검색_파라미터": {

                "장르": fact.get("genre", []),

                "아티스트": fact.get("artist", [])
            },

            "playlist_structure": playlist_structure,

            "judgment_reason": judgment_reason
        })

    return classified

# =========================================================
# Spotify OAuth
# =========================================================

def get_spotify_client():

    try:

        sp = spotipy.Spotify(

            auth_manager=SpotifyOAuth(

                client_id=os.getenv(
                    "SPOTIFY_CLIENT_ID"
                ),

                client_secret=os.getenv(
                    "SPOTIFY_CLIENT_SECRET"
                ),

                redirect_uri=os.getenv(
                    "SPOTIFY_REDIRECT_URI"
                ),

                scope="playlist-modify-public"
            )
        )

        print("[Spotify OAuth] 로그인 성공")

        return sp

    except Exception as e:

        print(
            f"[Spotify OAuth] 실패: {e}"
        )

        return None

# =========================================================
# Spotify 후보곡 수집
# =========================================================

def search_candidate_tracks(
    search_params,
    sp,
    mood
):

    if not sp:

        print("[Spotify] fallback 곡 사용")

        return []

    collected_tracks = []

    genre_map = {

        "KPop": "k-pop",
        "k-pop": "k-pop",

        "JPop": "j-pop",
        "j-pop": "j-pop",

        "Pop": "pop",
        "pop": "pop",

        "알앤비": "r-n-b",
        "r&b": "r-n-b",

        "애니메이션": "anime",
        "anime": "anime",

        "힙합": "hip-hop",
        "hip-hop": "hip-hop",

        "랩": "rap",
        "rap": "rap",

        "인디": "indie",
        "indie": "indie"
    }

    mood_keywords = {

        "drive": [
            "drive",
            "night drive",
            "upbeat"
        ],

        "workout": [
            "workout",
            "gym",
            "power"
        ],

        "focus": [
            "focus",
            "study",
            "chill"
        ],

        "sad": [
            "sad",
            "emotional",
            "ballad"
        ],

        "excited": [
            "excited",
            "party",
            "dance",
            "energetic"
        ],

        "shower": [
            "shower",
            "sing along",
            "feel good",
            "happy"
        ],

        "study": [
            "study",
            "focus",
            "calm",
            "instrumental"
        ],

        "sleep": [
            "sleep",
            "lullaby",
            "calm",
            "relax",
            "night"
        ],

        "walk": [
            "walk",
            "stroll",
            "light",
            "breezy",
            "casual"
        ],

        "rainy": [
            "rainy",
            "rain",
            "melancholy",
            "cozy",
            "grey"
        ]
    }

    keywords = mood_keywords.get(
        mood,
        ["music"]
    )

    # -----------------------------------------------------
    # 아티스트 기반 검색
    # -----------------------------------------------------

    for artist in search_params.get(
        "아티스트",
        []
    ):

        search_queries = [

            f"artist:{artist}",

            f"{artist} {random.choice(keywords)}",

            f"{artist} playlist",

            f"{artist} mix"
        ]

        for query in search_queries:

            try:

                results = sp.search(

                    q=query,

                    type="track",

                    limit=10
                )

                items = results["tracks"]["items"]

                for item in items:

                    collected_tracks.append({

                        "id": item["id"],

                        "name": item["name"],

                        "artist": item["artists"][0]["name"],

                        "popularity": item.get(
                            "popularity",
                            50
                        )
                    })

            except Exception as e:

                print(
                    f"[Spotify] 아티스트 검색 실패: {e}"
                )

    # -----------------------------------------------------
    # 장르 기반 검색
    # -----------------------------------------------------

    for genre in search_params.get(
        "장르",
        []
    ):

        spotify_genre = genre_map.get(
            genre,
            genre.lower()
        )

        genre_queries = [

            f"genre:{spotify_genre}",

            f"genre:{spotify_genre} "
            f"{random.choice(keywords)}",

            f"{spotify_genre} playlist",

            f"{spotify_genre} mix"
        ]

        for query in genre_queries:

            try:

                results = sp.search(

                    q=query,

                    type="track",

                    limit=10
                )

                items = results["tracks"]["items"]

                for item in items:

                    collected_tracks.append({

                        "id": item["id"],

                        "name": item["name"],

                        "artist": item["artists"][0]["name"],

                        "popularity": item.get(
                            "popularity",
                            50
                        )
                    })

            except Exception as e:

                print(
                    f"[Spotify] 장르 검색 실패: {e}"
                )

    # -----------------------------------------------------
    # 중복 제거
    # -----------------------------------------------------

    unique_tracks = {}

    for track in collected_tracks:

        unique_tracks[track["id"]] = track

    result_tracks = list(
        unique_tracks.values()
    )

    print(
        f"[Spotify] 후보곡 수집 완료: "
        f"{len(result_tracks)}곡"
    )

    return result_tracks

# =========================================================
# 외부 컨텍스트 수집
# =========================================================

def fetch_external_context(
    search_params,
    music_props
):

    sp = get_spotify_client()

    if not sp:

        print("[External] fallback 모드")

        return {

            "tracks": [],

            "status": "fallback",

            "sp": None
        }

    tracks = search_candidate_tracks(

        search_params,

        sp,

        music_props["mood"]
    )

    print("[External] Spotify 데이터 수집 완료")

    return {

        "tracks": tracks,

        "status": "success",

        "sp": sp
    }

# =========================================================
# 필터 병합 에이전트
# =========================================================

def filter_tracks_by_situation(
    tracks,
    music_props,
    search_params
):

    filtered = []

    for track in tracks:

        score = 0

        artist_text = (
            track["artist"].lower()
        )

        track_name = (
            track["name"].lower()
        )

        # -------------------------------------------------
        # 아티스트 우선
        # -------------------------------------------------

        for artist in search_params["아티스트"]:

            if artist.lower() in artist_text:

                score += 70

        # -------------------------------------------------
        # popularity 반영
        # -------------------------------------------------

        score += track.get(
            "popularity",
            50
        )

        # -------------------------------------------------
        # 상황별 키워드 반영
        # -------------------------------------------------

        if music_props["mood"] == "drive":

            drive_keywords = [
                "drive",
                "night",
                "highway"
            ]

            for keyword in drive_keywords:

                if keyword in track_name:

                    score += 25

        elif music_props["mood"] == "workout":

            workout_keywords = [
                "power",
                "run",
                "fire"
            ]

            for keyword in workout_keywords:

                if keyword in track_name:

                    score += 25

        # -------------------------------------------------
        # 랜덤성 강화
        # -------------------------------------------------

        score += random.randint(0, 50)

        track["score"] = score

        filtered.append(track)

    filtered.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    top_tracks = filtered[:30]

    random.shuffle(top_tracks)

    return top_tracks

# =========================================================
# 추천 이유 생성
# =========================================================

def generate_reason(
    track,
    music_props,
    search_params
):

    reasons = []

    artist_text = (
        track["artist"].lower()
    )

    track_name = (
        track["name"].lower()
    )

    # -----------------------------------------------------
    # 아티스트 기반 추천
    # -----------------------------------------------------

    for artist in search_params["아티스트"]:

        if artist.lower() in artist_text:

            artist_reasons = [

                f"{artist} 기반 추천",

                f"{artist} 스타일과 유사한 곡",

                f"{artist} 팬들이 자주 듣는 곡",

                f"{artist}와 분위기가 잘 어울리는 곡"
            ]

            reasons.append(
                random.choice(artist_reasons)
            )

    # -----------------------------------------------------
    # popularity 기반 추천
    # -----------------------------------------------------

    popularity = track.get(
        "popularity",
        50
    )

    if popularity >= 85:

        popularity_reasons = [

            "매우 인기 있는 곡",

            "최근 많이 재생되는 곡",

            "대중 반응이 좋은 곡"
        ]

        reasons.append(
            random.choice(popularity_reasons)
        )

    elif popularity >= 70:

        popularity_reasons = [

            "많이 재생된 인기곡",

            "플레이리스트에서 자주 추천되는 곡",

            "드라이브용으로 많이 선택되는 곡"
        ]

        reasons.append(
            random.choice(popularity_reasons)
        )

    elif popularity >= 50:

        popularity_reasons = [

            "대중적으로 자주 추천되는 곡",

            "안정적으로 분위기를 이어주는 곡",

            "무난하게 듣기 좋은 곡"
        ]

        reasons.append(
            random.choice(popularity_reasons)
        )

    # -----------------------------------------------------
    # 드라이브 상황
    # -----------------------------------------------------

    if music_props["mood"] == "drive":

        drive_reason_map = {

            "drive": [
                "드라이브 분위기와 잘 어울림",
                "차 안에서 듣기 좋은 분위기"
            ],

            "night": [
                "야간 드라이브 감성과 어울림",
                "밤 분위기에 잘 맞는 곡"
            ],

            "highway": [
                "속도감 있는 분위기의 곡",
                "고속도로 드라이브 느낌과 어울림"
            ],

            "beat": [
                "리듬감 있는 드라이브 분위기",
                "비트감이 살아있는 곡"
            ],

            "fire": [
                "에너지 넘치는 곡",
                "텐션을 끌어올리는 분위기"
            ],

            "dance": [
                "신나는 분위기와 잘 어울림",
                "흥을 올려주는 스타일의 곡"
            ],

            "up": [
                "텐션을 올려주는 곡",
                "활기찬 흐름을 만들어주는 곡"
            ]
        }

        matched = False

        for keyword, reason_list in drive_reason_map.items():

            if keyword in track_name:

                reasons.append(
                    random.choice(reason_list)
                )

                matched = True

        if not matched:

            default_drive_reasons = [

                "드라이브 중 분위기를 이어주는 곡",

                "이동하면서 듣기 좋은 곡",

                "차 안 분위기와 잘 어울리는 곡",

                "주행 중 편하게 듣기 좋은 곡"
            ]

            reasons.append(
                random.choice(
                    default_drive_reasons
                )
            )

    # -----------------------------------------------------
    # 운동 상황
    # -----------------------------------------------------

    elif music_props["mood"] == "workout":

        workout_reason_map = {

            "power": [
                "운동 텐션을 높여주는 곡",
                "강한 에너지가 느껴지는 곡"
            ],

            "run": [
                "러닝과 잘 어울리는 곡",
                "박자감이 살아있는 곡"
            ],

            "fire": [
                "에너지 넘치는 분위기",
                "운동 집중도를 올려주는 곡"
            ]
        }

        matched = False

        for keyword, reason_list in workout_reason_map.items():

            if keyword in track_name:

                reasons.append(
                    random.choice(reason_list)
                )

                matched = True

        if not matched:

            default_workout_reasons = [

                "운동 분위기와 잘 어울리는 곡",

                "집중력을 올려주는 스타일의 곡",

                "활동적인 분위기에 적합한 곡"
            ]

            reasons.append(
                random.choice(
                    default_workout_reasons
                )
            )

    # -----------------------------------------------------
    # 집중 상황
    # -----------------------------------------------------

    elif music_props["mood"] == "focus":

        focus_reasons = [

            "집중할 때 듣기 좋은 분위기",

            "잔잔하게 흐름을 유지해주는 곡",

            "공부할 때 부담 없이 듣기 좋은 곡"
        ]

        reasons.append(
            random.choice(focus_reasons)
        )

    # -----------------------------------------------------
    # 슬픈 분위기
    # -----------------------------------------------------

    elif music_props["mood"] == "sad":

        sad_reasons = [

            "감성적인 분위기와 잘 어울림",

            "잔잔한 감정을 이어주는 곡",

            "감정선과 어울리는 스타일의 곡"
        ]

        reasons.append(
            random.choice(sad_reasons)
        )

    # -----------------------------------------------------
    # 신날 때
    # -----------------------------------------------------
    if music_props["mood"] == "excited":
        excited_reasons = [
            "신나는 분위기와 잘 어울리는 곡",
            "텐션을 올려주는 곡"
        ]
        reasons.append(random.choice(excited_reasons))

    # -----------------------------------------------------
    # 씻을 때
    # -----------------------------------------------------
    elif music_props["mood"] == "shower":
        shower_reasons = [
            "따라 부르기 좋은 곡",
            "기분 좋게 시작하는 곡"
        ]
        reasons.append(random.choice(shower_reasons))

    # -----------------------------------------------------
    # 공부할 때
    # -----------------------------------------------------
    elif music_props["mood"] == "study":
        sleep_reasons = [
            "공부할 때 집중을 도와주는 곡",
            "잔잔하게 흐르는 곡"
        ]
        reasons.append(random.choice(sleep_reasons))

    # -----------------------------------------------------
    # 잠들기 전
    # -----------------------------------------------------
    elif music_props["mood"] == "sleep":
        sleep_reasons = [
            "잠들기 좋은 잔잔한 곡",
            "편안하게 쉬게 해주는 곡"
        ]
        reasons.append(random.choice(sleep_reasons))

    # -----------------------------------------------------
    # 산책할 때
    # -----------------------------------------------------
    elif music_props["mood"] == "walk":
        walk_reasons = [
            "산책 템포와 잘 맞는 곡",
            "걸으면서 듣기 좋은 곡"
        ]
        reasons.append(random.choice(walk_reasons))

    # -----------------------------------------------------
    # 비 오는 날
    # -----------------------------------------------------
    elif music_props["mood"] == "rainy":
        rainy_reasons = [
            "비 오는 날 감성과 어울리는 곡",
            "창밖을 바라보며 듣기 좋은 곡"
        ]
        reasons.append(random.choice(rainy_reasons))

    # -----------------------------------------------------
    # 중복 제거
    # -----------------------------------------------------

    reasons = list(dict.fromkeys(reasons))

    # -----------------------------------------------------
    # fallback
    # -----------------------------------------------------

    if not reasons:

        reasons.append(
            "현재 분위기와 어울리는 곡"
        )

    return " / ".join(reasons[:2])

# =========================================================
# 플레이리스트 흐름 구성
# =========================================================

def build_playlist_flow(tracks):

    if not tracks:
        return []

    random.shuffle(tracks)

    # Select up to 20 tracks initially
    selected_tracks = random.sample(
        tracks,
        min(20, len(tracks))
    )

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

    print(
        f"[Playlist] 최종 플레이리스트: "
        f"{len(filtered_tracks)}곡"
    )

    return filtered_tracks

# =========================================================
# 출력 생성
# =========================================================

def write_output(classified_items):

    outputs = []

    for item in classified_items:

        fact = item["원래_입력"]

        situation = fact.get("situation")

        outputs.append(
            "\n==============================="
        )

        outputs.append(
            f"{item['input_id']} 플레이리스트"
        )

        outputs.append(
            f"상황: {situation}"
        )

        outputs.append(
            "===============================\n"
        )

        external_context = fetch_external_context(

            item["검색_파라미터"],

            item["음악_속성"]
        )

        candidate_tracks = (
            external_context["tracks"]
        )

        filtered_tracks = (
            filter_tracks_by_situation(

                candidate_tracks,

                item["음악_속성"],

                item["검색_파라미터"]
            )
        )

        playlist = build_playlist_flow(
            filtered_tracks
        )

        for idx, track in enumerate(
            playlist,
            start=1
        ):

            reason = generate_reason(

                track,

                item["음악_속성"],

                item["검색_파라미터"]
            )

            outputs.append(

                f"{idx}. "
                f"{track['artist']} - "
                f"{track['name']}"
            )

            outputs.append(
                f"   이유: {reason}\n"
            )

    return "\n".join(outputs)

# =========================================================
# 저장
# =========================================================

def save_draft(text):

    file_path = Path("draft.md")

    file_path.write_text(
        text,
        encoding="utf-8"
    )

    print(f"[Save] 저장 완료: {file_path}")

# =========================================================
# MAIN
# =========================================================

def main():

    user_input = input(
        "상황, 장르, 아티스트를 입력하시겠습니까? (y/n): "
    )

    if user_input.strip().lower() == "y":

        user_situation = input(
            "상황 입력: "
        )

        user_genres = input(
            "장르 입력 (쉼표 구분): "
        )

        user_artists = input(
            "아티스트 입력 (쉼표 구분): "
        )

        local_sample_input = f"""
[입력 1]
- 상황: {user_situation}
- 장르: {user_genres}
- 아티스트: {user_artists}
"""

    else:

        local_sample_input = SAMPLE_INPUT

    print("\n--- 입력 분석 에이전트 ---")

    facts = extract_facts(
        local_sample_input
    )

    for fact in facts:
        print(fact)

    print("\n--- 상황 분석 에이전트 ---")

    classified_items = classify_items(
        facts
    )

    for item in classified_items:
        print(item)
        print(f"구성 계획: {item['playlist_structure']}")
        print(f"판단 근거: {item['judgment_reason']}")

    approval = input(
        "\n플레이리스트를 생성할까요? (y/n): "
    )

    if approval.strip().lower() != "y":

        print("생성을 취소했습니다.")

        return

    print("\n--- 플레이리스트 생성 ---")

    output = write_output(
        classified_items
    )

    print(output)

    while True:

        print("\n--- 사용자 선택 ---")

        print("1. 저장 후 종료")
        print("2. 같은 조건으로 다시 생성")
        print("3. 장르/아티스트 수정")

        choice = input(
            "선택 입력 (1/2/3): "
        ).strip()

        if choice == "1":

            save_draft(output)

            print("프로그램 종료")

            return

        elif choice == "2":

            print(
                "\n같은 조건으로 재생성"
            )

            output = write_output(
                classified_items
            )

            print(output)

        elif choice == "3":

            print(
                "\n장르/아티스트 수정"
            )

            for fact in facts:

                new_genres = input(

                    f"{fact['input_id']} "
                    f"새 장르 입력 "
                    f"(쉼표 구분): "
                )

                new_artists = input(

                    f"{fact['input_id']} "
                    f"새 아티스트 입력 "
                    f"(쉼표 구분): "
                )

                fact["genre"] = [

                    g.strip()

                    for g in new_genres.split(",")
                ]

                fact["artist"] = [

                    a.strip()

                    for a in new_artists.split(",")
                ]

            classified_items = classify_items(
                facts
            )

            output = write_output(
                classified_items
            )

            print(output)

        else:

            print("잘못된 입력")

# =========================================================
# 실행
# =========================================================

if __name__ == "__main__":
    main()