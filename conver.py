import json
import requests
import logging
from requests.exceptions import Timeout, RequestException
import sys
from datetime import date

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def fetch_json_with_retry(url, max_retries=10, timeout=30):
    retry_count = 1
    while retry_count < max_retries:
        try:
            logging.info(f"第{retry_count}次尝试请求 {url}")
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except (Timeout, RequestException) as e:
            logging.error(f"第{retry_count+1}次请求 {url} 时发生错误: {e}", extra={'retries': retry_count + 1})
            retry_count += 1
    logging.error(f"无法获取 {url} 的数据，重试次数已达上限")
    return None


xray_data = fetch_json_with_retry('https://download.fanyu.site/maimai/alias.json')
yuzuai_data = fetch_json_with_retry('https://api.yuzuai.xyz/maimaidx/maimaidxalias')
music_data = fetch_json_with_retry('https://www.diving-fish.com/api/maimaidxprober/music_data')
version_data = fetch_json_with_retry('https://bucket-1256206908.cos.ap-shanghai.myqcloud.com/update.json')

if not xray_data:
    logging.error("无法获取xray数据")
elif not yuzuai_data:
    logging.error("无法获取yuzuai数据")
elif not music_data:
    logging.error("无法获取music数据")
elif not version_data:
    logging.error("无法获取version数据")
else:
    converted_data = {}
    for key, value in xray_data.items():
        if value and len(value) > 0:
            alias_list = [k for k, v in xray_data.items() if v == value]
            converted_data[value[0]] = {"Name": key, "Alias": alias_list}
    logging.info("别名转换完成")

    for id, data in yuzuai_data.items():
        if id in converted_data:
            merged_alias = list(set(data['Alias'] + converted_data[id]['Alias']))
            data['Alias'] = sorted(merged_alias)
    logging.info("别名合并完成")

    with open('alias.json', 'w', encoding='utf-8') as file:
        json.dump(yuzuai_data, file, ensure_ascii=False, separators=(',', ':'))
    logging.info("别名写入完成")

    data_json = []
    for item in music_data:
        item_id = item["id"]
        if item_id in yuzuai_data:
            item["alias"] = yuzuai_data[item_id]["Alias"]
        data_json.append(item)
    logging.info("数据合并完成")

    with open('data.json', 'w', encoding='utf-8') as file:
        json.dump(data_json, file, ensure_ascii=False, separators=(',', ':'))
    logging.info("数据写入完成")

    current_date = date.today().strftime("%Y%m%d")
    new_data = {
        "alias_version": current_date,
        "alias_url": "https://raw.githubusercontent.com/Becods/maimaiDX-CN-songs-alias-database/datas/alias.json"
    }
    version_data.update(new_data)
    logging.info("版本合并完成")
    with open('update.json', 'w', encoding='utf-8') as file:
        json.dump(version_data, file, ensure_ascii=False, separators=(',', ':'))
    logging.info("版本写入完成")
