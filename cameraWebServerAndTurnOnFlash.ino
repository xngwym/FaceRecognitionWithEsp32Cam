#include <WebServer.h>
#include <WiFi.h>
#include <esp32cam.h>

#define LED_RED 14
#define LED_BLUE 2

const char* AP_SSID = "ESP32-Cam-AP";
const char* AP_PASS = "password";

WebServer server(80); // khơi tạo đối tượng webserver dùng để xử lý các yêu cầu http và đặt trên cổng 80
String receivedData;  // Biến lưu trữ dữ liệu từ Python

static auto midRes = esp32cam::Resolution::find(350, 530); // khơi tạo độ phân giải của camera

// hàm chụp ảnh từ cam và gửi đến client qua http
void serveJpg() {
  auto frame = esp32cam::capture(); // tạo một đối tượng frame và gán là giá trị là một khung hình chụp từ cam
  if (frame == nullptr) { // kiểm tra nếu frame là rỗng thì return
    Serial.println("CAPTURE FAIL");
    server.send(503, "", "");
    return;
  }

  Serial.printf("CAPTURE OK %dx%d %db\n", frame->getWidth(), frame->getHeight(),
                static_cast<int>(frame->size())); // in ra kích thước của bức ảnh lên serial

  server.setContentLength(frame->size()); // báo cho trình duyệt biết kích thước dữ liệu mà trình duyệt sẽ nhận được
  server.send(200, "image/jpeg"); // gửi phản hổi http với mã trạng thái 200 nghĩa là OK
  WiFiClient client = server.client(); // kết nối tới trình duyệt
  frame->writeTo(client); // truyền hình ảnh tới trình duyệt thông qua kết nối bên trên
}

// Thay đổi độ phân giải của của camera và gọi hàm serverJpg để gửi hình ảnh
void handleJpgMid() {
  if (!esp32cam::Camera.changeResolution(midRes)) {
    Serial.println("SET-MID-RES FAIL");
  }
  serveJpg();
}

// Xử lý request từ máy chủ gửi về
void handlePythonRequest() {
  receivedData = server.arg("data");  // Lấy dữ liệu từ yêu cầu POST

  // Xử lý sự kiện toggle-flash
  if (receivedData.equals("TRUE")) { // nếu request gửi về là true thì nháy led blue nếu khác true thì nháy led red
    digitalWrite(LED_BLUE, HIGH);
    delay(500);
    digitalWrite(LED_BLUE, LOW);
  } else {
    digitalWrite(LED_RED, HIGH);
    delay(500);
    digitalWrite(LED_RED, LOW);
  }

  // Gửi phản hồi về Python (nếu cần)
  server.send(200, "text/plain", "Data received: " + receivedData);
}

void setup() {
  Serial.begin(115200);
  Serial.println();

  pinMode(LED_BLUE, OUTPUT);
  pinMode(LED_RED, OUTPUT);

  // Thiết lập chế độ Access Point
  WiFi.softAP(AP_SSID, AP_PASS); // thiết lập một điểm truy cập các thiêt bị khác có thể kêt nối vào thông qua mạng wifi này
  IPAddress apIP = WiFi.softAPIP(); // lấy địa chỉ của điêm truy cập
  String ip = apIP.toString(); // ép kiểu thành chuỗi
  Serial.print("AP IP Address: "); 
  Serial.println(apIP); // in ra địa chỉ ip trên serial

  {
    using namespace esp32cam;
    Config cfg; // tạo đối tượng config trong namespace esp32cam đối tượng này chứa các thiết lập camera
    cfg.setPins(pins::AiThinker); // Thiết lập chân (pins) sử dụng cho module camera
    cfg.setResolution(hiRes); // Thiết lập độ phân giải cho camera
    cfg.setBufferCount(2); // Thiết lập số lượng bộ đệm sử dụng bởi camera
    cfg.setJpeg(80); //  Thiết lập chất lượng nén JPEG 

    bool ok = Camera.begin(cfg); //  Khởi tạo camera với các thiết lập đã được cấu hình bên trên
    Serial.println(ok ? "CAMERA OK" : "CAMERA FAIL"); // Hiển thị thông báo trạng thái của camera 
  }

  Serial.println("http://" + ip + "/cam-mid.jpg"); // in ra url

  server.on("/cam-mid.jpg", HTTP_GET, handleJpgMid); 
  server.on("/python-request", HTTP_POST, handlePythonRequest);  // Thêm sự kiện xử lý yêu cầu POST từ Python

  server.begin(); // bắt đầu chạy web server
}

void loop() {
  server.handleClient(); // xử lý các yêu cầu từ client đã kết nối đến web server
}
