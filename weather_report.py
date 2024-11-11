# 安装依赖 pip3 install requests html5lib bs4 schedule
import os
import requests
import json
from bs4 import BeautifulSoup

# 从测试号信息获取
appID = os.environ.get("APP_ID")
appSecret = os.environ.get("APP_SECRET") 
# 收信人ID列表，以逗号分隔
openIds = os.environ.get("OPEN_IDS", "").split(",")
# 天气预报模板ID
weather_template_id = os.environ.get("TEMPLATE_ID")

def get_weather(my_city, my_district="历城"):
    url = "http://www.weather.com.cn/textFC/hd.shtml"
    resp = requests.get(url)
    text = resp.content.decode("utf-8")
    soup = BeautifulSoup(text, 'html5lib')
    div_conMidtab = soup.find("div", class_="conMidtab")
    tables = div_conMidtab.find_all("table")
    
    for table in tables:
        trs = table.find_all("tr")[2:]  # 从第3行开始，因为前两行可能是标题
        for index, tr in enumerate(trs):
            tds = tr.find_all("td")
            
            # 获取城市和区县的名称
            city_td = tds[0] if index == 0 else tds[1]
            district_td = tds[0] if index != 0 else None
            this_city = list(city_td.stripped_strings)[0]
            this_district = list(district_td.stripped_strings)[0] if district_td else this_city
            
            # 匹配目标城市和区县
            if this_city == my_city and this_district == my_district:
                high_temp_td = tds[-5]
                low_temp_td = tds[-2]
                weather_type_day_td = tds[-7]
                weather_type_night_td = tds[-4]
                wind_td_day = tds[-6]
                wind_td_night = tds[-3]

                high_temp = list(high_temp_td.stripped_strings)[0]
                low_temp = list(low_temp_td.stripped_strings)[0]
                weather_type_day = list(weather_type_day_td.stripped_strings)[0]
                weather_type_night = list(weather_type_night_td.stripped_strings)[0]

                wind_day = ''.join(list(wind_td_day.stripped_strings))
                wind_night = ''.join(list(wind_td_night.stripped_strings))

                temp = f"{low_temp}——{high_temp}摄氏度" if high_temp != "-" else f"{low_temp}摄氏度"
                weather_type = weather_type_day if weather_type_day != "-" else weather_type_night
                wind = wind_day if wind_day != "--" else wind_night
                
                return this_district, temp, weather_type, wind
    return None, None, None, None

def get_access_token():
    url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}'.format(appID.strip(), appSecret.strip())
    response = requests.get(url).json()
    access_token = response.get('access_token')
    return access_token

def get_daily_love():
    url = "https://api.lovelive.tools/api/SweetNothings/Serialization/Json"
    r = requests.get(url)
    all_dict = json.loads(r.text)
    sentence = all_dict['returnObj'][0]
    return sentence

def send_weather(access_token, weather):
    import datetime
    today = datetime.date.today()
    today_str = today.strftime("%Y年%m月%d日")

    if not openIds or openIds == [""]:
        print("Error: OPEN_IDS 环境变量未设置或为空")
        return

    for openId in openIds:
        openId = openId.strip().replace('"', '')  # 去除多余的引号和空格
        if openId:
            body = {
                "touser": openId,
                "template_id": weather_template_id.strip(),
                "url": "https://weixin.qq.com",
                "data": {
                    "date": {
                        "value": today_str
                    },
                    "region": {
                        "value": weather[0]
                    },
                    "weather": {
                        "value": weather[2]
                    },
                    "temp": {
                        "value": weather[1]
                    },
                    "wind_dir": {
                        "value": weather[3]
                    },
                    "today_note": {
                        "value": get_daily_love()
                    }
                }
            }
            url = 'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}'.format(access_token)
            response = requests.post(url, json.dumps(body)).text
            print(f"发送至 {openId}: {response}")

def weather_report(this_city, this_district="历城"):
    access_token = get_access_token()
    weather = get_weather(this_city, this_district)
    print(f"天气信息： {weather}")
    send_weather(access_token, weather)

if __name__ == '__main__':
    weather_report("济南", "历城")
