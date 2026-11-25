/*
  Cấu hình thống kê truy cập.

  Trang này chạy trên GitHub Pages (chỉ có file tĩnh), nên khách vào xem KHÔNG thể tự ghi vào data/stats.json.
  Khi nối MongoDB (qua một API nhỏ), chỉ cần điền địa chỉ API vào `api` bên dưới:

    window.NT_STATS = { api: "https://ten-api-cua-ban.example.com" };

  API cần 2 đường:

    POST {api}/collect         (nhận mỗi lượt xem, KHÔNG cần khóa)
      body (text/plain chứa JSON):
        { t: 1764057600000,        // thời điểm (ms)
          path: "/index.html",     // trang
          ref: "facebook.com",     // nguồn giới thiệu (chỉ tên miền), có thể rỗng
          vid: "…",                // mã khách ngẫu nhiên lưu trên máy (đếm khách riêng biệt)
          sid: "…",                // mã phiên (mỗi tab)
          lang: "vi-VN", tz: "Asia/Ho_Chi_Minh", w: 390 }
      Máy chủ tự lấy IP từ request, tra ra quốc gia / vùng / thành phố,
      rồi LƯU IP ĐÃ BĂM (ví dụ sha256 + muối bí mật, cắt 12 ký tự) — đừng lưu IP gốc.

    GET {api}/stats?from=YYYY-MM-DD&to=YYYY-MM-DD   (cần header  x-stats-key: <khóa của bạn>)
      trả về đúng cấu trúc như data/stats.json:
        { daily:      [{ date, views, visitors }],
          byLocation: [{ date, country, region, city, views, visitors }],
          byIp:       [{ date, ipHash, country, city, views }] }

  Khi api để trống: không gửi gì đi cả, trang thống kê đọc data/stats.json.
*/
window.NT_STATS = { api: "" };
