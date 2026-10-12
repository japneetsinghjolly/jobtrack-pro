document.addEventListener("DOMContentLoaded", function () {
    // Mobile navigation
    const menuToggle = document.querySelector(".menu-toggle");
    const navLinks = document.querySelector(".nav-links");

    if (menuToggle && navLinks) {
        menuToggle.addEventListener("click", function () {
            const isOpen = navLinks.classList.toggle("is-open");
            menuToggle.setAttribute("aria-expanded", String(isOpen));
        });

        navLinks.querySelectorAll("a").forEach(function (link) {
            link.addEventListener("click", function () {
                navLinks.classList.remove("is-open");
                menuToggle.setAttribute("aria-expanded", "false");
            });
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                navLinks.classList.remove("is-open");
                menuToggle.setAttribute("aria-expanded", "false");
            }
        });
    }

    // Dismiss flash notifications
    document.querySelectorAll(".flash-message").forEach(function (message) {
        const closeButton = message.querySelector(".flash-close");

        if (closeButton) {
            closeButton.addEventListener("click", function () {
                message.remove();
            });
        }
    });

    // Small interaction for feature cards
    document.querySelectorAll(".feature-card").forEach(function (card) {
        card.addEventListener("pointerdown", function () {
            card.classList.add("is-pressed");
        });

        ["pointerup", "pointerleave", "pointercancel"].forEach(function (eventName) {
            card.addEventListener(eventName, function () {
                card.classList.remove("is-pressed");
            });
        });
    });
});
