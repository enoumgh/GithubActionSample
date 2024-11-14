# 安装依赖 pip3 install requests html5lib bs4 schedule certifi
import os
import requests
import json
import certifi
from bs4 import BeautifulSoup

# 从测试号信息获取
appID = os.environ.get("APP_ID")
appSecret = os.environ.get("APP_SECRET")
# 收信人ID列表，以逗号分隔
openIds = os.environ.get("OPEN_IDS", "").split(",")
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
                    return this_city, temp, weather_typ, wind

def get_access_token():
    url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}' \
        .format(appID.strip(), appSecret.strip())
    response = requests.get(url).json()
    print(response)
    access_token = response.get('access_token')
    return access_token

def get_daily_love():
    url = "https://v1.hitokoto.cn"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # 添加重试机制
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
        
        # 使用session发送请求
        r = session.get(
            url,
            headers=headers,
            timeout=10
        )
        
        response_data = r.json()
        # 获取基本信息
        hitokoto = response_data['hitokoto']
        source = response_data.get('from', '未知')
        author = response_data.get('from_who')

        # 根据是否有作者信息来格式化输出
        result = f"{hitokoto} ——《{source}》{author}" if author else f"{hitokoto} ——《{source}》"
        print(f"\n获取到的一言: {result}")  # 添加这行来打印一言内容
        return result

    except Exception as e:
        print(f"获取一言API失败：{str(e)}")
        return "今天也要开开心心哦！"

def send_weather(access_token, weather):
    import datetime
    today = datetime.date.today()
    today_str = today.strftime("%Y年%m月%d日")

    if not openIds or openIds == [""]:
        print("Error: OPEN_IDS 环境变量未设置或为空")
        return

    # 在循环外获取一言
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
                        "value": daily_message  # 使用已获取的一言
                    }
                }
            }
            url = 'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}'.format(access_token)
            response = requests.post(url, json.dumps(body)).text
            print(f"发送至 {openId}: {response}")

def weather_report(this_city):
    # 1.获取access_token
    access_token = get_access_token()
    # 2. 获取天气
    weather = get_weather(this_city)
    print(f"天气信息： {weather}")
    # 3. 发送消息
    send_weather(access_token, weather)

if __name__ == '__main__':
    weather_report("济南")
