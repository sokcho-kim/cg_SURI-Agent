from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, pandas as pd

options = webdriver.ChromeOptions()
options.add_argument('--headless=new')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)

# 페이지 진입 및 탭 이동
driver.get("https://www.hira.or.kr/rc/insu/insuadtcrtr/InsuAdtCrtrList.do?pgmid=HIRAA030069000400")
time.sleep(2)
driver.execute_script("goTabMove('10');")  # '심의사례공개' 탭 이동
time.sleep(2)

# 1. '페이지수 선택' 드롭다운 열기
dropdown = driver.find_element(By.ID, "pageLen")
dropdown.find_element(By.CLASS_NAME, "selected").click()
time.sleep(0.5)

# 2. '30개' 항목 클릭
option_30 = driver.find_element(By.XPATH, "//*[@id='pageLen']//a[text()='30개']")
driver.execute_script("arguments[0].click();", option_30)
time.sleep(2)


data = []
index = 1

while True:
    # 목록 테이블 rows
    rows = driver.find_elements(By.CSS_SELECTOR, "#cont > div.board_list > table > tbody > tr")
    for row in rows:
        title_el = row.find_element(By.CSS_SELECTOR, "td.subject > a")
        title = title_el.text.strip()
        date = row.find_element(By.CSS_SELECTOR, "td.date").text.strip()

        # 팝업 열기
        driver.execute_script("arguments[0].click();", title_el)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".pop_view > .view")))

        time.sleep(1)  # 팝업 로딩 대기
        popup = driver.find_element(By.CSS_SELECTOR, ".pop_view > .view")

        # 첨부파일 있는지 확인
        try:
            file_el = popup.find_element(By.CSS_SELECTOR, "ul.file_list > li > a")
            attachment_url = file_el.get_attribute("href")
            has_attachment = True
            content_html = None
        except:
            has_attachment = False
            attachment_url = None
            try:
                content_html = popup.find_element(By.CSS_SELECTOR, ".view_cont").get_attribute("innerHTML")
            except:
                content_html = None

        # 팝업 닫기
        close_btn = driver.find_element(By.CSS_SELECTOR, "button.btn_close")
        close_btn.click()
        time.sleep(0.5)

        data.append({
            "index": f"{index:03}",
            "title": title,
            "date": date,
            "has_attachment": has_attachment,
            "attachment_url": attachment_url,
            "content_html": content_html
        })
        index += 1

    # 다음 페이지 이동 확인
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, "a.next")
        if "disabled" in next_btn.get_attribute("class"):
            break
        else:
            next_btn.click()
            time.sleep(2)
    except:
        break

driver.quit()

# 저장
df = pd.DataFrame(data)
df.to_csv("심의사례공개_메타데이터.csv", index=False, encoding="utf-8-sig")
print("✅ 전체 목록 메타데이터 저장 완료: 심의사례공개_메타데이터.csv")
