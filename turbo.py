import os
import json
import requests
import time
import re
import hashlib
from datetime import datetime, timedelta

# 配置文件路径
config_file_path = "config.json"
签到结果 = ""

# 获取html中的用户信息
def fetch_and_extract_info(domain,headers, params):
    url = f"{domain}/appuser/userinfo"

    # 发起 GET 请求
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print("用户信息获取失败，页面打开异常.")
        return None

    # 解析登录响应的 JSON 数据
    user_json = response.json()
    
    # 获取用户剩余流量
    transfer = user_json['data']['transfer']
    print('Left transfer:', transfer)
    
    transfer_mb = int(transfer) / 1024 / 1024

    # 输出用户信息
    用户信息 = f"剩余流量: {transfer_mb}\n"
    print(f"剩余流量: {transfer_mb}")

    return 用户信息

def generate_config():
    # 获取环境变量
    domain = os.getenv('DOMAIN', 'https://api.viewturbo.com')  # 默认值，如果未设置环境变量
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')

    # if not bot_token or not chat_id:
        # raise ValueError("BOT_TOKEN 和 CHAT_ID 是必需的环境变量。")

    # 获取用户和密码的环境变量
    accounts = []
    index = 1

    while True:
        user = os.getenv(f'USER{index}')
        password = os.getenv(f'PASS{index}')

        if not user or not password:
            break  # 如果没有找到更多的用户信息，则退出循环

        accounts.append({
            'user': user,
            'pass': password
        })
        index += 1

    # 构造配置数据
    config = {
        'domain': domain,
        'BotToken': bot_token,
        'ChatID': chat_id,
        'accounts': accounts
    }
    print(config)
    return config


# 发送消息到 Telegram Bot 的函数，支持按钮
def send_message(msg="", BotToken="", ChatID=""):
    # 获取当前 UTC 时间，并转换为北京时间（+8小时）
    now = datetime.utcnow()
    beijing_time = now + timedelta(hours=8)
    formatted_time = beijing_time.strftime("%Y-%m-%d %H:%M:%S")

    # 打印调试信息
    # print(msg)

    # 如果 Telegram Bot Token 和 Chat ID 都配置了，则发送消息
    if BotToken != '' and ChatID != '':
        # 构建消息内容
        message_text = f"执行时间: {formatted_time}\n{msg}"

        # 构造按钮的键盘布局
        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "一休交流群",
                        "url": "https://t.me/yxjsjl"
                    }
                ]
            ]
        }

        # 发送消息时附带内联按钮
        url = f"https://api.telegram.org/bot{BotToken}/sendMessage"
        payload = {
            "chat_id": ChatID,
            "text": message_text,
            "parse_mode": "HTML",
            "reply_markup": json.dumps(keyboard)
        }

        try:
            # 发送 POST 请求
            response = requests.post(url, data=payload)
            return response
        except Exception as e:
            print(f"发送电报消息时发生错误: {str(e)}")
            return None

