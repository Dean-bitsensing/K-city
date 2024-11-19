import base64
import gzip
import json
from typing import Optional, Dict, Any, List, Union
import requests
from app.models.new_fusion import your_schema_pb2



class KcityApiClient:
    """K city server로 API호출을 담당하는 """

    def __init__(self, base_url: str):
        """
        Init

        Args:
            base_url (str): Kcity Server Base url. 회사내부의 경우 192.168.0.209:20000
        """
        self.base_url = base_url.rstrip('/')  # 변수끝에있는 slash 삭제
        self.timeout = 30  # Default timeout

        # API endpoints
        self._DEVICE_ENDPOINT = "/api/kcity/v1/map/devices"
        self._MAP_OBJECT_ENDPOINT = "/api/kcity/v1/map/object-data"

    class ApiResponse:
        def __init__(self, success: bool, data: Any = None, error: str = None):
            self.success = success
            self.data = data
            self.error = error

        def __bool__(self):
            return self.success

    def get_devices(self, group_code: str) -> ApiResponse:
        """
        GROUP에 속한 Device정보를 조회하는 API

        Args:
            group_code (str): Group Code. Verona의 경우 r2U9A8fUA2

        Returns:
            ApiResponse 스키마
            "success": bool. 성공적일경우 true
            "data": List<>로 하나의 리스트 요소마다 그룹이 있음.
            ㄴ 하나의 리스트요소
                ㄴ"id": 1,
                ㄴ"locationName": "verona_1",
                ㄴ"status": "ACTIVE",
                ㄴ"groupCode": "r2U9A8fUA2",
                ㄴ"devices": List로 각 요소마다 Device정보를 포함.
                    ㄴ "device" :
                        ㄴ "id": 1,
                        ㄴ "deviceId": "A04B200003",
                        ㄴ "lat": 45.43077362571124,
                        ㄴ "lng": 10.987699417245228,
                        ㄴ "headingAngle": 352.16,
                        ㄴ "alias": "Device 1",
                        ㄴ "color": "#f91b5e"
                        ...
                ...
        """
        params = {'group-code': group_code}
        result = self._make_request(self._DEVICE_ENDPOINT, params)

        if result and isinstance(result, list):
            # Device 데이터 구조 검증
            devices_data = []
            for location in result:
                if 'devices' in location:
                    devices_data.extend(location['devices'])
            return self.ApiResponse(True, devices_data)
        return self.ApiResponse(False, error="Failed to fetch device data")

    def get_map_objects(self, group_code: str, datetime_str: str) -> ApiResponse:
        """
        Object Data 조회 API

        Args:
            group_code (str): 조회할 Object data group 의 group code
            datetime_str (str): 'YYYY-MM-DD HH:MM:SS' 형식의 날짜 포맷(띄어쓰기에 유의해 주세용)

        Returns:
            ApiResponse: 성공적인 데이터일 경우 success True이고 data필드에 실질적인 데이터 포함.
            data 필드의 구조
            data
            ㄴ datetime : datetime
            ㄴ mergedData : 압축된 object data
            ㄴ deviceGroup
                ㄴ locationName : location name ex)verona_1
                ㄴ status : ex)ACTIVE
                ㄴ groupCode : groupCode ex) r2U9A8fUA2
        """
        params = {
            'group-code': group_code,
            'datetime': datetime_str
        }
        result = self._make_request(self._MAP_OBJECT_ENDPOINT, params)

        if result:
            return self.ApiResponse(True, result)
        return self.ApiResponse(False, error="Failed to fetch map object data")

    def _make_request(self, endpoint: str, params: dict) -> Optional[Any]:
        """
        API로 HTTP Request 전송

        Args:
            endpoint (str): API endpoint
            params (dict): Query parameters

        Returns:
            Optional[Any]: Response data if successful, None otherwise
        """
        try:
            url = f"{self.base_url}{endpoint}"

            response = requests.get(
                url,
                params=params,
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            if result.get('success'):
                return result['data']
            else:
                print(f"API request failed: {result.get('message', 'No error message provided')}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")
            return None
        except ValueError as e:
            print(f"Error parsing JSON response: {e}")
            return None

    def set_timeout(self, timeout: int) -> None:
        """Set request timeout in seconds"""
        self.timeout = timeout


def decompress_data(compressed_data: str) :
    """
    Base64로 인코딩되고 gzip으로 압축된 데이터를 디코딩하고 압축해제하는 함수

    Args:
        compressed_data (str): Base64로 인코딩되고 gzip으로 압축된 데이터

    Returns:
        Union[dict, str]: 압축해제된 데이터. JSON 형식이면 dict로, 아니면 str로 반환

    Raises:
        ValueError: 잘못된 데이터 형식이나 디코딩/압축해제 실패시
    """
    try:
        # Base64 디코딩
        decoded_data = base64.b64decode(compressed_data)

        # Gzip 압축해제
        decompressed_data = gzip.decompress(decoded_data)

        # 결과를 문자열로 디코딩
        result = decompressed_data


        return result

    except Exception as e:
        raise ValueError(f"데이터 디코딩/압축해제 실패: {str(e)}")


    
   
        




    