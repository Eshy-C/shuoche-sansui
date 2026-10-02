const DEFAULT_API_BASE_URL = 'https://shuoche-sansui-api.onrender.com/api';
const COLLECTION_NAME = 'vehicle_records';

function authorizationHeader() {
  return {};
}

async function withAuthorization(operation) {
  return operation();
}

function getApiBaseURL() {
  try {
    const app = getApp();
    return (app.globalData && app.globalData.apiBaseUrl) || DEFAULT_API_BASE_URL;
  } catch (error) {
    return DEFAULT_API_BASE_URL;
  }
}

function buildURL(path) {
  return `${getApiBaseURL().replace(/\/$/, '')}/${path.replace(/^\//, '')}`;
}

function isAvailable() {
  return Boolean(
    wx
      && typeof wx.request === 'function'
      && typeof wx.uploadFile === 'function'
  );
}

function isFileID(value) {
  return typeof value === 'string' && value.indexOf('api://') === 0;
}

function uniqueFileIDs(fileIDs) {
  return Array.from(new Set((fileIDs || []).filter((fileID) => isFileID(fileID))));
}

function collectFileIDs(record) {
  const vehicleFileIDs = (record && record.vehiclePhotos || []).map((photo) => photo.fileID);
  return uniqueFileIDs([
    record && record.salesPhotoFileID,
    ...vehicleFileIDs,
  ]);
}

function parseResponseData(data) {
  if (typeof data !== 'string') {
    return data || {};
  }

  try {
    return JSON.parse(data);
  } catch (error) {
    return { detail: data };
  }
}

function createRequestError(response, fallbackMessage) {
  const detail = response && response.detail;
  const error = new Error(detail || response && response.message || fallbackMessage);
  error.statusCode = response && response.statusCode;
  error.detail = detail;
  error.response = response;
  return error;
}

function sendRequestJSON(path, options = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: buildURL(path),
      method: options.method || 'GET',
      data: options.data,
      header: {
        'content-type': 'application/json',
        ...authorizationHeader(),
        ...(options.header || {}),
      },
      timeout: options.timeout || 120000,
      success: (response) => {
        const data = parseResponseData(response.data);
        if (response.statusCode >= 200 && response.statusCode < 300) {
          resolve(data);
          return;
        }
        reject(createRequestError({ ...data, statusCode: response.statusCode }, '接口请求失败'));
      },
      fail: (error) => reject(createRequestError(error, '无法连接后端服务')),
    });
  });
}

function requestJSON(path, options = {}) {
  return withAuthorization(() => sendRequestJSON(path, options));
}

function getTempFileURLMap(fileIDs) {
  const uniqueIDs = uniqueFileIDs(fileIDs);
  if (!uniqueIDs.length) {
    return Promise.resolve({});
  }
  return requestJSON('file-urls', { method: 'POST', data: { file_ids: uniqueIDs } });
}

function parseVehiclePhotos(value) {
  if (Array.isArray(value)) {
    return value;
  }

  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value);
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      console.warn('车辆图片字段解析失败', error);
    }
  }

  return [];
}

function hydrateRecord(record) {
  const fileIDs = (record.vehiclePhotos || []).filter((photo) => !photo.path).map((photo) => photo.fileID);
  if (!record.salesPhoto) {
    fileIDs.push(record.salesPhotoFileID);
  }
  return getTempFileURLMap(fileIDs).then((urlMap) => ({
    ...record,
    salesPhoto: record.salesPhoto || urlMap[record.salesPhotoFileID] || '',
    vehiclePhotos: (record.vehiclePhotos || []).map((photo) => ({
      ...photo,
      path: photo.path || urlMap[photo.fileID] || '',
    })),
  }));
}

