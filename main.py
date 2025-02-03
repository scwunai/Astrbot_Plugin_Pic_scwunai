from astrbot.api.message_components import *
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
import requests
from typing import Union, List, Optional, Dict

@register("Pic_Get", "scwunai", "一个简单的二次元图片获取工具", "1.0.0")
class PicPlugin(Star):
    def __init__(self, context: Context,config: dict = None):
        super().__init__(context)
        self.config = config
        self.r18 = self.config.get("R18开关，0非R18，1R18，2混合", 0)
        self.num = self.config.get("请求图片数量", 1)
        self.proxy = self.config.get("pixiv 反代服务地址", "i.pixiv.re")
        self.dsc = self.config.get("禁用自动转换", False)
        self.exclude_ai = self.config.get("排除AI", False)
        self.method = self.config.get("请求方法", "GET")
        

    
    # 注册指令的装饰器。指令名为 helloworld
    @filter.command("pic")
    async def pic(self, event: AstrMessageEvent,
            keyword: Optional[str] = None,
            tag: Optional[Union[List[str], List[List[str]]]] = None,
            size: Optional[List[str]] = None,
            aspect_ratio: Optional[str] = None,):
        

        def get_pic(
            r18: int = 0,
            num: int = 1,
            uid: Optional[List[int]] = None,
            keyword: Optional[str] = None,
            tag: Optional[Union[List[str], List[List[str]]]] = None,
            size: Optional[List[str]] = None,
            proxy: str = "i.pixiv.re",
            date_after: Optional[int] = None,
            date_before: Optional[int] = None,
            dsc: bool = False,
            exclude_ai: bool = False,
            aspect_ratio: Optional[str] = None,
            method: str = "GET"
        ) -> dict:
            """
            调用 lolicon.app setu API v2
            
            :param r18: 0非R18，1R18，2混合
            :param num: 返回数量(1-20)
            :param uid: 作者UID列表
            :param keyword: 关键词模糊匹配
            :param tag: 标签匹配规则
            :param size: 图片规格列表
            :param proxy: 反代服务地址
            :param date_after: 上传时间之后(毫秒时间戳)
            :param date_before: 上传时间之前(毫秒时间戳)
            :param dsc: 禁用自动转换
            :param exclude_ai: 排除AI作品
            :param aspect_ratio: 长宽比筛选
            :param method: 请求方法 GET/POST
            :return: API响应字典
            """
            url = "https://api.lolicon.app/setu/v2"
            
            params = {
                "r18": r18,
                "num": max(1, min(20, num)),
                "keyword": keyword,
                "proxy": proxy,
                "dsc": str(dsc).lower() if method == "GET" else dsc,
                "excludeAI": str(exclude_ai).lower() if method == "GET" else exclude_ai,
                "aspectRatio": aspect_ratio
            }
            
            # 处理数组参数
            array_params = {
                "uid": uid,
                "tag": tag,
                "size": size or ["original"]
            }
            
            # 处理时间参数
            if date_after:
                params["dateAfter"] = date_after
            if date_before:
                params["dateBefore"] = date_before

            # GET请求处理
            if method.upper() == "GET":
                for key, value in array_params.items():
                    if value:
                        if key == "tag" and isinstance(value[0], list):
                            params[key] = ["|".join(t) for t in value]
                        else:
                            params[key] = value
                response = requests.get(url, params=params)
            
            # POST请求处理
            elif method.upper() == "POST":
                payload = {k: v for k, v in params.items() if v is not None}
                
                # 处理数组参数格式
                for key in array_params:
                    if array_params[key]:
                        if key == "tag" and isinstance(array_params[key][0], list):
                            payload[key] = array_params[key]
                        else:
                            payload[key] = array_params[key]
                
                # 转换布尔值
                for bool_key in ["dsc", "excludeAI"]:
                    if bool_key in payload:
                        payload[bool_key] = bool(payload[bool_key])
                
                response = requests.post(url, json=payload)
            
            else:
                raise ValueError("Invalid method, must be GET or POST")

            return response.json()

        def extract_pic_urls(response_data: Dict) -> List[str]:
            """
            从API响应中提取所有图片的原始URL
            
            :param response_data: API返回的字典数据
            :return: 图片URL列表，格式为["https://...", ...]
            """
            url_list = []
            
            # 验证数据结构
            if not isinstance(response_data, dict):
                return url_list
                
            data = response_data.get("data", [])
            
            for item in data:
                try:
                    # 获取原始规格图片URL
                    if "urls" in item and "original" in item["urls"]:
                        url_list.append(item["urls"]["original"])
                except (KeyError, TypeError):
                    continue
            
            return url_list


        pic_json = get_pic(r18 = self.r18,num = self.num, keyword = keyword, tag = tag, size = size, proxy = self.proxy, dsc = self.dsc, exclude_ai = self.exclude_ai, aspect_ratio = aspect_ratio, method = self.method)
        if pic_json:
            At(qq=event.get_sender_id()),
            Plain("图片返回："),
            Image.fromURL(extract_pic_urls(pic_json)[0], size='small'),
        else:
            Plain("请求失败，请检查配置")
