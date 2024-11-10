# 安装依赖 pip3 install requests html5lib bs4 schedule
import os
import requests
import json
from bs4 import BeautifulSoup

# 从测试号信息获取
appID = os.environ.get("APP_ID")
appSecret = os.environ.get("APP_SECRET")

# 收信人ID列表，即多个用户的微信号，默认使用空字符串防止 split 出错
openIds = os.environ.get("OPEN_IDS", "").split(",") if os.environ.get("OPEN_IDS") else []
# 天气预报模板ID
weather_template_id = os.environ.get("TEMPLATE_ID")

def get_weather(my_city):
    urls = ["http://www.weather.com.cn/textFC/hb.shtml",
            "http://www.weather.com.cn/textFC/db.shtml",
            "http://www.weather.com.cn/textFC/hd.shtml",
            "http://www.weather.com.cn/textFC/hz.shtml",
            "http://www.weather.com.cn/textFC/hn.shtml",
            "http://www.weather.com.cn/textFC/xb.shtml",
            "http://www.weather.com.cn/textFC/xn.shtml"
            ]
    for url in urls:
        resp = requests.get(url)
        text = resp.content.decode("utf-8")
        soup = BeautifulSoup(text, 'html5lib')
        div_conMidtab = soup.find("div", class_="conMidtab")
        tables = div_conMidtab.find_all("table")
        for table in tables:
            trs = table.find_all("tr")[2:]
            for index, tr in enumerate(trs):
                tds = tr.find_all("td")
                # 这里倒着数，因为每个省会的td结构跟其他不一样
                city_td = tds[-8]
                this_city = list(city_td.stripped_strings)[0]
                if this_city == my_city:
                    high_temp = list(tds[-5].stripped_strings)[0]
                    low_temp = list(tds[-2].stripped_strings)[0]
                    weather_typ_day = list(tds[-7].stripped_strings)[0]
                    weather_type_night = list(tds[-4].stripped_strings)[0]
                    wind_day = "".join(list(tds[-6].stripped_strings))
                    wind_night = "".join(list(tds[-3].stripped_strings))
                    
                    temp = f"{low_temp}——{high_temp}摄氏度" if high_temp != "-" else f"{low_temp}摄氏度"
                    weather_typ = weather_typ_day if weather_typ_day != "-" else weather_type_night
                    wind = wind_day if wind_day != "--" else wind_night
                    
                    return this_city, temp, weather_typ, wind

def get_access_token():
    url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}' \
        .format(appID.strip(), appSecret.strip())
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

    body_template = {
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

    # 循环发送消息给每个用户
    for openId in openIds:
        body = body_template.copy()
        body["touser"] = openId.strip()
        url = f'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}'
        print(requests.post(url, json.dumps(body)).text)

def weather_report(this_city):
    access_token = get_access_token()
    weather = get_weather(this_city)
    if weather:
        print(f"天气信息： {weather}")
        send_weather(access_token, weather)
    else:
        print("无法获取天气信息")

if __name__ == '__main__':
    weather_report("济南")
