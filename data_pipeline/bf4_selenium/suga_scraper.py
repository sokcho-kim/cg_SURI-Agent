import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options


def wait_for_page_load(driver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#resultList tbody tr"))
        )
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "#resultList tbody tr")) > 0
        )
        return True
    except TimeoutException:
        return False


def crawl_suga_codes():
    options = Options()
    options.add_argument("--headless=new")  # 백그라운드 실행
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    chrome_driver_path = r"C:\tools\chromedriver-win64\chromedriver.exe"  # 형님 경로 맞게 수정

    service = Service(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    url = "https://www.koicd.kr/ins/act.do"
    print("🔄 웹사이트 접속 중...")
    driver.get(url)
    time.sleep(2)  # JS 렌더링 대기

    if not wait_for_page_load(driver):
        print("❌ 초기 페이지 로딩 실패")
        driver.quit()
        return

    rows = driver.find_elements(By.CSS_SELECTOR, "#resultList tbody tr")
    results = []
    for row in rows:
        try:
            tds = row.find_elements(By.TAG_NAME, "td")
            suga_code = tds[0].text.strip()
            name_kr = tds[1].text.strip()
            name_en = tds[2].text.strip()
            results.append([suga_code, name_kr, name_en])
        except Exception as e:
            print(f"⚠️ 행 파싱 실패: {e}")
            continue

    driver.quit()

    if results:
        with open("suga_result.csv", "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["수가코드", "행위명(한글)", "행위명(영문)"])
            writer.writerows(results)
        print(f"✅ {len(results)}건 수집 완료")
    else:
        print("❌ 수집된 데이터가 없습니다")


if __name__ == "__main__":
    crawl_suga_codes()
