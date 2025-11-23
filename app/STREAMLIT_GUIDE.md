# Streamlit 챗봇 페이지 수정 가이드

## 📍 주요 수정 포인트

### 1. **사용자 입력 처리 로직** (53-130줄)

#### `extract_user_preferences()` 함수
- **위치**: 53-84줄
- **역할**: 사용자 메시지에서 선호도 추출
- **수정 방법**:
  ```python
  # 키워드 추가/수정
  if any(word in message_lower for word in ["새로운키워드"]):
      preferences["trust_safety"] = 80.0  # 값 변경
  ```

#### `parse_search_query()` 함수
- **위치**: 87-110줄
- **역할**: 검색 쿼리 추출
- **수정 방법**:
  ```python
  # 패턴 추가
  patterns = [
      r"찾고\s+있",
      r"새로운패턴",  # 여기에 추가
  ]
  ```

#### `build_user_input()` 함수
- **위치**: 113-130줄
- **역할**: API에 전달할 데이터 생성
- **수정 방법**:
  ```python
  return {
      "search_query": search_query,
      **preferences,
      "category": "스마트폰",  # 기본값 설정
      "price_min": 100000,     # 기본값 설정
  }
  ```

---

### 2. **추천 요청 처리** (133-184줄)

#### `handle_recommendation_request()` 함수
- **위치**: 133-184줄
- **역할**: 사용자 메시지 처리 및 API 호출

**주요 수정 포인트:**

```python
# 1. 챗봇 응답 메시지 변경 (141줄)
add_message("assistant", "원하는 메시지로 변경")

# 2. 워크플로우 상태 단계 수정 (144줄)
update_workflow_status("원하는단계명", [], is_running=True)

# 3. API 호출 전 처리 추가 (150줄 이전)
# 예: 입력 검증, 추가 데이터 수집 등

# 4. API 응답 처리 로직 수정 (163-178줄)
if status == "success":
    # 여기서 결과 처리 방식 변경
    final_items = result.get("final_item_scores", [])
    # 원하는 로직 추가
```

---

### 3. **UI 레이아웃** (187-298줄)

#### `main()` 함수 - 사이드바 (196-224줄)
```python
with st.sidebar:
    # 버튼 추가
    if st.button("새로운 버튼"):
        # 버튼 클릭 시 동작
    
    # 입력 필드 추가
    new_input = st.text_input("새 입력 필드")
    
    # 선택 박스 추가
    option = st.selectbox("옵션 선택", ["옵션1", "옵션2"])
```

#### `main()` 함수 - 메인 영역 (226-270줄)
```python
# 1. 레이아웃 비율 변경 (227줄)
col1, col2 = st.columns([3, 1])  # 비율 변경

# 2. 채팅 히스토리 표시 방식 변경 (244-246줄)
for message in chat_history:
    # 커스텀 렌더링 로직 추가
    render_message(message)

# 3. 입력 영역 수정 (255-259줄)
user_input = st.text_area(  # text_input 대신 text_area 사용
    "메시지 입력",
    height=100,
    key="chat_input"
)
```

#### `main()` 함수 - 추천 결과 영역 (272-298줄)
```python
# 1. 결과 표시 방식 변경
if final_items:
    # 카드 대신 테이블로 표시
    st.dataframe(final_items)
    
    # 또는 다른 컴포넌트 사용
    for item in final_items:
        st.write(item)
```

---

### 4. **스타일링** (37-50줄)

```python
st.markdown("""
    <style>
    /* CSS 추가/수정 */
    .chat-container {
        height: 800px;  /* 높이 변경 */
        background-color: #ffffff;  /* 배경색 변경 */
    }
    
    /* 새로운 스타일 추가 */
    .custom-class {
        color: red;
    }
    </style>
""", unsafe_allow_html=True)
```

---

### 5. **컴포넌트 커스터마이징**

#### 메시지 표시 변경: `app/components/chat_message.py`
```python
# 사용자 메시지 스타일 변경
st.markdown(
    f"""
    <div style="background-color: #원하는색상;">
        {content}
    </div>
    """,
    unsafe_allow_html=True
)
```

#### 추천 카드 변경: `app/components/recommendation_card.py`
```python
# 카드 레이아웃 변경
col1, col2, col3 = st.columns([1, 1, 1])  # 3열로 변경

# 추가 정보 표시
st.image(product.get("image_url"))  # 이미지 추가
```

---

## 🔧 자주 사용하는 Streamlit 기능

### 입력 위젯
```python
# 텍스트 입력
text = st.text_input("레이블", value="기본값")

# 숫자 입력
number = st.number_input("숫자", min_value=0, max_value=100)

# 선택 박스
option = st.selectbox("선택", ["옵션1", "옵션2"])

# 슬라이더
value = st.slider("슬라이더", 0, 100, 50)

# 체크박스
checked = st.checkbox("체크박스")
```

### 표시 위젯
```python
# 텍스트
st.write("텍스트")
st.markdown("**마크다운**")
st.title("제목")
st.header("헤더")
st.subheader("서브헤더")

# 데이터
st.dataframe(data)  # 테이블
st.json(data)       # JSON
st.table(data)      # 간단한 테이블

# 상태
st.success("성공")
st.error("에러")
st.warning("경고")
st.info("정보")
```

### 레이아웃
```python
# 컬럼
col1, col2 = st.columns(2)
with col1:
    st.write("왼쪽")
with col2:
    st.write("오른쪽")

# 탭
tab1, tab2 = st.tabs(["탭1", "탭2"])
with tab1:
    st.write("탭1 내용")

# 컨테이너
with st.container():
    st.write("컨테이너 내용")
```

### 상태 관리
```python
# 세션 상태에 저장
st.session_state["key"] = value

# 세션 상태에서 읽기
value = st.session_state.get("key", "기본값")

# 페이지 새로고침
st.rerun()
```

---

## 📝 수정 예시

### 예시 1: 챗봇 응답 메시지 변경
```python
# 141줄 수정
add_message("assistant", "알겠습니다! 분석을 시작할게요. 잠시만요...")
```

### 예시 2: 입력 필드를 text_area로 변경
```python
# 255줄 수정
user_input = st.text_area(
    "메시지 입력",
    placeholder="여러 줄 입력 가능",
    height=100,
    key="chat_input"
)
```

### 예시 3: 추천 결과를 테이블로 표시
```python
# 289줄 수정
if final_items:
    # 카드 대신 테이블
    df = pd.DataFrame(final_items)
    st.dataframe(df, use_container_width=True)
```

### 예시 4: 사이드바에 필터 추가
```python
# 196줄 이후에 추가
with st.sidebar:
    st.header("🔍 필터")
    category = st.selectbox("카테고리", ["전체", "스마트폰", "노트북"])
    price_range = st.slider("가격 범위", 0, 10000000, (0, 10000000))
```

---

## ⚠️ 주의사항

1. **`st.rerun()`**: 버튼 클릭 후 페이지 새로고침 필요 시 사용
2. **`st.session_state`**: 데이터 저장/읽기용 (페이지 새로고침 시 유지)
3. **`key` 파라미터**: 같은 위젯을 여러 번 사용할 때 고유 키 필요
4. **컴포넌트 import**: 다른 파일의 함수 사용 시 `from app.xxx import yyy` 형식

---

## 🚀 빠른 시작

1. **간단한 수정**: 메시지 텍스트 변경 (141줄, 171줄 등)
2. **로직 수정**: `handle_recommendation_request()` 함수 내부
3. **UI 변경**: `main()` 함수의 레이아웃 부분
4. **스타일 변경**: 37-50줄의 CSS 부분

