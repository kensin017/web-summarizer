import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import openai

st.set_page_config(page_title="GPT 웹 요약기", layout="wide")

st.title("🌐 GPT 웹페이지 요약기")
st.write("웹페이지 본문을 자동으로 요약해드립니다. 하위 링크까지 포함됩니다.")

def extract_links(url):
    base = urlparse(url).netloc
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        links = set()
        for tag in soup.find_all('a', href=True):
            href = urljoin(url, tag['href'])
            if base in urlparse(href).netloc:
                links.add(href.split('#')[0])
        return list(links)
    except:
        return []

def extract_text(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        for tag in soup(['script', 'style', 'header', 'footer', 'nav']):
            tag.decompose()
        text = soup.get_text(separator=' ', strip=True)
        return text[:4000]  # GPT token 제한 대응
    except:
        return ""

def summarize_text(text):
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"다음 웹 페이지 내용을 핵심만 요약해줘:\n{text}"}],
        temperature=0.5
    )
    return response.choices[0].message.content

url = st.text_input("🔗 웹페이지 주소 입력", placeholder="https://example.com")

if st.button("요약 시작") and url:
    with st.spinner("링크 추출 중..."):
        all_links = [url] + extract_links(url)
    with st.spinner("본문 수집 중..."):
        texts = [extract_text(link) for link in all_links]
    with st.spinner("GPT 요약 중..."):
        merged = "\n\n".join(texts)
        summary = summarize_text(merged)
    st.subheader("📝 요약 결과")
    st.write(summary)
    st.download_button("요약 결과 다운로드", summary, file_name="summary.txt")
