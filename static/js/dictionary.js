(() => {
  const toggle = document.getElementById('globalDictionaryToggle');
  const dictionary = document.getElementById('siteDictionary');
  if (!toggle || !dictionary) return;

  const searchInput = document.getElementById('siteDictionarySearch');
  const status = document.getElementById('siteDictionaryStatus');
  const results = document.getElementById('siteDictionaryResults');
  const closeButton = document.getElementById('siteDictionaryClose');
  const databaseName = 'daarulPortalDictionary';
  const databaseVersion = 2;
  const storeName = 'offlineData';
  const maximumResults = 15;
  let entries = null;
  let searchIndex = null;
  let offlineAvailable = false;
  let loadPromise = null;
  let searchTimer = null;

  function openDatabase() {
    return new Promise((resolve, reject) => {
      if (!window.indexedDB) {
        reject(new Error('IndexedDB is unavailable in this browser.'));
        return;
      }

      const request = window.indexedDB.open(databaseName, databaseVersion);
      request.onupgradeneeded = () => {
        if (!request.result.objectStoreNames.contains(storeName)) {
          request.result.createObjectStore(storeName);
        }
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error('Unable to open dictionary storage.'));
      request.onblocked = () => reject(new Error('Dictionary storage is blocked by another tab.'));
    });
  }

  async function readCachedEntries() {
    const database = await openDatabase();
    try {
      return await new Promise((resolve, reject) => {
        const transaction = database.transaction(storeName, 'readonly');
        const request = transaction.objectStore(storeName).get('entries');
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error || new Error('Unable to read the offline dictionary.'));
      });
    } finally {
      database.close();
    }
  }

  async function saveEntries(entriesToSave) {
    const database = await openDatabase();
    try {
      await new Promise((resolve, reject) => {
        const transaction = database.transaction(storeName, 'readwrite');
        transaction.objectStore(storeName).put(entriesToSave, 'entries');
        transaction.oncomplete = resolve;
        transaction.onerror = () => reject(transaction.error || new Error('Unable to save the offline dictionary.'));
        transaction.onabort = () => reject(transaction.error || new Error('Saving the offline dictionary was aborted.'));
      });
    } finally {
      database.close();
    }
  }

  function isValidDictionary(data) {
    return Array.isArray(data) && data.length > 0 && data.every((entry) => (
      Array.isArray(entry) &&
      typeof entry[0] === 'string' &&
      Array.isArray(entry[1]) &&
      entry[1].every((translation) => typeof translation === 'string') &&
      Array.isArray(entry[2]) &&
      entry[2].every((meaning) => (
        Array.isArray(meaning) &&
        typeof meaning[0] === 'string' &&
        typeof meaning[1] === 'string'
      ))
    ));
  }

  async function loadEntries() {
    if (entries) return entries;
    if (loadPromise) return loadPromise;

    loadPromise = (async () => {
      try {
        const cachedEntries = await readCachedEntries();
        if (isValidDictionary(cachedEntries)) {
          entries = cachedEntries;
          offlineAvailable = true;
          return entries;
        }
      } catch (error) {
        console.warn('Unable to read the saved offline dictionary:', error);
      }

      const response = await fetch(dictionary.dataset.dictionaryUrl, { cache: 'force-cache' });
      if (!response.ok) {
        throw new Error(`Dictionary data request failed (${response.status}).`);
      }

      const downloadedEntries = await response.json();
      if (!isValidDictionary(downloadedEntries)) {
        throw new Error('The downloaded dictionary data has an invalid format.');
      }

      entries = downloadedEntries;
      try {
        await saveEntries(entries);
        offlineAvailable = true;
      } catch (error) {
        offlineAvailable = false;
        console.warn('Dictionary loaded but could not be saved for offline use:', error);
      }
      return entries;
    })();

    try {
      return await loadPromise;
    } finally {
      loadPromise = null;
    }
  }

  function normalizeTerm(value, arabic) {
    let normalized = value.normalize('NFKC').trim();
    if (arabic) {
      normalized = normalized
        .replace(/[\u064B-\u065F\u0670\u0640]/g, '')
        .replace(/[أإآٱ]/g, 'ا')
        .replace(/ى/g, 'ي');
    }
    return normalized.toLowerCase();
  }

  function matchRank(value, query) {
    if (value === query.term) return 0;
    if (value.startsWith(query.term)) return 1;
    if (value.includes(query.term)) return 2;
    return 3;
  }

  function prepareSearchIndex() {
    if (searchIndex) return;
    searchIndex = entries.map(([english, translations, meanings]) => ({
      english,
      translations,
      meanings,
      englishTerm: normalizeTerm(english, false),
      arabicTerms: translations.map((translation) => normalizeTerm(translation, true)),
    }));
  }

  function renderResults(queryText) {
    results.replaceChildren();
    const originalQuery = queryText.trim();
    if (!originalQuery) return;
    if (!entries) return;

    if (originalQuery.length < 2) {
      status.textContent = 'Type at least two characters to search.';
      return;
    }

    const arabic = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]/.test(originalQuery);
    const query = {
      arabic,
      term: normalizeTerm(originalQuery, arabic),
    };
    const matches = [[], [], []];

    for (const entry of searchIndex) {
      let rank = arabic ? 3 : matchRank(entry.englishTerm, query);
      if (arabic) {
        for (const translation of entry.arabicTerms) {
          rank = Math.min(rank, matchRank(translation, query));
          if (rank === 0) break;
        }
      }
      if (rank < matches.length && matches[rank].length < maximumResults) {
        matches[rank].push(entry);
      }
    }

    const found = matches.flat().slice(0, maximumResults);
    if (!found.length) {
      status.textContent = 'No matching entries found.';
      return;
    }

    status.textContent = `${found.length} ${found.length === 1 ? 'result' : 'results'} shown.`;
    for (const { english, translations, meanings } of found) {
      const result = document.createElement('div');
      result.className = 'site-dictionary-result';

      const englishText = document.createElement('span');
      englishText.className = 'site-dictionary-english';
      englishText.textContent = english;

      const meaningLabel = document.createElement('span');
      meaningLabel.className = 'site-dictionary-meaning-label';
      meaningLabel.textContent = 'Meaning';

      let meaningContent;
      if (meanings.length) {
        meaningContent = document.createElement('ul');
        meaningContent.className = 'site-dictionary-meanings';
        for (const [partOfSpeech, definition] of meanings) {
          const item = document.createElement('li');
          const partLabel = document.createElement('strong');
          partLabel.textContent = `${partOfSpeech}: `;
          item.append(partLabel, document.createTextNode(definition));
          meaningContent.append(item);
        }
      } else {
        meaningContent = document.createElement('span');
        meaningContent.className = 'site-dictionary-meaning-missing';
        meaningContent.textContent = 'No definition is available for this entry.';
      }

      const translationLabel = document.createElement('span');
      translationLabel.className = 'site-dictionary-translation-label';
      translationLabel.textContent = 'Arabic translation';

      const arabicText = document.createElement('span');
      arabicText.className = 'site-dictionary-arabic';
      arabicText.dir = 'rtl';
      arabicText.lang = 'ar';
      arabicText.textContent = translations.join('، ');

      result.append(englishText, meaningLabel, meaningContent, translationLabel, arabicText);
      results.append(result);
    }
  }

  async function setOpen(isOpen, restoreFocus = false) {
    dictionary.hidden = !isOpen;
    toggle.setAttribute('aria-expanded', String(isOpen));
    toggle.setAttribute('aria-label', isOpen ? 'Close dictionary' : 'Open dictionary');
    if (!isOpen) {
      if (restoreFocus) toggle.focus();
      return;
    }

    searchInput.disabled = true;
    status.textContent = 'Loading dictionary data...';
    searchInput.focus();
    try {
      await loadEntries();
      prepareSearchIndex();
      searchInput.disabled = false;
      if (dictionary.hidden) return;
      const definedEntryCount = entries.filter((entry) => entry[2].length > 0).length;
      status.textContent = offlineAvailable
        ? `Ready offline with ${entries.length.toLocaleString()} entries and ${definedEntryCount.toLocaleString()} meanings.`
        : `Loaded ${entries.length.toLocaleString()} entries, but offline storage is unavailable.`;
      renderResults(searchInput.value);
      searchInput.focus();
    } catch (error) {
      console.error('Unable to load the offline dictionary:', error);
      searchInput.disabled = true;
      status.textContent = navigator.onLine === false
        ? 'This device has not saved the dictionary yet. Open it while online once to enable offline lookup.'
        : 'The dictionary could not be loaded. Close and reopen it to try again.';
    }
  }

  toggle.addEventListener('click', () => setOpen(dictionary.hidden));
  closeButton.addEventListener('click', () => setOpen(false, true));
  searchInput.addEventListener('input', () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => renderResults(searchInput.value), 100);
  });

  dictionary.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      setOpen(false, true);
    }
  });

  document.addEventListener('click', (event) => {
    if (!dictionary.hidden && !dictionary.contains(event.target) && !toggle.contains(event.target)) {
      setOpen(false);
    }
  });
})();
