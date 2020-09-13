/* Project specific Javascript goes here. */
(function () {

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
                fetch(`/find/search?q=${userInput}`)
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

})();
