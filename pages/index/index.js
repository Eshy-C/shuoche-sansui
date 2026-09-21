const RECORDS_STORAGE_KEY = 'shuoche-sansui-vehicle-records';
const LEGACY_DRAFT_STORAGE_KEY = 'shuoche-sansui-vehicle-draft';
const cloud = require('../../utils/cloud');

const PHOTO_SLOTS = [
  { key: 'front45', index: '01', label: '左前 45°', icon: '/assets/icons/front45.png' },
  { key: 'front', index: '02', label: '正前方', icon: '/assets/icons/front.png' },
  { key: 'rear45', index: '03', label: '右后 45°', icon: '/assets/icons/rear45.png' },
  { key: 'leftSide', index: '04', label: '左侧车身', icon: '/assets/icons/left-side.png' },
  { key: 'rightSide', index: '05', label: '右侧车身', icon: '/assets/icons/right-side.png' },
  { key: 'dashboard', index: '06', label: '中控内饰', icon: '/assets/icons/dashboard.png' },
  { key: 'frontSeats', index: '07', label: '前排座椅', icon: '/assets/icons/front-seats.png' },
  { key: 'rearSeats', index: '08', label: '后排空间', icon: '/assets/icons/rear-seats.png' },
  { key: 'details', index: '09', label: '亮点细节', icon: '/assets/icons/details.png' },
];

function createEmptyPhotoSlots() {
  return PHOTO_SLOTS.map((slot) => ({ ...slot, path: '', fileID: '' }));
}

function countUploadedPhotos(photos) {
  return photos.filter((photo) => Boolean(photo.path || photo.fileID)).length;
}

function createRecordId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function getFileExtension(filePath) {
  if (typeof filePath !== 'string') {
    return '.jpg';
  }
  const match = filePath.match(/\.(jpg|jpeg|png|webp|gif)(?:\?|$)/i);
  return match ? `.${match[1].toLowerCase()}` : '.jpg';
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
    vehiclePhotos: legacyDraft.vehiclePhotos || createEmptyPhotoSlots(),
    sellingPoints: legacyDraft.sellingPoints || '',
    updatedAt: legacyDraft.updatedAt || Date.now(),
  }];
  wx.setStorageSync(RECORDS_STORAGE_KEY, migratedRecords);
  return migratedRecords;
}

