import os
import requests
import json
import certifi
from bs4 import BeautifulSoup
import time  # 导入time模块

# 从测试号信息获取
appID = os.environ.get("APP_ID")
appSecret = os.environ.get("APP_SECRET")
# 收信人ID列表，以逗号分隔
openIds = os.environ.get("OPEN_IDS", "").split(",")
# 天气预报模板ID
weather_template_id = os.environ.get("TEMPLATE_ID")

def log_time(message):
    """打印当前时间和消息"""
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}")

def get_weather(my_city):
    log_time("开始获取天气信息")
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
                city_td = tds[-8]
                this_city = list(city_td.stripped_strings)[0]
                if this_city == my_city:
                    high_temp_td = tds[-5]
                    low_temp_td = tds[-2]
                    weather_type_day_td = tds[-7]
                    weather_type_night_td = tds[-4]
                    wind_td_day = tds[-6]
                    wind_td_day_night = tds[-3]

                    high_temp = list(high_temp_td.stripped_strings)[0]
                    low_temp = list(low_temp_td.stripped_strings)[0]
                    weather_typ_day = list(weather_type_day_td.stripped_strings)[0]
                    weather_type_night = list(weather_type_night_td.stripped_strings)[0]

                    wind_day = list(wind_td_day.stripped_strings)[0] + list(wind_td_day.stripped_strings)[1]
                    wind_night = list(wind_td_day_night.stripped_strings)[0] + list(wind_td_day_night.stripped_strings)[1]

                    temp = f"{low_temp}——{high_temp}摄氏度" if high_temp != "-" else f"{low_temp}摄氏度"
                    weather_typ = weather_typ_day if weather_typ_day != "-" else weather_type_night
                    wind = f"{wind_day}" if wind_day != "--" else f"{wind_night}"
                    log_time("完成获取天气信息")
                    return this_city, temp, weather_typ, wind

def get_access_token():
    log_time("开始获取access token")
    url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}' \
        .format(appID.strip(), appSecret.strip())
    response = requests.get(url).json()
    print(response)
    access_token = response.get('access_token')
    log_time("完成获取access token")
    return access_token

def get_daily_love():
    log_time("开始获取一言")
    url = "https://v1.hitokoto.cn"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        from requests.adapters import HTTPAdapter
        from requests.packages.urllib3.util.retry import Retry
        from requests.packages.urllib3.poolmanager import PoolManager
        import ssl

        class TLSAdapter(HTTPAdapter):
            def init_poolmanager(self, connections, maxsize, block=False):
                self.poolmanager = PoolManager(
                    num_pools=connections,
                    maxsize=maxsize,
                    block=block,
                    ssl_version=ssl.PROTOCOL_TLSv1_2
                )

        session = requests.Session()
        adapter = TLSAdapter()
        session.mount('https://', adapter)
        
        r = session.get(
            url,
            headers=headers,
            timeout=10
        )
        
        response_data = r.json()
        hitokoto = response_data['hitokoto']  # 只获取一言内容

        print(f"\n获取到的一言: {hitokoto}")
        log_time("完成获取一言")
        return hitokoto  # 直接返回一言内容

    except Exception as e:
        print(f"获取一言API失败：{str(e)}")
        return "今天也要开开心心哦！"

def send_weather(access_token, weather):
    log_time("开始发送天气信息")
    import datetime
    today = datetime.date.today()
    today_str = today.strftime("%Y年%m月%d日")

    if not openIds or openIds == [""]:
        print("Error: OPEN_IDS 环境变量未设置或为空")
        return

    daily_message = get_daily_love()

    for openId in openIds:
        openId = openId.strip().replace('"', '')
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
                        "value": daily_message
                    }
                }
            }
            url = 'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}'.format(access_token)
            response = requests.post(url, json.dumps(body)).text
            print(f"发送至 {openId}: {response}")
    log_time("完成发送天气信息")

def weather_report(this_city):
    log_time("开始天气报告")
    access_token = get_access_token()
    weather = get_weather(this_city)
    print(f"天气信息： {weather}")
    send_weather(access_token, weather)
    log_time("完成天气报告")

if __name__ == '__main__':
    weather_report("济南")
