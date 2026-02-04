# Deploy RKNN Conversion Environment for RV1106

Dựa trên các nguồn tài liệu được cung cấp, dưới đây là quy trình chi tiết để sử dụng Docker chạy **RKNN-Toolkit2** nhằm chuyển đổi model từ **ONNX (Float32)** sang **INT8 (RKNN)** dành cho chip **RV1106** (Luckfox Pico Pro/Max/Ultra).

## 1. Chuẩn bị môi trường Docker
Vì việc cài đặt môi trường trực tiếp trên Ubuntu có thể gặp vấn đề về phiên bản Python và thư viện phụ thuộc, việc sử dụng Docker là phương án tối ưu.
Môi trường này đã được cấu hình sẵn trong thư mục `deployment_RV1106CHIP/`.

## 2. Cấu hình Project
Thư mục dự án đã được tổ chức như sau:
```text
.
├── deployment_RV1106CHIP/  # Chứa file cấu hình deploy
│   ├── .env                # File cấu hình biến môi trường (Model name, Platform...)
│   ├── docker-compose.yml  # Config Docker mount
│   └── convert.py          # Script chuyển đổi (tự động)
├── dataset/                # Chứa ảnh dataset
│   └── txt/
│       └── data.txt        # File list ảnh (đường dẫn tuyệt đối hoặc tương đối)
└── models/                 # Chứa model ONNX và file RKNN đầu ra
    └── tag_det.onnx        
```

### Chỉnh sửa `.env`
Bạn chỉ cần sửa file `deployment_RV1106CHIP/.env` để thay đổi cấu hình:
```bash
# Tên file model ONNX (nằm trong thư mục models gốc)
ONNX_FILE=tag_det.onnx

# Tên file model RKNN đầu ra (sẽ lưu vào thư mục models gốc)
RKNN_FILE=tag_det_rv1106.rknn

# Platform đích (rv1106 hoặc rv1103)
TARGET_PLATFORM=rv1106

# Bật Quantization (True/False)
QUANTIZE=True
```

## 3. Chạy chuyển đổi
Di chuyển vào thư mục deploy và chạy Docker Compose:

```bash
cd deployment_RV1106CHIP
sudo docker compose up
```

Lệnh này sẽ:
1.  Tự động mount folder `models` và `dataset` của bạn vào container.
2.  Chạy script `convert.py` với các thông số từ file `.env`.
3.  Xuất file `.rknn` ra folder `models/` ngay trên máy host.

## 4. Các điểm quan trọng cần lưu ý cho RV1106
1.  **Platform:** Bắt buộc phải cấu hình `target_platform='rv1106'` (hoặc `rv1103` tùy board), nếu không model sẽ không chạy được trên NPU của Luckfox Pico.
2.  **Quantization (INT8):**
    *   Luckfox Pico (RV1106) hỗ trợ tốt nhất cho tính toán INT8.
    *   Nếu bạn chọn `do_quantization=False`, model sẽ chạy ở chế độ FP16 (nếu chip hỗ trợ) hoặc giả lập FP, nhưng RV1106 NPU 4.0 tối ưu nhất cho INT8 hỗn hợp.
    *   Lưu ý từ tài liệu: "luckfox-pico only supports int8 type inputs and outputs" (đầu vào/ra của NPU thường yêu cầu INT8, toolkit sẽ tự động chèn các lớp dequantize/quantize nếu cần, nhưng tốt nhất nên để INT8 thuần).
3.  **Hỗ trợ Operator:**
    *   Nên dùng công cụ **Netron** để kiểm tra model ONNX trước. Nếu có các lớp (layer) mà NPU RV1106 chưa hỗ trợ (ví dụ: một số phép toán Layer Normalization phức tạp ở cuối model), bạn nên cắt bỏ chúng khỏi ONNX và thực hiện phần đó bằng CPU trong code ứng dụng C++.

Sau khi chạy xong, file `.rknn` sẽ xuất hiện trong thư mục `models/` trên máy tính của bạn, sẵn sàng để copy vào bo mạch Luckfox Pico và chạy với C-API.