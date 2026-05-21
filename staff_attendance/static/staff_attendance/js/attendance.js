const attendanceState = {
  apiClockIn: null,
  apiClockOut: null,
  apiSync: null,
  enableGps: false,
  enableOfflineSync: false,
  enableClockOut: true,
  allowedRadius: 0,
};

const dbName = 'StaffAttendanceDB';
const storeName = 'attendance_records';

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

  document.getElementById('clockInBtn').addEventListener('click', handleClockIn);
  document.getElementById('clockOutBtn').addEventListener('click', handleClockOut);
  updateConnectionStatus();
  syncAttendance();
  registerServiceWorker();

  window.addEventListener('online', () => {
    updateConnectionStatus();
    syncAttendance();
  });

  window.addEventListener('offline', updateConnectionStatus);
}

function updateConnectionStatus() {
  const indicator = document.getElementById('onlineIndicator');
  if (!indicator) return;
  if (navigator.onLine) {
    indicator.textContent = 'Online';
    indicator.classList.remove('bg-danger');
    indicator.classList.add('bg-success');
  } else {
    indicator.textContent = 'Offline';
    indicator.classList.remove('bg-success');
    indicator.classList.add('bg-danger');
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
  const payload = {
    latitude: coords.latitude,
    longitude: coords.longitude,
    device_info: navigator.userAgent,
    offline_record: false,
  };

  if (!navigator.onLine) {
    return handleOfflineFallback(action, 'No network available. Storing locally until connection returns.');
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
  } catch (error) {
    await handleOfflineFallback(action, error.message);
  }
}

async function handleOfflineFallback(action, errorMessage) {
  if (!attendanceState.enableOfflineSync) {
    showMessage('Offline attendance is not enabled. ' + errorMessage, 'error');
    return;
  }
  try {
    const timestamp = new Date().toISOString();
    const position = await getCurrentPositionAsync();
    const record = {
      attendance_type: action,
      timestamp,
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      device_info: navigator.userAgent,
    };
    await saveOfflineRecord(record);
    showMessage('Stored attendance offline. It will sync automatically when you are online.', 'success');
    document.getElementById('syncStatus').textContent = 'Pending sync';
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
      return;
    }
    for (const record of records) {
      await deleteOfflineRecord(record.id);
    }
    showMessage('Offline attendance synced successfully.', 'success');
    document.getElementById('syncStatus').textContent = 'Synced';
  } catch (error) {
    console.warn('Sync failed:', error);
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
