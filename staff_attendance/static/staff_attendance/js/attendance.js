const attendanceState = {
  apiClockIn: null,
  apiClockOut: null,
  apiSync: null,
  enableGps: false,
  enableOfflineSync: false,
  enableClockOut: true,
  allowedRadius: 0,
  maxGpsAccuracy: 100,
  schoolLatitude: null,
  schoolLongitude: null,
  locationConfigured: false,
  currentAttendance: {
    clockIn: null,
    clockOut: null,
    status: null,
    synced: false,
  },
  liveTimerId: null,
};

const dbName = 'StaffAttendanceDB';
const storeName = 'attendance_records';
const settingsCacheKey = 'staffAttendanceSettingsCache';
let messageTimeoutId = null;

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
  attendanceState.maxGpsAccuracy = Number(config.dataset.maxGpsAccuracy) || 100;
  attendanceState.schoolLatitude = Number(config.dataset.schoolLatitude);
  attendanceState.schoolLongitude = Number(config.dataset.schoolLongitude);
  attendanceState.locationConfigured = Number.isFinite(attendanceState.schoolLatitude) && Number.isFinite(attendanceState.schoolLongitude);
  attendanceState.currentAttendance.clockIn = parseIsoDate(config.dataset.todayClockIn);
  attendanceState.currentAttendance.clockOut = parseIsoDate(config.dataset.todayClockOut);
  attendanceState.currentAttendance.status = config.dataset.todayStatus || null;
  attendanceState.currentAttendance.synced = config.dataset.todaySynced === 'true';

  cacheAttendanceSettings();
  updateConnectionStatus();
  setupAttendanceControls();
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

function setupAttendanceControls() {
  const clockInBtn = document.getElementById('clockInBtn');
  const clockOutBtn = document.getElementById('clockOutBtn');
  const completedBadge = document.getElementById('attendanceCompletedBadge');
  const noClockInMessage = document.getElementById('noClockInMessage');
  const liveTimerRow = document.getElementById('liveTimerRow');
  const syncStatus = document.getElementById('syncStatus');

  if (!clockInBtn || !clockOutBtn || !completedBadge) return;

  const hasClockIn = !!attendanceState.currentAttendance.clockIn;
  const hasClockOut = !!attendanceState.currentAttendance.clockOut;
  const completed = hasClockIn && hasClockOut;

  if (!attendanceState.locationConfigured) {
    showMessage('Attendance location not configured. Contact administrator.', 'error');
    clockInBtn.disabled = true;
    clockOutBtn.disabled = true;
    clockInBtn.classList.add('disabled');
    clockOutBtn.classList.add('disabled');
  }

  if (completed) {
    clockInBtn.classList.add('d-none');
    clockOutBtn.classList.add('d-none');
    completedBadge.classList.remove('d-none');
    if (noClockInMessage) noClockInMessage.classList.add('d-none');
    if (liveTimerRow) liveTimerRow.classList.add('d-none');
    updateStatusBadge('completed');
    return;
  }

  completedBadge.classList.add('d-none');
  if (liveTimerRow) liveTimerRow.classList.toggle('d-none', !hasClockIn);

  if (hasClockIn) {
    clockInBtn.classList.add('d-none');
    clockOutBtn.classList.remove('d-none');
    clockOutBtn.disabled = !attendanceState.enableClockOut;
    if (noClockInMessage) noClockInMessage.classList.add('d-none');
    startLiveTimer();
  } else {
    clockInBtn.classList.remove('d-none');
    clockOutBtn.classList.add('d-none');
    if (noClockInMessage) noClockInMessage.classList.remove('d-none');
    stopLiveTimer();
  }

  if (syncStatus) {
    syncStatus.textContent = attendanceState.currentAttendance.synced ? 'Synced' : 'Pending';
    syncStatus.className = `badge ${attendanceState.currentAttendance.synced ? 'bg-info' : 'bg-warning text-dark'}`;
  }
}

