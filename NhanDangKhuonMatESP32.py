import cv2
import face_recognition
import os
import numpy as  np
from datetime import datetime
import urllib.request
import requests
import mysql.connector


# Hàm mã hóa hình ảnh trong tệp
def imagesEncoding(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) # Chuyển từ bgr sang rgb
        encode = face_recognition.face_encodings(img)[0] # Mã hóa hình ảnh
        encodeList.append(encode) # Thêm hình ảnh mã hóa vào mảng
    return encodeList # Trả về mảng các hình ảnh được mã hóa

# Hàm lưu dữ liệu vào mysql
def saveData(name):
    _date = datetime.now().strftime("%Y-%m-%d")
    _time = datetime.now().strftime("%H:%M:%S")

    # kết nối tới cơ sở dữ liệu
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='diemdanh'
    )

    # Tạo con trỏ thực thi truy vấn
    cursor = connection.cursor()

    # Truy vấn cơ sở dữ liệu
    query = "INSERT INTO diemdanh VALUES (%s, %s, %s)"
    cursor.execute(query, (name, _date, _time)) # Truy vấn tới csdl

    connection.commit() # Lưu các thay đổi vào csdl
    cursor.close() # Đóng con trỏ
    connection.close() # Ngắt kết nối tới csdl


# load ảnh từ kho nhận dạng
path = r"original_images"
images = []
classNames = []
myList = os.listdir(path) # Lấy danh sách các tệp trong thư mục

for cl in myList:
    curImg = cv2.imread(f"{path}/{cl}")
    images.append(curImg)
    classNames.append(os.path.splitext(cl)[0]) # splitext sẽ tách path ra thành 2 phần, phần đuôi mở rộng và phần mở rộng

encodeListKnow = imagesEncoding(images) # Hình ảnh trong tệp được mã hóa và lưu vào list
print("ENCRYPTION SUCCESSFUL")

# khơi động webcam
url = f'http://192.168.4.1/cam-mid.jpg'
urlRequest = f"http://192.168.4.1/python-request"

while True:
    frame = urllib.request.urlopen(url) # Lấy hình ảnh từ webserver
    frame = np.array(bytearray(frame.read()), dtype=np.uint8) # Đọc hình ảnh và chuyển thành mảng byte, đặt kiểu dữ liệu uint8 biểu diễn dữ liệu hình ảnh từ 0-255
    frame = cv2.imdecode(frame, -1) # Giải mã data từ mảng byte thành đối tượng hình ảnh opencv có thể sử dụng
    framS = cv2.resize(frame, (0,0), None, fx = 0.5, fy = 0.5)
    framS = cv2.cvtColor(framS, cv2.COLOR_BGR2RGB) # Chuyển đổi hình ảnh từ hệ màu bgr sang rgb

    # Xác định vị trí khuôn mặt trên cam và encode hình ảnh trên cam
    facecurFrame = face_recognition.face_locations(framS) # Lấy vị trí của khuông mặt
    encodecurFrame = face_recognition.face_encodings(framS) # Mã hóa hình ảnh

    for encodeFace, faceLoc in zip(encodecurFrame, facecurFrame): # Lấy từng khuôn mặt và vị trí khuôn mặt hiện tại theo cặp
        matches = face_recognition.compare_faces(encodeListKnow, encodeFace) # So sách khuôn mặt được mã hóa lấy từ camera và khuôn mặt được mã hóa trong thư mục
        faceDis = face_recognition.face_distance(encodeListKnow, encodeFace) # Tính toán khoảng cách độ tương đồng giữa 2 khuôn mặt
        matchIndex = np.argmin(faceDis) # Lấy ra chỉ số gương mặt có độ tương đồng cao nhất

        if faceDis[matchIndex] < 0.55:
            name = classNames[matchIndex].upper() # Trả về tên của người nhận diện từ danh sách và chuyển thành chữ hoa
            saveData(name)  # Lưu dữ liệu vào database
            data_to_send = {'data': 'TRUE'} # Dữ liệu cần gửi lên
            response = requests.post(urlRequest, data = data_to_send) # Gửi yêu cầu POST
        else:
            name = "Unknow"
            data_to_send = {'data': 'FALSE'}
            response = requests.post(urlRequest, data=data_to_send)
        # Hiển thị lên màn hình và vẽ hinh chữ` nhật khuôn mặt
        y1, x2, y2, x1 = faceLoc
        y1, x2, y2, x1 = y1*2, x2*2, y2*2, x1*2
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
        cv2.putText(frame, name, (x2, y2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

    cv2.imshow("Xuan Nguyen", frame)
    if cv2.waitKey(1) == ord("q"):
        break

cv2.destroyAllWindows() # Thoát tất cả cửa sổ


