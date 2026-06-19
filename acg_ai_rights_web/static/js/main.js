document.addEventListener("change", function (e) {
    if (e.target && e.target.type === "file" && e.target.files.length > 0) {
        const name = e.target.files[0].name;
        e.target.title = name;
    }
});