function updateStatusBadge(state) {
  const statusBadge = document.getElementById('statusBadge');
  if (!statusBadge) return;
  if (state === 'completed') {
    statusBadge.textContent = 'Completed';
    statusBadge.className = 'badge bg-primary';
    return;
  }
  const status = attendanceState.currentAttendance.status;
  if (status === 'present') {
    statusBadge.textContent = 'Present';
    statusBadge.className = 'badge bg-success';
  } else if (status === 'late') {
    statusBadge.textContent = 'Late';
    statusBadge.className = 'badge bg-warning text-dark';
  } else {
    statusBadge.textContent = 'Absent';
    statusBadge.className = 'badge bg-danger';
  }
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

let messageTimeoutId = null;
function showMessage(message, type = 'info', autoHide = true) {
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
  if (messageTimeoutId) {
    clearTimeout(messageTimeoutId);
  }
  if (autoHide) {
    messageTimeoutId = setTimeout(() => {
      alertBox.classList.add('d-none');
    }, 8000);
  }
}

function parseIsoDate(value) {
  if (!value) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
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

function validateGpsAccuracy(accuracy) {
  if (typeof accuracy !== 'number' || Number.isNaN(accuracy)) {
    return { valid: false, message: 'Unable to verify GPS accuracy.' };
  }
  if (accuracy > attendanceState.maxGpsAccuracy) {
    return {
      valid: false,
      message: 'Location accuracy too weak. Move outdoors or enable GPS.',
    };
  }
  return { valid: true };
}

function formatTimeSpan(totalSeconds) {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = Math.floor(totalSeconds % 60);
  return `${hours.toString().padStart(2, '0')}h ${minutes.toString().padStart(2, '0')}m ${seconds.toString().padStart(2, '0')}s`;
}

function formatWorkDuration(totalSeconds) {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
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
  if (!attendanceState.locationConfigured) {
    showMessage('Attendance location not configured. Contact administrator.', 'error');
    return;
  }
  if (!attendanceState.enableGps) {
    showMessage('GPS validation is currently disabled. The app will still attempt to clock you in without location.', 'warning');
  }
  try {
    setLoading(true, 'Getting location...');
    const position = await getCurrentPositionAsync();
    const accuracyCheck = validateGpsAccuracy(position.coords.accuracy);
    if (!accuracyCheck.valid) {
      showMessage(accuracyCheck.message, 'error');
      setLoading(false);
      return;
    }
    await sendClockEvent('clock_in', position.coords);
  } catch (error) {
    await handleOfflineFallback('clock_in', error.message);
  } finally {
    setLoading(false);
  }
}

async function handleClockOut() {
  if (!attendanceState.locationConfigured) {
    showMessage('Attendance location not configured. Contact administrator.', 'error');
    return;
  }
  if (!attendanceState.enableClockOut) {
    showMessage('Clock out is disabled by school settings.', 'warning');
    return;
  }
  try {
    setLoading(true, 'Getting location...');
    const position = await getCurrentPositionAsync();
    const accuracyCheck = validateGpsAccuracy(position.coords.accuracy);
    if (!accuracyCheck.valid) {
      showMessage(accuracyCheck.message, 'error');
      setLoading(false);
      return;
    }
    await sendClockEvent('clock_out', position.coords);
  } catch (error) {
    await handleOfflineFallback('clock_out', error.message);
  } finally {
    setLoading(false);
  }
}

async function sendClockEvent(action, coords) {
  const offlineSyncId = createOfflineSyncId();
  const payload = buildClockPayload(action, coords, offlineSyncId);
  setLoading(true, action === 'clock_in' ? 'Clocking in...' : 'Clocking out...');

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
    if (action === 'clock_in') {
      attendanceState.currentAttendance.clockIn = new Date();
      attendanceState.currentAttendance.status = result.status || 'present';
      attendanceState.currentAttendance.synced = result.synced;
      updateStatusBadge(attendanceState.currentAttendance.status);
    } else {
      attendanceState.currentAttendance.clockOut = new Date();
      attendanceState.currentAttendance.synced = result.synced;
      stopLiveTimer();
    }
    setupAttendanceControls();
  } catch (error) {
    await handleOfflineFallback(action, error.message, payload);
  } finally {
    setLoading(false);
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

function setLoading(isLoading, message = '') {
  const clockInBtn = document.getElementById('clockInBtn');
  const clockOutBtn = document.getElementById('clockOutBtn');
  if (clockInBtn) {
    clockInBtn.disabled = isLoading;
    clockInBtn.classList.toggle('disabled', isLoading);
  }
  if (clockOutBtn) {
    clockOutBtn.disabled = isLoading;
    clockOutBtn.classList.toggle('disabled', isLoading);
  }
  if (message) {
    showMessage(message, 'info', false);
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
  if (!status || !accuracy || !distance) return;

  if (!attendanceState.locationConfigured) {
    status.textContent = 'Attendance location not configured. Contact administrator.';
    accuracy.textContent = '--';
    distance.textContent = '--';
    return;
  }

  if (!attendanceState.enableGps) {
    status.textContent = 'GPS not required for this school configuration.';
    accuracy.textContent = '--';
    distance.textContent = '--';
    return;
  }

  getCurrentPositionAsync()
    .then((position) => {
      const coords = position.coords;
      const accuracyCheck = validateGpsAccuracy(coords.accuracy);
      if (!accuracyCheck.valid) {
        status.textContent = accuracyCheck.message;
        accuracy.textContent = `>${attendanceState.maxGpsAccuracy} meters`;
        distance.textContent = '--';
        return;
      }

      accuracy.textContent = `${coords.accuracy.toFixed(1)} meters`;
      status.textContent = 'Location available';
      const meters = computeDistanceMeters(
        attendanceState.schoolLatitude,
        attendanceState.schoolLongitude,
        coords.latitude,
        coords.longitude,
      );
      distance.textContent = `${meters.toFixed(1)} meters`;
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

function startLiveTimer() {
  const liveTimer = document.getElementById('liveTimer');
  if (!liveTimer || !attendanceState.currentAttendance.clockIn) return;
  stopLiveTimer();
  function updateTimer() {
    const now = new Date();
    const seconds = Math.max(0, Math.floor((now - attendanceState.currentAttendance.clockIn) / 1000));
    liveTimer.textContent = formatTimeSpan(seconds);
  }
  updateTimer();
  attendanceState.liveTimerId = setInterval(updateTimer, 1000);
}

function stopLiveTimer() {
  if (attendanceState.liveTimerId) {
    clearInterval(attendanceState.liveTimerId);
    attendanceState.liveTimerId = null;
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
