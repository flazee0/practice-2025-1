key = "39c7f5f27amsh776f6ae3f521db1p13a141jsn6be7ebe18f4a"


import cv2
import numpy as np
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from urllib.parse import urlparse
import logging
import json
from io import BytesIO
from dataclasses import dataclass

import base64
from PIL import Image
import io
#import os
import matplotlib.pyplot as plt

CITY = "Moscow"                      # Город для погоды

def get_weather(city):
    """Получаем текущую погоду через WeatherAPI"""
    try:
        url = "https://weatherapi-com.p.rapidapi.com/current.json"
        querystring = {"q": city}
        headers = {
            "X-RapidAPI-Key": key,
            "X-RapidAPI-Host": "weatherapi-com.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        response.raise_for_status()  # Проверяем HTTP ошибки
        return response.json()
    
    except Exception as e:
        print(f"❌ Ошибка получения погоды: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"Ответ сервера: {e.response.text}")
        return None

def generate_clothing_description(weather_data):
    """Генерируем текстовое описание одежды по погоде"""
    try:
        temp = weather_data['current']['temp_c']
        condition = weather_data['current']['condition']['text'].lower()
        
        # Основная одежда по температуре
        if temp < 0:
            desc = "thick down jacket, warm hat, scarf and gloves"
        elif temp < 10:
            desc = "warm coat, sweater and jeans"
        elif temp < 20:
            desc = "light jacket with t-shirt"
        else:
            desc = "t-shirt and shorts"
        
        # Аксессуары по условиям
        if "rain" in condition:
            desc += ", waterproof boots and umbrella"
        elif "snow" in condition:
            desc += ", snow boots"
        if weather_data['current']['wind_kph'] > 15:
            desc += ", windproof jacket"
        
        return desc
    
    except KeyError as e:
        print(f"❌ Неожиданная структура данных о погоде: {str(e)}")
        return "casual outfit"  # Возвращаем описание по умолчанию

@dataclass
class TryOnDiffusionAPIResponse:
    status_code: int
    image: np.ndarray = None
    response_data: bytes = None
    error_details: str = None
    seed: int = None


class TryOnDiffusionClient:
    def __init__(self, base_url: str = "http://localhost:8000/", api_key: str = ""):
        self._logger = logging.getLogger("try_on_diffusion_client")
        self._base_url = base_url
        self._api_key = api_key

        if self._base_url[-1] == "/":
            self._base_url = self._base_url[:-1]

        parsed_url = urlparse(self._base_url)

        self._rapidapi_host = parsed_url.netloc if parsed_url.netloc.endswith(".rapidapi.com") else None

        if self._rapidapi_host is not None:
            self._logger.info(f"Using RapidAPI proxy: {self._rapidapi_host}")

    @staticmethod
    def _image_to_upload_file(image: np.ndarray) -> tuple:
        _, jpeg_data = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 99])
        jpeg_data = jpeg_data.tobytes()

        fp = BytesIO(jpeg_data)

        return "image.jpg", fp, "image/jpeg"

    def try_on_file(
        self,
        clothing_image: np.ndarray = None,
        clothing_prompt: str = None,
        avatar_image: np.ndarray = None,
        avatar_prompt: str = None,
        avatar_sex: str = None,
        background_image: np.ndarray = None,
        background_prompt: str = None,
        seed: int = -1,
        raw_response: bool = False,
    ) -> TryOnDiffusionAPIResponse:
        url = self._base_url + "/try-on-file"

        request_data = {"seed": str(seed)}

        if clothing_image is not None:
            request_data["clothing_image"] = self._image_to_upload_file(clothing_image)

        if clothing_prompt is not None:
            request_data["clothing_prompt"] = clothing_prompt

        if avatar_image is not None:
            request_data["avatar_image"] = self._image_to_upload_file(avatar_image)

        if avatar_prompt is not None:
            request_data["avatar_prompt"] = avatar_prompt

        if avatar_sex is not None:
            request_data["avatar_sex"] = avatar_sex

        if background_image is not None:
            request_data["background_image"] = self._image_to_upload_file(background_image)

        if background_prompt is not None:
            request_data["background_prompt"] = background_prompt

        multipart_data = MultipartEncoder(fields=request_data)

        headers = {"Content-Type": multipart_data.content_type}

        if self._rapidapi_host is not None:
            headers["X-RapidAPI-Key"] = self._api_key
            headers["X-RapidAPI-Host"] = self._rapidapi_host
        else:
            headers["X-API-Key"] = self._api_key

        try:
            response = requests.post(
                url,
                data=multipart_data,
                headers=headers,
            )
        except Exception as e:
            self._logger.error(e, exc_info=True)
            return TryOnDiffusionAPIResponse(status_code=0)

        if response.status_code != 200:
            self._logger.warning(f"Request failed, status code: {response.status_code}, response: {response.content}")

        result = TryOnDiffusionAPIResponse(status_code=response.status_code)

        if not raw_response and response.status_code == 200:
            try:
                result.image = cv2.imdecode(np.frombuffer(response.content, np.uint8), cv2.IMREAD_COLOR)
            except:
                result.image = None
        else:
            result.response_data = response.content

        if result.status_code == 200:
            if "X-Seed" in response.headers:
                result.seed = int(response.headers["X-Seed"])
        else:
            try:
                response_json = (
                    json.loads(result.response_data.decode("utf-8")) if result.response_data is not None else None
                )

                if response_json is not None and "detail" in response_json:
                    result.error_details = response_json["detail"]
            except:
                result.error_details = None

        return result

def main():
    # 1. Получаем погоду
    print(f"🔄 Получаем погоду для {CITY}...")
    weather = get_weather(CITY)
    if not weather:
        return
        
    print(f"🌡 Погода в {CITY}: {weather['current']['temp_c']}°C")
    print(f"☁️ Состояние: {weather['current']['condition']['text']}")
    print(f"💨 Ветер: {weather['current']['wind_kph']} км/ч")
        
    # 2. Генерируем описание одежды
    clothing_desc = generate_clothing_description(weather)
    print(f"\n👕 Рекомендуемый лук: {clothing_desc}")

    vtond = TryOnDiffusionClient(base_url="https://try-on-diffusion.p.rapidapi.com", api_key=key)


    image = cv2.imread("woman.jpg")

    result = vtond.try_on_file(avatar_image=image, clothing_prompt=clothing_desc, seed=-1)
    
    plt.figure(figsize=(10, 10))
    plt.imshow(result.image)
    plt.axis("off")
    plt.title(f"Виртуальная примерка для {CITY}\n"
         f"{weather['current']['temp_c']}°C, {weather['current']['condition']['text']}")
    plt.show()

if __name__ == "__main__":
    main()