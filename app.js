const API_BASE_URL = 'http://127.0.0.1:8000/api';

App({
  globalData: {
    brandName: '说车三岁',
    apiBaseUrl: API_BASE_URL,
  },

  onLaunch() {
    console.log('说车三岁 API 地址：', API_BASE_URL);
  },
});
