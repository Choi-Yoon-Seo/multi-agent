SAMPLE_INPUT = """
[입력 1]
- 상황: 드라이브
- 장르: Pop
- 아티스트: Bruno Mars, The Weeknd

[입력 2]
- 상황: 신날 때
- 장르: KPop
- 아티스트: NCT WISH, ILLIT

[입력 3]
- 상황: 집중
- 장르: JPop
- 아티스트: 요네즈 켄시
"""

def extract_facts(text):
    """사용자가 입력한 문자열에서 입력ID, 상황, 장르, 아티스트를 추출합니다."""
    results = []
    # 공백 줄을 기준으로 블록을 나눕니다.
    blocks = text.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        fact = {}
        for line in lines:
            line = line.strip()
            if line.startswith("["):
                fact["id"] = line
            elif line.startswith("- 상황:"):
                fact["상황"] = line.replace("- 상황:", "").strip()
            elif line.startswith("- 장르:"):
                fact["장르"] = [g.strip() for g in line.replace("- 장르:", "").split(",")]
            elif line.startswith("- 아티스트:"):
                fact["아티스트"] = [a.strip() for a in line.replace("- 아티스트:", "").split(",")]
        
        if fact:
            results.append(fact)
    return results

def classify_items(facts):
    """추출된 상황 텍스트를 음악 속성(BPM, 에너지 등)으로 맵핑하고 필터를 병합합니다."""
    # 상황별 음악 속성 맵핑 테이블 (데이터베이스 대신 하드코딩)
    mapping = {
        "드라이브": {"bpm": "110-130", "energy": "High", "valence": "High", "instrumental": False},
        "신날 때": {"bpm": "130-150", "energy": "Very High", "valence": "High", "instrumental": False},
        "집중": {"bpm": "60-90", "energy": "Low", "valence": "Neutral", "instrumental": True}
    }
    
    classified = []
    for fact in facts:
        situation = fact.get("상황", "")
        # 매핑 테이블에 없는 경우 기본값 적용
        music_props = mapping.get(situation, {"bpm": "100", "energy": "Medium", "valence": "Medium", "instrumental": False})
        
        merged_item = {
            "id": fact.get("id"),
            "원래_입력": fact,
            "음악_속성": music_props,
            "검색_파라미터": {
                "장르": fact.get("장르", []),
                "아티스트": fact.get("아티스트", []),
                "최적_bpm": music_props["bpm"]
            }
        }
        classified.append(merged_item)
        
    return classified

def write_output(classified_items):
    """분류된 항목(검색 파라미터)을 기반으로 플레이리스트 초안을 구성하여 문장으로 작성합니다."""
    outputs = []
    
    for item in classified_items:
        fact = item["원래_입력"]
        situation = fact.get("상황")
        bpm = item['음악_속성']['bpm']
        energy = item['음악_속성']['energy']
        artists = fact.get("아티스트", ["알 수 없음"])
        
        # 첫 번째 아티스트와 마지막 아티스트 이름을 이용해 임의 조합 생성
        artist1 = artists[0]
        artist2 = artists[-1] if len(artists) > 1 else artists[0]

        draft_text = f"=== {item['id']} 플레이리스트 초안 ===\n"
        draft_text += f"[분석] 상황: '{situation}' ➔ BPM: {bpm} / 에너지: {energy}에 맞춘 설정\n\n"
        
        # 실제 API 호출 없이 하드코딩된 초안 형태 안내 (도입-전개-정점-마무리 구조)
        draft_text += f"1. 도입부: {artist1}의 잔잔한 분위기 곡\n   - 이유: '{situation}' 상황을 편안하게 열어주기 위해 선택\n"
        draft_text += f"2. 전개부: {artist1}의 템포감 있는 곡\n   - 이유: 점진적으로 {energy} 에너지를 끌어올림\n"
        draft_text += f"3. 정점부: {artist2}의 폭발력 있고 리듬감 넘치는 곡\n   - 이유: 이 플레이리스트의 하이라이트 구간\n"
        draft_text += f"4. 마무리: 비슷한 장르의 인스트루멘탈/차분한 곡\n   - 이유: 분위기를 정리하며 부드럽게 마무리\n"
        
        outputs.append(draft_text)
        
    return "\n".join(outputs)


def main():
    print("--- 1. extract_facts() 실행: 사실 추출 ---")
    facts = extract_facts(SAMPLE_INPUT)
    for f in facts:
        print(f)
        
    print("\n--- 2. classify_items() 실행: 분류 및 필터 병합 ---")
    classified_items = classify_items(facts)
    for c in classified_items:
        print(f"ID: {c['id']}, 속성: {c['음악_속성']}, 검색파라미터: {c['검색_파라미터']}")
        
    print("\n--- [사용자 개입 지점] ---------------------------------------------")
    print("시스템: 상황 및 필터 분석이 완료되었습니다. 이 조건으로 플레이리스트를 만들까요?")
    user_approval = input("승인하시겠습니까? (y/n): ")
    print("------------------------------------------------------------------\n")
    
    if user_approval.strip().lower() != 'y':
        print("승인이 거절되었습니다. 작업을 중단합니다.")
        return

    print("--- 3. write_output() 실행: 플레이리스트 초안 작성 ---")
    final_output = write_output(classified_items)
    print(final_output)

if __name__ == "__main__":
    main()
