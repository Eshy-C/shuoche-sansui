const API_BASE_URL = 'https://shuoche-sansui-api.onrender.com/api';

App({
  globalData: {
    brandName: '说车三岁',
    apiBaseUrl: API_BASE_URL,
  },

  onLaunch() {
    console.log('说车三岁 API 地址：', API_BASE_URL);
  },
});
