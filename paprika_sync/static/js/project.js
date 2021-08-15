/* Project specific Javascript goes here. */
(function () {

// New search page functionality (Aug 2021)
if (window.location.pathname === '/find') {
    const form = document.querySelector('form#search');
    const loadingSpinner = document.querySelector('.search-results .loading-spinner');
    const searchResults = document.querySelector('.search-results .results');
    let lastInputTime = Date.now();
    const waitAfterStopTypingToFetch = 500;  // milliseconds

    const allSearches = document.querySelectorAll('.recipe-search');
    const clearSearchIcons = document.querySelectorAll('.oi-x');
    const sourcesList = JSON.parse(document.getElementById('sources-list').textContent);
    const accountsList = JSON.parse(document.getElementById('accounts-list').textContent);
    const tagifyMap = {"source": new Tagify(document.querySelector('input[name=source]'),
        {
            whitelist: sourcesList,
            editTags: false,
            dropdown: {
                enabled: 0
            }
        }),
        "account": new Tagify(document.querySelector('input[name=account]'),
        {
            whitelist: accountsList,
            editTags: false,
            dropdown: {
                enabled: 0
            }
        })
    };
    let controller = new AbortController(); // for aborting the call if user is still typing

    function anySearchBoxHasInput() {
        return Array.from(allSearches).some(el => el.value.length >= 3);
    }

    // Attach change listeners to tagify inputs
    Array.from(allSearches).filter(el => el.classList.contains('tagify')).forEach(searchBox => searchBox.addEventListener('change', inputListener));
    // Attach input listeners to non-tagify inputs
    Array.from(allSearches).filter(el => !el.classList.contains('tagify')).forEach(searchBox => searchBox.addEventListener('input', inputListener));

    function inputListener() {
        const userInput = this.value;
        lastInputTime = Date.now()
        if (userInput.length > 0) {
            this.parentNode.querySelector('.oi-x').removeAttribute('hidden');
            this.parentNode.querySelector('.oi-magnifying-glass').setAttribute('hidden', '');
        }
        if (userInput.length === 0) {
            this.parentNode.querySelector('.oi-x').setAttribute('hidden', '');
            this.parentNode.querySelector('.oi-magnifying-glass').removeAttribute('hidden');
        }
        controller.abort();

        // Only query backend if user has typed at least 3 letters (shortest recipe name in db currently is 4 letters)
        if (anySearchBoxHasInput()) {
            searchResults.removeAttribute('hidden');
            loadingSpinner.removeAttribute('hidden');
            // Timer prevents querying unless user has stopped typing for 500ms
            setTimeout(function() {
                if (Date.now() - lastInputTime >= waitAfterStopTypingToFetch) {
                    const formData = new FormData(form);
                    const params = new URLSearchParams(formData);
                    let controller = new AbortController();
                    fetch(`/find/search?${params}`, {signal: controller.signal})
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.text()
                    })
                    .then(text => {
                        loadingSpinner.setAttribute('hidden', '');
                        searchResults.innerHTML = text;
                    })
                    .catch(error => {
                        if (error.name === 'AbortError') {
                            console.log('Fetch aborted:', error);
                        }
                        else {
                            console.error('Error fetching recipe search results:', error);
                        }
                    });
                }
            }, waitAfterStopTypingToFetch);
        }
        else {
            searchResults.setAttribute('hidden', '');
        }
        lastSearchInput = userInput;
    }

    clearSearchIcons.forEach(searchIcon => searchIcon.addEventListener('click', function() {
        const localSearchBox = this.parentNode.parentNode.querySelector('input.recipe-search');
        if (localSearchBox.classList.contains('tagify')) {
            tagifyMap[localSearchBox.getAttribute('name')].removeAllTags();
        }
        else {
            localSearchBox.value = '';
            const event = document.createEvent('HTMLEvents');
            event.initEvent('input', true, false);
            localSearchBox.dispatchEvent(event);
            localSearchBox.focus();
        }
    }));
}

// Old search page functionality
else if (window.location.pathname === '/find_old') {
    const searchBox = document.querySelector('.recipe-search');
    const searchResults = document.querySelector('.search-results .results');
    const loadingSpinner = document.querySelector('.search-results .loading-spinner');
    const browseAccounts = document.querySelector('.account-list');
    const searchIcon = document.querySelector('.oi-magnifying-glass');
    const clearSearchIcon = document.querySelector('.oi-x');
    let lastSearchInput = searchBox.value;
    let lastInputTime = Date.now();
    const waitAfterStopTypingToFetch = 500;  // milliseconds

    searchBox.addEventListener('input', function() {
        const userInput = this.value;
        lastInputTime = Date.now()
        if (userInput.length > 0) {
            clearSearchIcon.removeAttribute('hidden');
            searchIcon.setAttribute('hidden', '');
        }
        if (userInput.length === 0) {
            clearSearchIcon.setAttribute('hidden', '');
            searchIcon.removeAttribute('hidden');
        }
        if (userInput.length < 3) {
            searchResults.setAttribute('hidden', '');
        }

        // Only query backend if user has typed at least 3 letters (shortest recipe name in db currently is 4 letters)
        if (userInput.length >= 3) {
            searchResults.removeAttribute('hidden');
            loadingSpinner.removeAttribute('hidden');
            // Timer prevents querying unless user has stopped typing for 500ms
            setTimeout(function() {
                if (Date.now() - lastInputTime >= waitAfterStopTypingToFetch) {
                    fetch(`/find_old/search?q=${userInput}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.text()
                    })
                    .then(text => {
                        loadingSpinner.setAttribute('hidden', '');
                        searchResults.innerHTML = text;
                    })
                    .catch(error => {
                        console.error('Error fetching recipe search results:', error);
                    });
                }
            }, waitAfterStopTypingToFetch);
        }
        lastSearchInput = userInput;
    });

    clearSearchIcon.addEventListener('click', function() {
        searchBox.value = '';
        const event = document.createEvent('HTMLEvents');
        event.initEvent('input', true, false);
        searchBox.dispatchEvent(event);
        searchBox.focus();
    });
}

})();
