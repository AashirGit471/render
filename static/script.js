async function refreshStatus() {
    try {
        const response = await fetch("/status");
        const data = await response.json();
        const status = data.status;
        const badge = document.getElementById("status-badge");
        const startBtn = document.getElementById("start-btn");
        const stopBtn = document.getElementById("stop-btn");
        badge.textContent = status.toUpperCase();
        badge.className = status;

        switch (status) {
            case "stopped":
                startBtn.disabled = false;
                stopBtn.disabled = true;
                break;

            case "running":
                startBtn.disabled = true;
                stopBtn.disabled = false;
                break;

            case "starting":
            case "stopping":
                startBtn.disabled = true;
                stopBtn.disabled = true;
                break;

            default:
                startBtn.disabled = true;
                stopBtn.disabled = true;
        }
    } catch (err) {
        console.error("Status refresh failed:", err);
    }
}

async function startBot() {
    try {
        const response = await fetch("/start", {
            method: "POST",
        });
        if (!response.ok) {
            throw new Error("Failed to start bot");
        }
        await refreshStatus();
    } catch (err) {
        console.error(err);
        alert("Bot start nahi ho saka.");
    }
}

async function stopBot() {
    const confirmed = confirm("Bot ko stop karna hai?");

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch("/stop", {
            method: "POST",
        });

        if (!response.ok) {
            throw new Error("Failed to stop bot");
        }

        await refreshStatus();
    } catch (err) {
        console.error(err);

        alert("Bot stop nahi ho saka.");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    refreshStatus();

    setInterval(refreshStatus, 3000);
});
