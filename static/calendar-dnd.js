(() => {
  const cards = document.querySelectorAll(".garment-card[draggable='true']");
  const days = document.querySelectorAll(".drop-day");

  cards.forEach((card) => {
    card.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", card.dataset.itemId);
      e.dataTransfer.effectAllowed = "copy";
      card.classList.add("dragging");
    });
    card.addEventListener("dragend", () => card.classList.remove("dragging"));
  });

  days.forEach((day) => {
    day.addEventListener("dragover", (e) => {
      e.preventDefault();
      day.classList.add("drag-over");
      e.dataTransfer.dropEffect = "copy";
    });
    day.addEventListener("dragleave", () => day.classList.remove("drag-over"));
    day.addEventListener("drop", async (e) => {
      e.preventDefault();
      day.classList.remove("drag-over");
      const itemId = e.dataTransfer.getData("text/plain");
      const wornOn = day.dataset.date;
      if (!itemId || !wornOn) return;
      try {
        const res = await fetch("/api/log", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ item_id: Number(itemId), worn_on: wornOn }),
        });
        const data = await res.json();
        if (!data.ok && data.reason === "duplicate") {
          day.classList.add("flash-dup");
          setTimeout(() => day.classList.remove("flash-dup"), 600);
          return;
        }
        if (data.ok) {
          window.location.reload();
        }
      } catch (err) {
        console.error(err);
      }
    });
  });
})();