Page({
  data: {
    statusBarHeight: 20,
    pageTitle: '新建车辆档案',
    recordId: '',
    recordName: '',
    recordCount: 0,
    createdAt: 0,
    salesPhoto: '',
    salesPhotoFileID: '',
    vehiclePhotos: createEmptyPhotoSlots(),
    uploadedVehicleCount: 0,
    sellingPoints: '',
    dragIndex: -1,
    dragOverIndex: -1,
    saving: false,
  },

  photoRects: [],
  ignorePhotoTap: false,
  pendingDeleteFileIDs: [],

  onLoad(options = {}) {
    const systemInfo = wx.getSystemInfoSync();
    const records = readRecords();
    const record = options.id ? records.find((item) => item.id === options.id) : null;
    this.setData({ statusBarHeight: systemInfo.statusBarHeight || 20 });
    this.applyRecord(record || {}, record ? record.id : (options.id || createRecordId()), records.length);

    if (options.id && cloud.isAvailable()) {
      this.loadCloudRecord(options.id);
    }
  },

  onShow() {
    this.setData({ recordCount: readRecords().length });
  },

  applyRecord(source = {}, fallbackId, recordCount) {
    const storedPhotos = Array.isArray(source.vehiclePhotos) ? source.vehiclePhotos : [];
    const vehiclePhotos = createEmptyPhotoSlots().map((slot, index) => {
      const storedPhoto = storedPhotos.find((photo) => photo.key === slot.key) || storedPhotos[index] || {};
      return {
        ...slot,
        path: storedPhoto.path || '',
        fileID: storedPhoto.fileID || '',
      };
    });

    this.setData({
      pageTitle: source.id ? '继续录入车辆' : '新建车辆档案',
      recordId: source.id || fallbackId,
      recordName: source.name || '',
      recordCount: typeof recordCount === 'number' ? recordCount : this.data.recordCount,
      createdAt: source.createdAt || this.data.createdAt || Date.now(),
      salesPhoto: source.salesPhoto || '',
      salesPhotoFileID: source.salesPhotoFileID || '',
      vehiclePhotos,
      uploadedVehicleCount: countUploadedPhotos(vehiclePhotos),
      sellingPoints: source.sellingPoints || '',
    });
  },

  async loadCloudRecord(recordId) {
    try {
      const record = await cloud.getRecord(recordId);
      if (!record) {
        return;
      }

      this.applyRecord(record, record.id, Math.max(this.data.recordCount, readRecords().length));
      const records = readRecords().filter((item) => item.id !== record.id);
      records.unshift(record);
      wx.setStorageSync(RECORDS_STORAGE_KEY, records);
    } catch (error) {
      console.warn('云端车辆档案读取失败', error);
    }
  },

  goToRecords() {
    wx.navigateTo({ url: '/pages/records/index' });
  },

  chooseSalesPhoto() {
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: ({ tempFilePaths }) => {
        if (this.data.salesPhotoFileID) {
          this.rememberDeletedFileID(this.data.salesPhotoFileID);
        }
        this.setData({
          salesPhoto: tempFilePaths[0] || '',
          salesPhotoFileID: '',
        });
      },
    });
  },

  chooseVehiclePhoto(event) {
    if (this.ignorePhotoTap || this.data.dragIndex !== -1) {
      this.ignorePhotoTap = false;
      return;
    }

    const index = Number(event.currentTarget.dataset.index);
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: ({ tempFilePaths }) => {
        if (!tempFilePaths[0]) {
          return;
        }

        const vehiclePhotos = this.data.vehiclePhotos.map((photo, photoIndex) => (
          photoIndex === index ? { ...photo, path: tempFilePaths[0], fileID: '' } : photo
        ));

        if (this.data.vehiclePhotos[index].fileID) {
          this.rememberDeletedFileID(this.data.vehiclePhotos[index].fileID);
        }

        this.setData({
          vehiclePhotos,
          uploadedVehicleCount: countUploadedPhotos(vehiclePhotos),
        });
      },
    });
  },

  startPhotoDrag(event) {
    const index = Number(event.currentTarget.dataset.index);
    const photo = this.data.vehiclePhotos[index];
    if (!photo || !photo.path) {
      return;
    }

    this.ignorePhotoTap = true;
    this.setData({ dragIndex: index, dragOverIndex: index });
    wx.createSelectorQuery()
      .selectAll('.photo-slot')
      .boundingClientRect((rects) => {
        this.photoRects = rects || [];
      })
      .exec();
    wx.vibrateShort({ type: 'light' });
  },

  findPhotoIndexAt(clientX, clientY) {
    if (!this.photoRects.length) {
      return -1;
    }

    let nearestIndex = -1;
    let nearestDistance = Number.POSITIVE_INFINITY;
    this.photoRects.forEach((rect, index) => {
      const inside = clientX >= rect.left
        && clientX <= rect.right
        && clientY >= rect.top
        && clientY <= rect.bottom;
      if (inside) {
        nearestIndex = index;
        nearestDistance = 0;
        return;
      }

      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      const distance = Math.pow(clientX - centerX, 2) + Math.pow(clientY - centerY, 2);
      if (distance < nearestDistance) {
        nearestDistance = distance;
        nearestIndex = index;
      }
    });

    if (!this.photoRects[nearestIndex]) {
      return -1;
    }

    const nearestRect = this.photoRects[nearestIndex];
    const maxDistance = Math.pow(Math.max(nearestRect.width, nearestRect.height) * 1.25, 2);
    return nearestDistance <= maxDistance ? nearestIndex : -1;
  },

  onPhotoTouchMove(event) {
    if (this.data.dragIndex === -1) {
      return;
    }

    const touch = event.touches && event.touches[0];
    if (!touch) {
      return;
    }

    const dragOverIndex = this.findPhotoIndexAt(touch.clientX, touch.clientY);
    if (dragOverIndex !== -1 && dragOverIndex !== this.data.dragOverIndex) {
      this.setData({ dragOverIndex });
    }
  },

  onPhotoTouchEnd() {
    const { dragIndex, dragOverIndex } = this.data;
    if (dragIndex === -1) {
      return;
    }

    if (dragOverIndex !== -1 && dragIndex !== dragOverIndex) {
      const vehiclePhotos = this.data.vehiclePhotos.map((photo) => ({ ...photo }));
      const sourcePhoto = vehiclePhotos[dragIndex];
      const targetPhoto = vehiclePhotos[dragOverIndex];
      const sourcePath = sourcePhoto.path;
      const sourceFileID = sourcePhoto.fileID;
      sourcePhoto.path = targetPhoto.path;
      sourcePhoto.fileID = targetPhoto.fileID;
      targetPhoto.path = sourcePath;
      targetPhoto.fileID = sourceFileID;
      this.setData({
        vehiclePhotos,
        dragIndex: -1,
        dragOverIndex: -1,
      });
    } else {
      this.setData({ dragIndex: -1, dragOverIndex: -1 });
    }

    setTimeout(() => {
      this.ignorePhotoTap = false;
    }, 300);
  },

  removeVehiclePhoto(event) {
    const index = Number(event.currentTarget.dataset.index);
    const photo = this.data.vehiclePhotos[index];
    if (!photo || !photo.path) {
      return;
    }

    wx.showModal({
      title: '删除这张照片？',
      content: `将删除「${photo.label}」照片，可重新上传。`,
      confirmText: '删除',
      confirmColor: '#e45868',
      success: ({ confirm }) => {
        if (!confirm) {
          return;
        }

        this.rememberDeletedFileID(photo.fileID);
        const vehiclePhotos = this.data.vehiclePhotos.map((item, photoIndex) => (
          photoIndex === index ? { ...item, path: '', fileID: '' } : item
        ));
        this.setData({
          vehiclePhotos,
          uploadedVehicleCount: countUploadedPhotos(vehiclePhotos),
        });
      },
    });
  },

  chooseVehicleBatch() {
    const remaining = 9 - this.data.uploadedVehicleCount;
    if (remaining <= 0) {
      wx.showToast({ title: '9 个照片位已全部上传', icon: 'none' });
      return;
    }

    wx.chooseImage({
      count: remaining,
      sizeType: ['compressed'],
      sourceType: ['album'],
      success: ({ tempFilePaths }) => {
        let nextPathIndex = 0;
        const vehiclePhotos = this.data.vehiclePhotos.map((photo) => {
          if (photo.path || photo.fileID || !tempFilePaths[nextPathIndex]) {
            return photo;
          }

          const updatedPhoto = {
            ...photo,
            path: tempFilePaths[nextPathIndex],
            fileID: '',
          };
          nextPathIndex += 1;
          return updatedPhoto;
        });

        this.setData({
          vehiclePhotos,
          uploadedVehicleCount: countUploadedPhotos(vehiclePhotos),
        });
      },
    });
  },

  onSellingPointsInput(event) {
    this.setData({ sellingPoints: event.detail.value });
  },

  onRecordNameInput(event) {
    this.setData({ recordName: event.detail.value });
  },

  openVehicleDetails() {
    wx.showToast({ title: '详情页确认后接入', icon: 'none' });
  },

  rememberDeletedFileID(fileID) {
    if (!cloud.isFileID(fileID) || this.pendingDeleteFileIDs.indexOf(fileID) !== -1) {
      return;
    }
    this.pendingDeleteFileIDs.push(fileID);
  },

  async saveDraft() {
    const saved = await this.persistDraft();
    if (saved) {
      wx.redirectTo({ url: '/pages/records/index' });
    }
  },

  async saveAndContinue() {
    const saved = await this.persistDraft();
    if (saved) {
      wx.redirectTo({ url: '/pages/records/index' });
    }
  },

  async uploadRecordFiles(record) {
    const uploadStamp = Date.now();
    const salesPhotoFileID = record.salesPhotoFileID || await cloud.uploadImage(
      record.salesPhoto,
      `vehicles/${record.id}/sales-${uploadStamp}${getFileExtension(record.salesPhoto)}`
    );
    const vehiclePhotos = [];

    for (const photo of record.vehiclePhotos) {
      const fileID = photo.fileID || await cloud.uploadImage(
        photo.path,
        `vehicles/${record.id}/${photo.key}-${uploadStamp}${getFileExtension(photo.path)}`
      );
      vehiclePhotos.push({ ...photo, fileID });
    }

    return { ...record, salesPhotoFileID, vehiclePhotos };
  },

  async persistDraft() {
    if (this.data.saving) {
      return false;
    }

    const currentRecord = {
      id: this.data.recordId || createRecordId(),
      name: this.data.recordName.trim(),
      salesPhoto: this.data.salesPhoto,
      salesPhotoFileID: this.data.salesPhotoFileID,
      vehiclePhotos: this.data.vehiclePhotos.map((photo) => ({ ...photo })),
      sellingPoints: this.data.sellingPoints,
      createdAt: this.data.createdAt || Date.now(),
      updatedAt: Date.now(),
    };

    this.setData({ saving: true });
    wx.showLoading({ title: '正在保存' });

    try {
      let savedRecord = currentRecord;
      let cloudPartialSave = false;
      if (cloud.isAvailable()) {
        const metadataCloudRecord = await cloud.upsertRecord(currentRecord);

        try {
          const uploadedRecord = await this.uploadRecordFiles(currentRecord);
          const cloudRecord = await cloud.upsertRecord(uploadedRecord);
          savedRecord = {
            ...uploadedRecord,
            cloudId: cloudRecord.cloudId,
          };

          if (this.pendingDeleteFileIDs.length) {
            try {
              await cloud.deleteFiles(this.pendingDeleteFileIDs);
            } catch (error) {
              console.warn('旧图片清理失败', error);
            }
          }
        } catch (error) {
          savedRecord = {
            ...currentRecord,
            cloudId: metadataCloudRecord.cloudId,
          };
          cloudPartialSave = true;
        }
      } else {
        throw new Error('当前运行包没有启用微信云开发，请检查 app.js 的云环境初始化和开发者工具的云开发设置');
      }

      const records = readRecords().filter((record) => record.id !== savedRecord.id);
      records.unshift(savedRecord);
      wx.setStorageSync(RECORDS_STORAGE_KEY, records);
      this.pendingDeleteFileIDs = cloudPartialSave ? this.pendingDeleteFileIDs : [];
      this.setData({
        recordId: savedRecord.id,
        recordCount: records.length,
        createdAt: savedRecord.createdAt,
        salesPhoto: savedRecord.salesPhoto,
        salesPhotoFileID: savedRecord.salesPhotoFileID,
        vehiclePhotos: savedRecord.vehiclePhotos,
        uploadedVehicleCount: countUploadedPhotos(savedRecord.vehiclePhotos),
        saving: false,
      });

      if (cloudPartialSave) {
        wx.showModal({
          title: '文案已保存',
          content: '车辆名称和卖点已经写入云数据库，但图片还没有全部同步，请重新选择图片后再次保存。',
          showCancel: false,
        });
        return false;
      }

      return true;
    } catch (error) {
      const records = readRecords().filter((record) => record.id !== currentRecord.id);
      records.unshift(currentRecord);
      wx.setStorageSync(RECORDS_STORAGE_KEY, records);
      this.setData({ saving: false });
      wx.showModal({
        title: '云端保存失败',
        content: `${cloud.getErrorMessage(error)}\n\n当前内容已保存在本机，请修复云端设置后再次保存。`,
        showCancel: false,
      });
      return false;
    } finally {
      wx.hideLoading();
    }
  },
});