function uploadImage(filePath, cloudPath) {
  if (!filePath) {
    return Promise.resolve('');
  }
  if (isFileID(filePath)) {
    return Promise.resolve(filePath);
  }

  const pathParts = String(cloudPath || '').split('/');
  const recordId = pathParts[1];
  if (!recordId) {
    return Promise.reject(new Error('上传图片缺少车辆档案 ID'));
  }

  return withAuthorization(() => new Promise((resolve, reject) => {
    wx.uploadFile({
      url: buildURL(`records/${encodeURIComponent(recordId)}/files`),
      filePath,
      name: 'file',
      formData: { storage_key: cloudPath },
      header: authorizationHeader(),
      timeout: 120000,
      success: (response) => {
        const data = parseResponseData(response.data);
        if (response.statusCode >= 200 && response.statusCode < 300 && data.fileID) {
          resolve(data.fileID);
          return;
        }
        reject(createRequestError({ ...data, statusCode: response.statusCode }, '图片上传失败'));
      },
      fail: (error) => reject(createRequestError(error, '无法连接后端服务')),
    });
  }));
}

function toCloudData(record) {
  return {
    record_id: record.id,
    name: record.name || '',
    sales_photo_file_id: record.salesPhotoFileID || '',
    vehicle_photos: (record.vehiclePhotos || []).map((photo) => ({
      key: photo.key,
      index: photo.index,
      label: photo.label,
      fileID: photo.fileID || '',
    })),
    selling_points: record.sellingPoints || '',
    created_at: record.createdAt || Date.now(),
    updated_at: record.updatedAt || Date.now(),
  };
}

function fromCloudData(document) {
  const vehiclePhotos = parseVehiclePhotos(document.vehiclePhotos || document.vehicle_photos);
  const salesPhotoFileID = document.salesPhotoFileID || document.sales_photo_file_id || '';

  return {
    id: document.id || document.record_id || '',
    cloudId: document.cloudId || document.id || document.record_id || '',
    cloudSynced: document.cloudSynced !== false,
    name: document.name || '',
    salesPhotoFileID,
    salesPhoto: document.salesPhoto || '',
    vehiclePhotos: vehiclePhotos.map((photo) => ({
      ...photo,
      path: photo.path || '',
    })),
    sellingPoints: document.sellingPoints || document.selling_points || '',
    createdAt: Number(document.createdAt || document.created_at) || Date.now(),
    updatedAt: Number(document.updatedAt || document.updated_at) || Date.now(),
  };
}

async function upsertRecord(record) {
  const response = await requestJSON(`records/${encodeURIComponent(record.id)}`, {
    method: 'PUT',
    data: toCloudData(record),
  });
  return hydrateRecord(fromCloudData(response));
}

async function getRecord(recordId) {
  try {
    const response = await requestJSON(`records/${encodeURIComponent(recordId)}`);
    return hydrateRecord(fromCloudData(response));
  } catch (error) {
    if (error.statusCode === 404) {
      return null;
    }
    throw error;
  }
}

async function listRecords() {
  const response = await requestJSON('records');
  const records = Array.isArray(response) ? response : [];
  return Promise.all(records.map((record) => hydrateRecord(fromCloudData(record))));
}

async function deleteFiles(fileIDs) {
  const uniqueIDs = uniqueFileIDs(fileIDs);
  if (!uniqueIDs.length) {
    return;
  }
  return requestJSON('files', {
    method: 'DELETE',
    data: { file_ids: uniqueIDs },
  });
}

async function deleteRecord(record) {
  await requestJSON(`records/${encodeURIComponent(record.id)}`, { method: 'DELETE' });
  return { fileDeleteError: null };
}

function getErrorMessage(error) {
  const message = error && (error.errMsg || error.message || error.detail || error.error);
  if (error && error.statusCode === 401) {
    return '云端接口拒绝访问，请检查后端服务配置';
  }
  if (error && error.statusCode === 404) {
    return '后端接口不存在，请确认 FastAPI 已启动并使用最新代码';
  }
  if (String(message || '').indexOf('无法连接后端服务') !== -1) {
    return '无法连接后端服务，请先启动 FastAPI，或把 app.js 的 API 地址改成已部署的 HTTPS 地址';
  }
  return message || '后端服务暂时不可用';
}

module.exports = {
  COLLECTION_NAME,
  collectFileIDs,
  deleteFiles,
  deleteRecord,
  fromCloudData,
  getErrorMessage,
  getRecord,
  getTempFileURLMap,
  hydrateRecord,
  isAvailable,
  isFileID,
  listRecords,
  toCloudData,
  uploadImage,
  upsertRecord,
};
