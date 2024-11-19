from .kcity_api_client import *
from .your_schema_pb2 import *
from .fusion_module import *

def fusion_main():
    # 클라이언트 초기화
    client = KcityApiClient("http://192.168.0.209:20000")

    # 예시 사용
    GROUP_CODE = "r2U9A8fUA2"
    DATETIME = "2024-10-18 15:00:00"

    # Device 데이터 조회
    device_response = client.get_devices(GROUP_CODE)
    if device_response:
        devices = device_response.data
        # print(f"Found {len(devices)} devices")
        # for device in devices:
        #     print(f"Device {device}:")
        #     print(device['deviceId'])
    else:
        print(f"Error: {device_response.error}")

    #Map Object 데이터 조회
    map_response = client.get_map_objects(GROUP_CODE, DATETIME)
    # print("####################################################################################################")
    if map_response:
        map_data = map_response.data
        decompressed_result = decompress_data(map_data['mergedData'])
        root_message = your_schema_pb2.Root()
        root_message.ParseFromString(decompressed_result)

        # print(f"map_data {root_message}")
    else:
        print(f"Error: {map_response.error}")

    # fusion Loop 밖에서 선언되어야됨
    esterno = Fusion()
    interno = Fusion()
    verona = Fusion()
    
    fusion_result = fusion(esterno, interno,verona, root_message, devices)

    return fusion_result

    