import requests
from bs4 import BeautifulSoup
import json
import re

# URL ตารางใช้ห้องเรียน อาคารเรียนรวม 80 ปี จาก REG MJU
URL = "https://reg.mju.ac.th/registrar/room_timeall.asp?f_cmd=1&campusid=50&campusname=%E0%AA%D5%C2%A7%E3%CB%C1%E8&bc=147&bn=%CD%D2%A4%D2%C3%E0%C3%D5%C2%B9%C3%C7%C1+80+%BB%D5"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def parse_day(day_str):
    days = {
        'จ.': 1, 'อ.': 2, 'พ.': 3, 'พฤ.': 4, 'ศ.': 5, 'ส.': 6, 'อา.': 7,
        'จันทร์': 1, 'อังคาร': 2, 'พุธ': 3, 'พฤหัสบดี': 4, 'ศุกร์': 5, 'เสาร์': 6, 'อาทิตย์': 7
    }
    for k, v in days.items():
        if k in day_str:
            return v
    return None

def fetch_schedules():
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.encoding = 'tis-620' # กำหนด Encoding ตามระบบ REG
        
        soup = BeautifulSoup(response.text, 'html.parser')
        schedules = []
        
        # ค้นหาตารางในหน้า REG
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            current_room = ""
            
            for row in rows:
                cols = [td.text.strip() for td in row.find_all(['td', 'th'])]
                if not cols:
                    continue
                
                # ตรวจหาชื่อห้อง (เช่น 80-201 หรือ ห้อง 80-102)
                for cell in cols:
                    match_room = re.search(r'80-\d{3}', cell)
                    if match_room:
                        current_room = match_room.group(0)

                # ดึงวัน เวลา และชื่อวิชา
                # รูปแบบเวลาปกติ เช่น 08:00 - 11:00 หรือ 08:00-11:00
                time_match = re.search(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', " ".join(cols))
                if time_match and current_room:
                    start_time, end_time = time_match.groups()
                    
                    # หาวันในสัปดาห์
                    day_num = None
                    for cell in cols:
                        day_num = parse_day(cell)
                        if day_num:
                            break
                    
                    if day_num:
                        # ฟอร์แมตเวลาให้เป็น HH:mm
                        s_h, s_m = start_time.split(':')
                        e_h, e_m = end_time.split(':')
                        formatted_start = f"{int(s_h):02d}:{s_m}"
                        formatted_end = f"{int(e_h):02d}:{e_m}"
                        
                        schedules.append({
                            "room": current_room,
                            "dayOfWeek": day_num,
                            "startTime": formatted_start,
                            "endTime": formatted_end,
                            "raw_info": " ".join(cols)
                        })
                        
        print(f"ดึงข้อมูลตารางสอนสำเร็จ ทั้งหมด {len(schedules)} รายการ")
        return schedules

    except Exception as e:
        print("เกิดข้อผิดพลาดในการดึงข้อมูล:", e)
        return []

if __name__ == "__main__":
    data = fetch_schedules()
    with open("schedules.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("บันทึกไฟล์ schedules.json เรียบร้อยแล้ว")