const attendanceState = {
  apiClockIn: null,
  apiClockOut: null,
  apiSync: null,
  enableGps: false,
  enableOfflineSync: false,
  enableClockOut: true,
  allowedRadius: 0,
  schoolLatitude: null,
  schoolLongitude: null,
};

const dbName = 'StaffAttendanceDB';
const storeName = 'attendance_records';
const settingsCacheKey = 'staffAttendanceSettingsCache';

function initializeAttendancePage() {
  const config = document.getElementById('staffAttendanceConfig');
  if (!config) {
    return;
  }

  attendanceState.apiClockIn = config.dataset.clockInUrl;
  attendanceState.apiClockOut = config.dataset.clockOutUrl;
  attendanceState.apiSync = config.dataset.syncUrl;
  attendanceState.enableGps = config.dataset.enableGps === 'true';
  attendanceState.enableOfflineSync = config.dataset.enableOfflineSync === 'true';
  attendanceState.enableClockOut = config.dataset.enableClockOut === 'true';
  attendanceState.allowedRadius = Number(config.dataset.allowedRadius) || 0;
  attendanceState.schoolLatitude = parseFloat(config.dataset.schoolLatitude) || null;
  attendanceState.schoolLongitude = parseFloat(config.dataset.schoolLongitude) || null;

  cacheAttendanceSettings();
  updateConnectionStatus();
  updatePendingCount();
  updateLocationStatus();
  syncAttendance();
  registerServiceWorker();

  document.getElementById('clockInBtn').addEventListener('click', handleClockIn);
  document.getElementById('clockOutBtn').addEventListener('click', handleClockOut);

  window.addEventListener('online', () => {
    updateConnectionStatus();
    syncAttendance();
  });

  window.addEventListener('offline', updateConnectionStatus);
}

function updateConnectionStatus() {
  const indicator = document.getElementById('onlineIndicator');
  const offlineBadge = document.getElementById('offlineBadge');
  if (!indicator) return;
  if (navigator.onLine) {
    indicator.textContent = 'Online';
    indicator.classList.remove('bg-danger');
    indicator.classList.add('bg-success');
    if (offlineBadge) {
      offlineBadge.classList.add('d-none');
    }
  } else {
    indicator.textContent = 'Offline';
    indicator.classList.remove('bg-success');
    indicator.classList.add('bg-danger');
    if (offlineBadge) {
      offlineBadge.classList.remove('d-none');
    }
  }
}

function showMessage(message, type = 'info') {
  const alertBox = document.getElementById('attendanceMessage');
  if (!alertBox) return;
  alertBox.className = 'alert';
  alertBox.classList.add(
    type === 'error' ? 'alert-danger' :
    type === 'success' ? 'alert-success' :
    'alert-info'
  );
  alertBox.textContent = message;
  alertBox.classList.remove('d-none');
}

function getCurrentPositionAsync() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not available.'));
      return;
    }
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 20000,
      maximumAge: 10000,
    });
  });
}

function computeDistanceMeters(lat1, lon1, lat2, lon2) {
  const toRad = (value) => value * Math.PI / 180;
  const R = 6371000;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function createOfflineSyncId() {
  if (window.crypto && window.crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'offline-' + Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function buildClockPayload(action, coords, syncId) {
  return {
    attendance_type: action,
    latitude: coords.latitude,
    longitude: coords.longitude,
    device_info: navigator.userAgent,
    offline_record: false,
    timestamp: new Date().toISOString(),
    offline_sync_id: syncId,
  };
}

async function handleClockIn() {
  if (!attendanceState.enableGps) {
    showMessage('GPS validation is currently disabled. The app will still attempt to clock you in without location.', 'warning');
  }
  try {
    const position = await getCurrentPositionAsync();
    await sendClockEvent('clock_in', position.coords);
  } catch (error) {
    await handleOfflineFallback('clock_in', error.message);
  }
}

async function handleClockOut() {
  if (!attendanceState.enableClockOut) {
    showMessage('Clock out is disabled by school settings.', 'warning');
    return;
  }
  try {
    const position = await getCurrentPositionAsync();
    await sendClockEvent('clock_out', position.coords);
  } catch (error) {
    await handleOfflineFallback('clock_out', error.message);
  }
}

async function sendClockEvent(action, coords) {
  const offlineSyncId = createOfflineSyncId();
  const payload = buildClockPayload(action, coords, offlineSyncId);

  if (!navigator.onLine) {
    return handleOfflineFallback(action, 'No network available. Storing locally until connection returns.', payload);
  }

  const url = action === 'clock_in' ? attendanceState.apiClockIn : attendanceState.apiClockOut;
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCsrfToken(),
      },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) {
      showMessage(result.detail || 'Unable to save attendance. ' + (result.message || ''), 'error');
      return;
    }
    showMessage(result.message || 'Attendance saved successfully.', 'success');
    document.getElementById('syncStatus').textContent = 'Synced';
    updatePendingCount();
  } catch (error) {
    await handleOfflineFallback(action, error.message, payload);
  }
}

