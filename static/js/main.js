
document.addEventListener("DOMContentLoaded", () => {
    const root = document.documentElement;
    const themeToggle = document.getElementById("themeToggle");
    const menuToggle = document.getElementById("menuToggle");
    const navLinks = document.getElementById("navLinks");

    // Theme selection
    function applyTheme(theme) {
        const dark = theme === "dark";

        if (dark) {
            root.dataset.theme = "dark";
        } else {
            delete root.dataset.theme;
        }

        if (themeToggle) {
            themeToggle.textContent = dark ? "☀ Light mode" : "◐ Dark mode";
            themeToggle.setAttribute("aria-pressed", String(dark));
        }
    }

    let savedTheme = "light";

    try {
        savedTheme = localStorage.getItem("jobtrack-theme") || "light";
    } catch (error) {
        // Default to light mode if storage is unavailable.
    }

    applyTheme(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener("click", () => {
            const nextTheme =
                root.dataset.theme === "dark" ? "light" : "dark";

            applyTheme(nextTheme);

            try {
                localStorage.setItem("jobtrack-theme", nextTheme);
            } catch (error) {
                // Theme still changes for the current page.
            }
        });
    }

    // Mobile navigation
    if (menuToggle && navLinks) {
        menuToggle.addEventListener("click", () => {
            const isOpen = navLinks.classList.toggle("open");

            menuToggle.setAttribute("aria-expanded", String(isOpen));
            menuToggle.textContent = isOpen ? "✕" : "☰";
        });

        navLinks.querySelectorAll("a").forEach((link) => {
            link.addEventListener("click", () => {
                navLinks.classList.remove("open");
                menuToggle.setAttribute("aria-expanded", "false");
                menuToggle.textContent = "☰";
            });
        });
    }

    // Dismissible flash messages
    document.querySelectorAll(".flash").forEach((message) => {
        const closeButton = message.querySelector("button");

        if (closeButton) {
            closeButton.addEventListener("click", () => message.remove());
        }

        window.setTimeout(() => {
            if (message.isConnected) {
                message.classList.add("flash-hiding");

                window.setTimeout(() => {
                    if (message.isConnected) message.remove();
                }, 250);
            }
        }, 6000);
    });
});
