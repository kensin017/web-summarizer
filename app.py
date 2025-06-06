import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import openai
import time
from openai import RateLimitError

st.set_page_config(page_title="GPT 웹페이지 요약기", layout="wide")

# 🔑 API 키 설정 (Streamlit Secrets 사용)
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("🧠 GPT 웹페이지 요약기")
st.write("웹페이지 본문을 자동으로 요약해드립니다. 하위 링크까지 포함됩니다.")

# ✅ 링크 수집
def extract_links(url):
    base_domain = urlparse(url).netloc
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        links = set()
        for tag in soup.find_all('a', href=True):
            href = urljoin(url, tag['href'])
            if base_domain in urlparse(href).netloc:
                links.add(href.split('#')[0])
        return list(links)
    except Exception as e:
        st.error(f"링크 수집 실패: {e}")
        return []

# ✅ 텍스트 추출
def extract_text(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        for tag in soup(['script', 'style', 'header', 'footer', 'nav']):
            tag.decompose()
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        st.warning(f"본문 추출 실패: {url} → {e}")
        return ""

# ✅ 요약 (RateLimit 대응 포함)
def summarize_text(text):
    prompt = f"다음 웹 페이지 내용을 핵심만 요약해줘:\n{text}"
    for i in range(3):  # 최대 3회 재시도
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            return response.choices[0].message.content
        except RateLimitError:
            wait = 2 ** i
            st.warning(f"요청이 많아 대기 중입니다... ({wait}초)")
            time.sleep(wait)
        except Exception as e:
            return f"요약 실패: {e}"
    return "❌ 요약 요청이 너무 많아 실패했습니다."

# ✅ 입력창
url = st.text_input("🔗 웹페이지 주소 입력", placeholder="https://example.com")

if st.button("요약 시작") and url:
    with st.spinner("🔍 링크 수집 중..."):
        all_links = [url] + extract_links(url)
    
    with st.spinner("📄 본문 수집 중..."):
        texts = [extract_text(link) for link in all_links]
        merged_text = "\n\n".join(texts)[:8000]  # 최대 토큰 제한 대응

    with st.spinner("🧠 GPT 요약 중..."):
        summary = summarize_text(merged_text)

    st.subheader("📋 요약 결과")
    st.write(summary)
    st.download_button("📥 요약 결과 다운로드", summary, file_name="summary.txt")
