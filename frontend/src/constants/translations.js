export const TEXT = {
  vi: {
    header: {
      greeting: "Xin chào",
      subtitle: "Nhập nhật ký canh tác bằng giọng nói",
      vietnamese: "Tiếng Việt",
      english: "English",
      chooseLanguage: "Chọn ngôn ngữ",
      toggleTheme: "Đổi giao diện sáng tối",

      profile: "Hồ sơ cá nhân",
      myLogs: "Nhật ký của tôi",
      settings: "Cài đặt",
      logout: "Đăng xuất",
      account: "Tài khoản NextFarm",
    },

    workflow: {
      record: "Ghi âm",
      processing: "AI xử lý",
      review: "Kiểm tra",
      confirm: "Xác nhận",
    },

    record: {
      ready: "Nhấn để ghi âm",
      recording: "Đang ghi âm...",
      recorded: "Đã ghi âm",
      confirmed: "Nhật ký đã được xác nhận",

      startLabel: "Bắt đầu ghi âm",
      stopLabel: "Dừng ghi âm",
      confirmedLabel: "Nhật ký đã được xác nhận",

      browserUnsupported:
        "Trình duyệt không hỗ trợ chức năng ghi âm.",

      recordingError: "Ghi âm bị lỗi",
      recordingErrorMessage:
        "Không thể tiếp tục ghi âm. Vui lòng thử lại.",

      emptyAudio: "Không thu được âm thanh",
      emptyAudioMessage:
        "Bản ghi không có dữ liệu. Vui lòng thử lại và nói gần microphone hơn.",

      microphoneDenied:
        "Chưa được cấp quyền microphone",

      microphoneDeniedMessage:
        "Vui lòng cho phép trình duyệt sử dụng microphone.",

      microphoneNotFound:
        "Không tìm thấy microphone",

      microphoneNotFoundMessage:
        "Thiết bị không có microphone hoặc microphone đang không khả dụng.",

      microphoneUnavailable:
        "Không thể truy cập microphone",

      microphoneUnavailableMessage:
        "Không thể sử dụng microphone. Vui lòng thử lại.",

      audioReady:
        "Bản ghi đã sẵn sàng để gửi AI.",

      confirmedMessage:
        "Nhật ký đã được xác nhận. Hãy chọn Tạo nhật ký mới để tiếp tục.",
    },

    audioPlayer: {
      title: "Bản ghi vừa tạo",
      unsupported:
        "Trình duyệt không hỗ trợ phát audio.",
    },

    transcript: {
      title: "Nội dung ghi âm",
      aiProcessed: "AI đã xử lý",
      confirmed: "Đã xác nhận",

      placeholder:
        "Sau khi AI xử lý, nội dung chuyển đổi sẽ hiển thị tại đây...",

      ariaLabel:
        "Nội dung ghi âm chuyển thành văn bản",

      empty:
        "Chưa có nội dung ghi âm.",

      reviewTip:
        "Kiểm tra nhanh nội dung và sửa nếu AI nhận sai trước khi xác nhận.",

      success:
        "Nội dung đã được xác nhận và sẵn sàng gửi lên hệ thống.",
    },

    aiForm: {
      title: "Dữ liệu AI trích xuất",
      editable: "Có thể chỉnh sửa",
      confirmed: "Đã xác nhận",

      lot: "Lô canh tác",
      lotPlaceholder: "Ví dụ: A01",

      work: "Công việc",
      workPlaceholder: "Ví dụ: Bón phân",

      material: "Vật tư",
      materialPlaceholder: "Ví dụ: Phân NPK",

      quantity: "Số lượng",
      quantityPlaceholder: "Ví dụ: 20",

      unit: "Đơn vị",
      unitPlaceholder: "Ví dụ: kg",

      time: "Thời gian",

      empty:
        "Chưa có dữ liệu AI trích xuất.",

      editHint:
        "Chỉnh sửa nếu AI nhận sai trước khi xác nhận.",
    },

    actions: {
      delete: "Xóa bản ghi",
      recordAgain: "Ghi lại",
      sendAI: "Gửi AI",
      processing: "AI đang xử lý...",
      confirmLog: "Xác nhận nhật ký",
      confirmed: "Đã xác nhận",
      createNew: "Tạo nhật ký mới",
    },

    messages: {
      sending:
        "Đang gửi bản ghi đến AI Service...",

      processed:
        "Xử lý bản ghi thành công.",

      backendError:
        "Không thể kết nối AI Service. Hãy kiểm tra backend tại cổng 8000.",

      reviewBeforeConfirm:
        "Vui lòng kiểm tra nội dung ghi âm trước khi xác nhận.",

      confirmed:
        "Nhật ký đã được xác nhận.",
    },
  },

  en: {
    header: {
      greeting: "Hello",
      subtitle: "Create farming logs using your voice",
      vietnamese: "Vietnamese",
      english: "English",
      chooseLanguage: "Choose language",
      toggleTheme: "Toggle light/dark theme",

      profile: "Profile",
      myLogs: "My logs",
      settings: "Settings",
      logout: "Log out",
      account: "NextFarm account",
    },

    profile: "Profile",
    myLogs: "My logs",
    settings: "Settings",
    logout: "Log out",
    account: "NextFarm account",

    workflow: {
      record: "Record",
      processing: "AI Process",
      review: "Review",
      confirm: "Confirm",
    },

    record: {
      ready: "Tap to record",
      recording: "Recording...",
      recorded: "Recorded",
      confirmed: "Log confirmed",

      startLabel: "Start recording",
      stopLabel: "Stop recording",
      confirmedLabel: "Log confirmed",

      browserUnsupported:
        "This browser does not support audio recording.",

      recordingError: "Recording error",
      recordingErrorMessage:
        "Unable to continue recording. Please try again.",

      emptyAudio: "No audio captured",
      emptyAudioMessage:
        "The recording contains no audio data. Please try again and speak closer to the microphone.",

      microphoneDenied:
        "Microphone permission denied",

      microphoneDeniedMessage:
        "Please allow the browser to use your microphone.",

      microphoneNotFound:
        "Microphone not found",

      microphoneNotFoundMessage:
        "No microphone was found or the microphone is currently unavailable.",

      microphoneUnavailable:
        "Unable to access microphone",

      microphoneUnavailableMessage:
        "Unable to use the microphone. Please try again.",

      audioReady:
        "The recording is ready to be sent to AI.",

      confirmedMessage:
        "This log has been confirmed. Select Create new log to continue.",
    },

    audioPlayer: {
      title: "Latest recording",
      unsupported:
        "Your browser does not support audio playback.",
    },

    transcript: {
      title: "Transcript",
      aiProcessed: "AI processed",
      confirmed: "Confirmed",

      placeholder:
        "The AI-generated transcript will appear here after processing...",

      ariaLabel:
        "Audio transcript",

      empty:
        "No transcript available.",

      reviewTip:
        "Review the transcript and correct any AI recognition errors before confirming.",

      success:
        "The transcript has been confirmed and is ready to be sent to the system.",
    },

    aiForm: {
      title: "AI extracted data",
      editable: "Editable",
      confirmed: "Confirmed",

      lot: "Farm plot",
      lotPlaceholder: "Example: A01",

      work: "Task",
      workPlaceholder: "Example: Fertilizing",

      material: "Material",
      materialPlaceholder: "Example: NPK fertilizer",

      quantity: "Quantity",
      quantityPlaceholder: "Example: 20",

      unit: "Unit",
      unitPlaceholder: "Example: kg",

      time: "Time",

      empty:
        "No AI extracted data available.",

      editHint:
        "Correct any AI extraction errors before confirming.",
    },

    actions: {
      delete: "Delete recording",
      recordAgain: "Record again",
      sendAI: "Send to AI",
      processing: "AI is processing...",
      confirmLog: "Confirm log",
      confirmed: "Confirmed",
      createNew: "Create new log",
    },

    messages: {
      sending:
        "Sending the recording to the AI Service...",

      processed:
        "Recording processed successfully.",

      backendError:
        "Unable to connect to the AI Service. Please check the backend on port 8000.",

      reviewBeforeConfirm:
        "Please review the transcript before confirming.",

      confirmed:
        "The log has been confirmed.",
    },
  },
};