async function handleOfflineFallback(action, errorMessage, payload = null) {
  if (!attendanceState.enableOfflineSync) {
    showMessage('Offline attendance is not enabled. ' + errorMessage, 'error');
    return;
  }
  try {
    let record = payload;
    if (!record) {
      const position = await getCurrentPositionAsync();
      record = {
        attendance_type: action,
        timestamp: new Date().toISOString(),
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        device_info: navigator.userAgent,
        offline_record: true,
        offline_sync_id: createOfflineSyncId(),
      };
    } else {
      record.offline_record = true;
    }
    await saveOfflineRecord(record);
    showMessage('Stored attendance offline. It will sync automatically when you are online.', 'success');
    document.getElementById('syncStatus').textContent = 'Pending sync';
    updatePendingCount();
  } catch (error) {
    showMessage('Unable to save attendance offline: ' + error.message, 'error');
  }
}

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(';').shift();
  }
  return null;
}

function getCsrfToken() {
  return getCookie('csrftoken');
}

function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(dbName, 1);
    request.onupgradeneeded = function(event) {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(storeName)) {
        db.createObjectStore(storeName, { keyPath: 'id', autoIncrement: true });
      }
    };
    request.onsuccess = function(event) {
      resolve(event.target.result);
    };
    request.onerror = function() {
      reject(new Error('Unable to open local attendance database.'));
    };
  });
}

async function saveOfflineRecord(record) {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([storeName], 'readwrite');
    const store = transaction.objectStore(storeName);
    const request = store.add(record);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(new Error('Unable to save the attendance record locally.'));
  });
}

async function getOfflineRecords() {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([storeName], 'readonly');
    const store = transaction.objectStore(storeName);
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result || []);
    request.onerror = () => reject(new Error('Unable to read offline attendance records.'));
  });
}

async function deleteOfflineRecord(id) {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([storeName], 'readwrite');
    const store = transaction.objectStore(storeName);
    const request = store.delete(id);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(new Error('Unable to remove synced record.'));
  });
}

async function syncAttendance() {
  if (!attendanceState.enableOfflineSync || !navigator.onLine) {
    return;
  }
  let records = [];
  try {
    records = await getOfflineRecords();
  } catch (error) {
    console.warn(error);
    return;
  }
  if (!records.length) {
    updatePendingCount(0);
    return;
  }

  try {
    const response = await fetch(attendanceState.apiSync, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCsrfToken(),
      },
      body: JSON.stringify({ records }),
    });
    const result = await response.json();
    if (!response.ok) {
      showMessage(result.detail || 'Offline sync failed.', 'error');
      updatePendingCount(records.length);
      return;
    }
    for (const record of records) {
      await deleteOfflineRecord(record.id);
    }
    showMessage('Offline attendance synced successfully.', 'success');
    document.getElementById('syncStatus').textContent = 'Synced';
    updatePendingCount(0);
  } catch (error) {
    console.warn('Sync failed:', error);
    updatePendingCount(records.length);
  }
}

function updatePendingCount(count = null) {
  const badge = document.getElementById('pendingCountBadge');
  if (!badge) return;
  if (count === null) {
    getOfflineRecords().then((records) => {
      if (!records.length) {
        badge.classList.add('d-none');
      } else {
        badge.textContent = `${records.length} pending sync`;
        badge.classList.remove('d-none');
      }
    }).catch(() => {
      badge.classList.add('d-none');
    });
    return;
  }
  if (count <= 0) {
    badge.classList.add('d-none');
  } else {
    badge.textContent = `${count} pending sync`;
    badge.classList.remove('d-none');
  }
}

function updateLocationStatus() {
  const status = document.getElementById('locationStatus');
  const accuracy = document.getElementById('accuracyInfo');
  const distance = document.getElementById('distanceInfo');
  if (!status || !accuracy || !distance || !attendanceState.enableGps) return;

  getCurrentPositionAsync()
    .then((position) => {
      const coords = position.coords;
      accuracy.textContent = `${coords.accuracy.toFixed(1)} meters`;
      status.textContent = 'Location available';
      if (attendanceState.schoolLatitude && attendanceState.schoolLongitude) {
        const meters = computeDistanceMeters(
          attendanceState.schoolLatitude,
          attendanceState.schoolLongitude,
          coords.latitude,
          coords.longitude,
        );
        distance.textContent = `${meters.toFixed(1)} meters`;
      } else {
        distance.textContent = 'School coordinates unavailable';
      }
    })
    .catch((error) => {
      status.textContent = `Location error: ${error.message}`;
      accuracy.textContent = '--';
      distance.textContent = '--';
    });
}

function cacheAttendanceSettings() {
  const settings = {
    enableGps: attendanceState.enableGps,
    allowedRadius: attendanceState.allowedRadius,
    schoolLatitude: attendanceState.schoolLatitude,
    schoolLongitude: attendanceState.schoolLongitude,
  };
  try {
    localStorage.setItem(settingsCacheKey, JSON.stringify(settings));
  } catch (error) {
    console.warn('Unable to cache attendance settings:', error);
  }
}

function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/staff_attendance/js/attendance-sw.js')
      .then((registration) => {
        console.log('Staff attendance service worker registered:', registration.scope);
      })
      .catch((error) => {
        console.warn('Service worker registration failed:', error);
      });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeAttendancePage);
} else {
  initializeAttendancePage();
}
