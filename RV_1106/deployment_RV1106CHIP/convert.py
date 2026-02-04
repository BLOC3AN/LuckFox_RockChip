import sys
import os
from rknn.api import RKNN

# ==============================================================================
# Cấu hình đường dẫn (Lấy từ Environment Variable)
# ==============================================================================
# ==============================================================================
# Cấu hình đường dẫn (Lấy từ Environment Variable)
# ==============================================================================
# Default fallback values are provided just in case
ONNX_FILENAME = os.getenv('ONNX_FILE', 'tag_det.onnx')
RKNN_FILENAME = os.getenv('RKNN_FILE', 'tag_det_rv1106.rknn')
TARGET_PLATFORM = os.getenv('TARGET_PLATFORM', 'rv1106')
QUANTIZE_ON = os.getenv('QUANTIZE', 'True').lower() == 'true'

# Đường dẫn tuyệt đối (Mirror từ Host vào Docker)
ONNX_MODEL = f'/home/ubuntu/data/rockchip/RV_1106/models/{ONNX_FILENAME}'
RKNN_MODEL = f'/home/ubuntu/data/rockchip/RV_1106/models/{RKNN_FILENAME}'
DATASET_TXT = '/home/ubuntu/data/rockchip/RV_1106/dataset/txt/data.txt'


if __name__ == '__main__':
    # Kiểm tra file đầu vào
    if not os.path.exists(ONNX_MODEL):
        print(f"❌ Error: ONNX model not found at {ONNX_MODEL}")
        print("Vui lòng đặt file model.onnx vào thư mục workspace/model/")
        sys.exit(1)

    if QUANTIZE_ON and not os.path.exists(DATASET_TXT):
        print(f"❌ Error: Dataset file not found at {DATASET_TXT}")
        print("Vui lòng đặt ảnh vào workspace/dataset/ và tạo file dataset.txt liệt kê tên ảnh.")
        sys.exit(1)

    # 1. Khởi tạo RKNN
    rknn = RKNN(verbose=True)

    # 2. Cấu hình cho RV1106
    print('--> Config model for RV1106')
    # Lưu ý: Sửa mean_values và std_values nếu model của bạn cần tiền xử lý khác
    rknn.config(
        mean_values=[[0, 0, 0]], 
        std_values=[[255, 255, 255]], 
        target_platform=TARGET_PLATFORM, 
        quantized_algorithm="normal"
    )

    # 3. Load ONNX model
    print('--> Loading ONNX model')
    ret = rknn.load_onnx(model=ONNX_MODEL)
    if ret != 0:
        print('Load model failed!')
        sys.exit(ret)

    # 4. Build model (Quantization INT8)
    print('--> Building model (INT8 Quantization)')
    ret = rknn.build(do_quantization=QUANTIZE_ON, dataset=DATASET_TXT)
    if ret != 0:
        print('Build model failed!')
        sys.exit(ret)

    # 5. Export RKNN
    print('--> Exporting RKNN model')
    ret = rknn.export_rknn(RKNN_MODEL)
    if ret != 0:
        print('Export rknn model failed!')
        sys.exit(ret)

    print(f'✅ Chuyển đổi thành công! File lưu tại: {RKNN_MODEL}')
    rknn.release()
