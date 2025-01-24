(function() {
    // max # of article-cards to display intially
    const MAX_VISIBLE = 3; // ex: 2 rows if each row has 3 columns

    const container = document.getElementById("articles-container");
    const allCards = container.querySelectorAll(".article-card");
    const loadMoreBtn = document.getElementById("loadMoreBtn");

    // if we have more than MAX_VISIBLE articles, hide the extras
    if (allCards.length > MAX_VISIBLE) {
        // hide all beyond MAX_VISIBLE
        for (let i = MAX_VISIBLE; i < allCards.length; i++) {
            allCards[i].classList.add("hidden-card");
        }
        // show the load more button
        loadMoreBtn.style.display = "inline-block";

        loadMoreBtn.addEventListener("click", () => {
            // reveal all hidden articles
            for (let i = MAX_VISIBLE; i < allCards.length; i++) {
                allCards[i].classList.remove("hidden-card");
            }
            loadMoreBtn.style.display = "none";
        });
    }
})();