# 登录并签到的主要函数
def checkin(account, domain, BotToken, ChatID):
    user = account['user']
    pass_ = hashlib.md5(account['pass'].encode()).hexdigest()

    签到结果 = f"地址: {domain[:9]}****{domain[-5:]}\n账号: {user[:1]}****{user[-5:]}\n密码: {pass_[:1]}****{pass_[-1]}\n\n"

    try:
        # 检查必要的配置参数是否存在
        if not domain or not user or not pass_:
            raise ValueError('必需的配置参数缺失')

        # 登录请求的 URL
        login_url = f"{domain}/appuser/reglogin"

        params = {
            "platform": "web",
            "cur_version": "0.0.0",
            "token": "",
            "deviceinfo": "",
            "lang": "hk",
            "code": "Others"
        }
        
        # 登录请求的 Payload（请求体）
        login_data = {
            'email': user,
            'password': pass_
        }
        print(login_data)

        # 设置请求头
        login_headers = {
            "accept": "application/json",
            "accept-language": "zh-CN,zh;q=0.9",
            "content-type": "application/json",
            "origin": "https://web.vtpro.xyz",
            "priority": "u=1, i",
            "referer": "https://web.vtpro.xyz/",
            "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Google Chrome\";v=\"145\", \"Chromium\";v=\"145\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        }

        # 发送登录请求
        login_response = requests.post(login_url, json=login_data, headers=login_headers, params=params)

        print(f'{user}账号登录状态:', login_response.status_code)

        # 如果响应状态不是200，表示登录失败
        if login_response.status_code != 200:
            raise ValueError(f"登录请求失败: {login_response.text}")

        # 解析登录响应的 JSON 数据
        login_json = login_response.json()
        print(f'{user}账号登录后返回的信息:', login_json)

        # 检查登录是否成功
        if login_json.get("msg") != "成功":
            raise ValueError(f"登录失败: {login_json.get('msg', '未知错误')}")

        # 获取登录成功后的 token
        token = login_json['data']['token']
        print('Received token:', token)
        if not token:
            raise ValueError('登录成功但未收到token')

        # print('Received cookies:', cookies)

        # 等待确保登录状态生效
        time.sleep(1)

        # 签到请求的 URL
        checkin_url = f"{domain}/appuser/checkin"

        # 签到请求的 Headers
        checkin_headers = {
            "accept": "application/json",
            "accept-language": "zh-CN,zh;q=0.9",
            "content-type": "application/json",
            "origin": "https://web.vtpro.xyz",
            "priority": "u=1, i",
            "referer": "https://web.vtpro.xyz/",
            "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Google Chrome\";v=\"145\", \"Chromium\";v=\"145\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        }
        
        params = {
            "platform": "web",
            "cur_version": "0.0.0",
            "token": token,
            "deviceinfo": "",
            "lang": "hk",
            "code": "Others"
        }
        data = {}
        data = json.dumps(data, separators=(',', ':'))

        # 发送签到请求
        checkin_response = requests.post(checkin_url, headers=checkin_headers, params=params, data=data)

        print(f'{user}账号签到状态:', checkin_response.status_code)

        # 获取签到请求的响应内容
        response_text = checkin_response.text
        print(f'{user}账号签到响应内容:', response_text)


        try:
            # 尝试解析签到的 JSON 响应
            checkin_result = checkin_response.json()
            # print(f'{user}账号签到后的json信息:', checkin_result)
            账号信息 = f"地址: {domain}\n账号: {user}\n密码: <tg-spoiler>{pass_}</tg-spoiler>\n"

            用户信息 = fetch_and_extract_info(domain,checkin_headers, params)

            # 账号信息的展示，注意密码用 <tg-spoiler> 标签隐藏
            # 根据返回的结果更新签到信息
            if checkin_result['msg'] == "成功":
                签到结果 = f"🎉 签到成功"
            else:
                签到结果 = f"🎉 签到失败"
        except Exception as e:
            # 如果出现解析错误，检查是否由于登录失效
            if "登录" in response_text:
                raise ValueError('登录状态无效，请检查Cookie处理')
            raise ValueError(f"解析签到响应失败: {str(e)}\n\n原始响应: {response_text}")

        # 发送签到结果到 Telegram
        send_message(账号信息 + 用户信息 + 签到结果, BotToken, ChatID)
        return 签到结果

    except Exception as error:
        # 捕获异常，打印错误并发送错误信息到 Telegram
        print(f'{user}账号签到异常:', error)
        签到结果 = f"签到过程发生错误: {error}"
        send_message(签到结果, BotToken, ChatID)
        return 签到结果

# 主程序执行逻辑
if __name__ == "__main__":

    # 读取配置
    config = generate_config()

    # 读取全局配置
    domain = config['domain']
    BotToken = config['BotToken']
    ChatID = config['ChatID']

    # 循环执行每个账号的签到任务
    for account in config.get("accounts", []):
        print("----------------------------------签到信息----------------------------------")
        print(checkin(account, domain, BotToken, ChatID))
        print("---------------------------------------------------------------------------")
