const RECORDS_STORAGE_KEY = 'shuoche-sansui-vehicle-records';
const LEGACY_DRAFT_STORAGE_KEY = 'shuoche-sansui-vehicle-draft';
const cloud = require('../../utils/cloud');

function createRecordId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function formatUpdatedAt(timestamp) {
  const date = new Date(timestamp || Date.now());
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${month}月${day}日 ${hours}:${minutes}`;
}

function countUploadedPhotos(vehiclePhotos) {
  return (vehiclePhotos || []).filter((photo) => Boolean(photo.path || photo.fileID)).length;
}

function readRecords() {
  const storedRecords = wx.getStorageSync(RECORDS_STORAGE_KEY);
  if (Array.isArray(storedRecords)) {
    return storedRecords;
  }

  const legacyDraft = wx.getStorageSync(LEGACY_DRAFT_STORAGE_KEY);
  if (!legacyDraft || typeof legacyDraft !== 'object') {
    return [];
  }

  const migratedRecords = [{
    id: createRecordId(),
    name: legacyDraft.recordName || '',
    salesPhoto: legacyDraft.salesPhoto || '',
    vehiclePhotos: legacyDraft.vehiclePhotos || [],
    sellingPoints: legacyDraft.sellingPoints || '',
    updatedAt: legacyDraft.updatedAt || Date.now(),
  }];
  wx.setStorageSync(RECORDS_STORAGE_KEY, migratedRecords);
  return migratedRecords;
}

function getNextStepLabel(record, uploadedVehicleCount) {
  if (!record.salesPhoto && !record.salesPhotoFileID) {
    return '先补充销售形象';
  }
  if (!uploadedVehicleCount) {
    return '先上传车辆照片';
  }
  if (!record.sellingPoints) {
    return '再补充车辆卖点';
  }
  return '素材已保存，可继续完善';
}

function decorateRecords(records) {
  return records.map((record, index) => {
    const uploadedVehicleCount = countUploadedPhotos(record.vehiclePhotos);
    const hasSalesPhoto = Boolean(record.salesPhoto || record.salesPhotoFileID);
    const progressPercent = Math.min(100, Math.round(((uploadedVehicleCount + (hasSalesPhoto ? 1 : 0)) / 10) * 100));
    const progressLabel = progressPercent >= 100 ? '已完成' : `${progressPercent}%`;
    const sellingPointsPreview = String(record.sellingPoints || '').replace(/\s+/g, ' ').trim();

    return {
      ...record,
      displayName: record.name || `未命名车辆 ${records.length - index}`,
      coverPath: record.salesPhoto || ((record.vehiclePhotos || []).find((photo) => photo.path) || {}).path || '',
      uploadedVehicleCount,
      progressPercent,
      progressLabel,
      statusLabel: progressPercent >= 100 ? '已完成' : '草稿',
      updatedAtLabel: formatUpdatedAt(record.updatedAt),
      nextStepLabel: getNextStepLabel(record, uploadedVehicleCount),
      sellingPointsPreview: sellingPointsPreview || '尚未填写卖点文案',
      sellingPointsEmpty: !sellingPointsPreview,
    };
  });
}

Page({
  data: {
    statusBarHeight: 20,
    records: [],
    deletingId: '',
    cloudSyncState: 'loading',
    cloudSyncMessage: '正在查询云端档案…',
  },

  onLoad() {
    const systemInfo = wx.getSystemInfoSync();
    this.setData({ statusBarHeight: systemInfo.statusBarHeight || 20 });
  },

  onShow() {
    this.loadRecords();
  },

  async loadRecords() {
    const localRecords = readRecords();
    let records = localRecords;
    let cloudSyncState = 'unavailable';
    let cloudSyncMessage = '当前仅显示本机草稿';

    if (cloud.isAvailable()) {
      try {
        const cloudRecords = await cloud.listRecords();
        const cloudRecordIDs = new Set(cloudRecords.map((record) => record.id));
        const unsyncedRecords = localRecords.filter((record) => (
          !cloudRecordIDs.has(record.id)
        ));
        records = [
          ...cloudRecords.map((record) => ({ ...record, cloudSynced: true })),
          ...unsyncedRecords.map((record) => ({ ...record, cloudSynced: false })),
        ];
        wx.setStorageSync(RECORDS_STORAGE_KEY, records);
        cloudSyncState = unsyncedRecords.length ? 'pending' : 'success';
        cloudSyncMessage = unsyncedRecords.length
          ? `云端 ${cloudRecords.length} 条，本机有 ${unsyncedRecords.length} 条待同步`
          : `云端已同步 ${cloudRecords.length} 条`;
      } catch (error) {
        console.warn('云端车辆档案读取失败', error);
        cloudSyncState = 'error';
        cloudSyncMessage = `云端查询失败：${cloud.getErrorMessage(error)}`;
      }
    }

    records.sort((left, right) => (right.updatedAt || 0) - (left.updatedAt || 0));
    this.setData({
      records: decorateRecords(records),
      cloudSyncState,
      cloudSyncMessage,
    });
  },

  createRecord() {
    wx.navigateTo({ url: `/pages/index/index?new=1&id=${createRecordId()}` });
  },

  continueRecord(event) {
    const { id } = event.currentTarget.dataset;
    wx.navigateTo({ url: `/pages/index/index?id=${id}` });
  },

  async deleteRecord(event) {
    if (this.data.deletingId) {
      return;
    }

    const { id } = event.currentTarget.dataset;
    const record = this.data.records.find((item) => item.id === id);
    if (!record) {
      return;
    }

    wx.showModal({
      title: '删除车辆档案？',
      content: `「${record.displayName}」删除后将无法在列表中继续录入。`,
      confirmText: '删除',
      confirmColor: '#e45868',
      success: async ({ confirm }) => {
        if (!confirm) {
          return;
        }

        this.setData({ deletingId: id });
        wx.showLoading({ title: '正在删除' });
        try {
          const hasCloudData = record.cloudId || cloud.collectFileIDs(record).length;
          let fileDeleteError = null;
          if (cloud.isAvailable() && hasCloudData) {
            const result = await cloud.deleteRecord(record);
            fileDeleteError = result.fileDeleteError;
          }

          const records = readRecords().filter((item) => item.id !== id);
          wx.setStorageSync(RECORDS_STORAGE_KEY, records);
          if (fileDeleteError) {
            wx.showToast({ title: '档案已删，图片清理失败', icon: 'none' });
          } else {
            wx.showToast({ title: '已删除', icon: 'success' });
          }
          await this.loadRecords();
        } catch (error) {
          wx.showModal({
            title: '云端删除失败',
            content: cloud.getErrorMessage(error),
            showCancel: false,
          });
        } finally {
          this.setData({ deletingId: '' });
          wx.hideLoading();
        }
      },
    });
  },
});
